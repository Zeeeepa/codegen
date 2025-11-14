#!/usr/bin/env node
/**
 * NPM Registry Indexer - Production Version
 * 
 * A production-grade npm registry indexer with:
 * - JSONL file-based storage for efficient streaming
 * - Incremental sync with CNPM mirror
 * - Parallel metadata enrichment
 * - CSV export with filtering
 * - Comprehensive error handling and retry logic
 * 
 * Usage:
 *   node indexer.js --index    # Sync from registry
 *   node indexer.js --enrich   # Enrich metadata
 *   node indexer.js --export   # Export to CSV
 *   node indexer.js --status   # Show status
 */

import fs from 'fs/promises';
import { createReadStream, createWriteStream, existsSync } from 'fs';
import path from 'path';
import readline from 'readline';
import log from 'npmlog';
import PQueue from 'p-queue';
import got from 'got';
import registryFetch from 'npm-registry-fetch';
import { Command } from 'commander';
import fastcsv from 'fast-csv';
import { pipeline } from 'stream/promises';
import { Transform, Readable } from 'stream';

const { format: csvFormat } = fastcsv;

// ============================================================================
// CONFIGURATION
// ============================================================================

const CONFIG = {
  REGISTRY_URL: process.env.NPM_REGISTRY_URL || 'https://registry.npmmirror.com',
  REGISTRY_CHANGES_URL: process.env.NPM_CHANGES_URL || 'https://r.cnpmjs.org',
  DATA_DIR: process.env.DATA_DIR || './data',
  BATCH_SIZE: parseInt(process.env.BATCH_SIZE || '1000', 10),
  ENRICH_CONCURRENCY: parseInt(process.env.ENRICH_CONCURRENCY || '20', 10),
  REQUEST_TIMEOUT: parseInt(process.env.REQUEST_TIMEOUT || '30000', 10),
  MAX_RETRIES: parseInt(process.env.MAX_RETRIES || '3', 10),
  CHECKPOINT_INTERVAL: 100 // Save checkpoint every N batches
};

const CHECKPOINT_FILE = path.join(CONFIG.DATA_DIR, 'checkpoint.json');
const PACKAGES_JSONL = path.join(CONFIG.DATA_DIR, 'packages.jsonl');
const CSV_FILE = path.join(CONFIG.DATA_DIR, 'packages.csv');

log.heading = 'NPMIndexer';
log.level = process.env.LOG_LEVEL || 'info';

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

async function ensureDataDir() {
  await fs.mkdir(CONFIG.DATA_DIR, { recursive: true });
}

async function atomicWrite(filepath, data) {
  const tempPath = `${filepath}.tmp`;
  try {
    await fs.writeFile(tempPath, data);
    await fs.rename(tempPath, filepath);
  } catch (error) {
    if (existsSync(tempPath)) await fs.unlink(tempPath);
    throw error;
  }
}

function formatNumber(num) {
  return num.toLocaleString();
}

function formatDuration(ms) {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}

// ============================================================================
// FILE STORAGE CLASS
// ============================================================================

class FileStorage {
  constructor() {
    this.checkpointPath = CHECKPOINT_FILE;
    this.packagesPath = PACKAGES_JSONL;
    this.csvPath = CSV_FILE;
  }

  async getCheckpoint() {
    try {
      const data = await fs.readFile(this.checkpointPath, 'utf8');
      return JSON.parse(data);
    } catch (error) {
      return {
        last_sequence: 0,
        total_packages: 0,
        enriched_count: 0,
        last_updated: null,
        version: '2.0.0'
      };
    }
  }

  async saveCheckpoint(checkpoint) {
    await ensureDataDir();
    const data = JSON.stringify({
      ...checkpoint,
      updated_at: new Date().toISOString()
    }, null, 2);
    await atomicWrite(this.checkpointPath, data);
  }

  async appendPackages(packages) {
    await ensureDataDir();
    const data = packages.map(pkg => JSON.stringify(pkg)).join('\n') + '\n';
    await fs.appendFile(this.packagesPath, data);
  }

  async *streamPackages() {
    if (!existsSync(this.packagesPath)) return;

    const fileStream = createReadStream(this.packagesPath, { 
      encoding: 'utf8',
      highWaterMark: 64 * 1024 
    });
    
    const rl = readline.createInterface({
      input: fileStream,
      crlfDelay: Infinity
    });

    for await (const line of rl) {
      if (!line.trim()) continue;
      try {
        yield JSON.parse(line);
      } catch (error) {
        log.warn('Storage', 'Invalid JSON line, skipping');
      }
    }
  }

  async getPackagesByState(state, limit = CONFIG.BATCH_SIZE) {
    const packages = [];
    for await (const pkg of this.streamPackages()) {
      if (pkg.state === state) {
        packages.push(pkg);
        if (packages.length >= limit) break;
      }
    }
    return packages;
  }

  async countByState(state) {
    let count = 0;
    for await (const pkg of this.streamPackages()) {
      if (pkg.state === state) count++;
    }
    return count;
  }

  async getStats() {
    const stats = { indexed: 0, synced: 0, enriched: 0, failed: 0, total: 0 };
    for await (const pkg of this.streamPackages()) {
      stats.total++;
      if (pkg.state) stats[pkg.state] = (stats[pkg.state] || 0) + 1;
    }
    return stats;
  }

  async updatePackagesBatch(updatesMap) {
    const tempPath = `${this.packagesPath}.tmp`;
    const writeStream = createWriteStream(tempPath);
    
    const processed = new Set();

    try {
      // Update existing packages
      for await (const pkg of this.streamPackages()) {
        const update = updatesMap.get(pkg.name);
        const toWrite = update || pkg;
        writeStream.write(JSON.stringify(toWrite) + '\n');
        if (update) processed.add(pkg.name);
      }

      // Add new packages
      for (const [name, pkg] of updatesMap) {
        if (!processed.has(name)) {
          writeStream.write(JSON.stringify(pkg) + '\n');
        }
      }

      writeStream.end();
      await new Promise((resolve, reject) => {
        writeStream.on('finish', resolve);
        writeStream.on('error', reject);
      });

      await fs.rename(tempPath, this.packagesPath);
      return updatesMap.size;
    } catch (error) {
      if (existsSync(tempPath)) await fs.unlink(tempPath);
      throw error;
    }
  }

  async csvExists() {
    return existsSync(this.csvPath);
  }
}

// ============================================================================
// REGISTRY INDEXER CLASS
// ============================================================================

class RegistryIndexer {
  constructor() {
    this.storage = new FileStorage();
    this.gotClient = got.extend({
      timeout: { request: CONFIG.REQUEST_TIMEOUT },
      retry: { 
        limit: CONFIG.MAX_RETRIES,
        methods: ['GET'],
        statusCodes: [408, 413, 429, 500, 502, 503, 504]
      }
    });
  }

  async getCurrentSequence() {
    const response = await this.gotClient.get(CONFIG.REGISTRY_URL, { 
      responseType: 'json' 
    });
    return response.body.update_seq;
  }

  async fetchChanges(since, limit = CONFIG.BATCH_SIZE) {
    const response = await this.gotClient.get(`${CONFIG.REGISTRY_CHANGES_URL}/_changes`, {
      searchParams: { since, limit },
      responseType: 'json'
    });
    return response.body;
  }

  async runFullIndex() {
    log.info('INDEX', '🌏 Registry: %s', CONFIG.REGISTRY_CHANGES_URL);
    await ensureDataDir();

    const checkpoint = await this.storage.getCheckpoint();
    const startSeq = checkpoint.last_sequence;
    
    let totalSeq;
    try {
      totalSeq = await this.getCurrentSequence();
    } catch (error) {
      log.error('INDEX', 'Failed to connect to registry: %s', error.message);
      throw new Error('Cannot connect to registry. Please check your network connection.');
    }

    if (startSeq >= totalSeq) {
      log.info('INDEX', '✅ Already up to date (seq: %d)', startSeq);
      return { 
        totalPackages: checkpoint.total_packages, 
        lastSequence: startSeq,
        skipped: true 
      };
    }

    log.info('INDEX', 'Syncing from %d → %d (%d changes)', 
      startSeq, totalSeq, totalSeq - startSeq);

    // Load existing packages into Set for deduplication
    const existingPackages = new Set();
    for await (const pkg of this.storage.streamPackages()) {
      existingPackages.add(pkg.name);
    }

    let currentSeq = startSeq;
    let newPackages = 0;
    let totalRecords = 0;
    let batchCount = 0;
    const startTime = Date.now();

    while (currentSeq < totalSeq) {
      try {
        const response = await this.fetchChanges(currentSeq, CONFIG.BATCH_SIZE);
        
        if (!response.results || response.results.length === 0) {
          log.info('INDEX', 'Reached end of changes feed');
          break;
        }

        const batch = [];
        for (const change of response.results) {
          if (change.id && 
              !change.id.startsWith('_design/') && 
              !existingPackages.has(change.id)) {
            batch.push({
              name: change.id,
              state: 'indexed',
              indexed_at: new Date().toISOString(),
              seq: change.seq
            });
            existingPackages.add(change.id);
            newPackages++;
          }
          totalRecords++;
          currentSeq = change.seq;
        }

        if (batch.length > 0) {
          await this.storage.appendPackages(batch);
        }

        batchCount++;
        const progress = ((currentSeq / totalSeq) * 100).toFixed(1);
        const elapsed = Date.now() - startTime;
        const rate = Math.round(totalRecords / (elapsed / 1000));

        log.info('INDEX', 'Batch %d | Seq: %d/%d (%s%%) | New: %d | Total: %d | Rate: %d/s',
          batchCount, currentSeq, totalSeq, progress, newPackages, 
          existingPackages.size, rate);

        // Save checkpoint periodically
        if (batchCount % CONFIG.CHECKPOINT_INTERVAL === 0) {
          await this.storage.saveCheckpoint({
            ...checkpoint,
            last_sequence: currentSeq,
            total_packages: existingPackages.size,
            last_updated: new Date().toISOString()
          });
          log.info('INDEX', '💾 Checkpoint saved');
        }

      } catch (error) {
        log.error('INDEX', 'Error fetching changes: %s', error.message);
        log.warn('INDEX', 'Retrying in 5 seconds...');
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    }

    // Final checkpoint
    await this.storage.saveCheckpoint({
      last_sequence: currentSeq,
      total_packages: existingPackages.size,
      last_updated: new Date().toISOString(),
      enriched_count: checkpoint.enriched_count || 0
    });

    const duration = Date.now() - startTime;
    log.info('INDEX', '✅ Complete!');
    log.info('INDEX', 'Packages: %s (+%s new)', 
      formatNumber(existingPackages.size), formatNumber(newPackages));
    log.info('INDEX', 'Duration: %s', formatDuration(duration));

    return { 
      totalPackages: existingPackages.size, 
      newPackages,
      lastSequence: currentSeq,
      duration 
    };
  }
}

// ============================================================================
// METADATA ENRICHER CLASS
// ============================================================================

class MetadataEnricher {
  constructor() {
    this.storage = new FileStorage();
    this.queue = new PQueue({ 
      concurrency: CONFIG.ENRICH_CONCURRENCY,
      interval: 1000,
      intervalCap: CONFIG.ENRICH_CONCURRENCY * 2
    });
    this.stats = { success: 0, failed: 0, skipped: 0 };
  }

  async fetchPackageMetadata(packageName) {
    try {
      return await registryFetch.json(`/${encodeURIComponent(packageName)}`, {
        registry: CONFIG.REGISTRY_URL,
        timeout: CONFIG.REQUEST_TIMEOUT,
        retry: { retries: CONFIG.MAX_RETRIES }
      });
    } catch (error) {
      if (error.statusCode === 404) {
        log.warn('ENRICH', 'Not found: %s', packageName);
      } else {
        log.error('ENRICH', 'Failed: %s (%s)', packageName, error.message);
      }
      return null;
    }
  }

  extractMetadata(packageData, packageName) {
    if (!packageData) {
      return {
        name: packageName,
        description: null,
        keywords: null,
        latest_version: null,
        publish_time: null,
        dependencies_count: 0,
        file_count: 0,
        unpacked_size: 0,
        homepage: null,
        repository: null,
        license: null,
        author: null,
        npm_url: `https://www.npmjs.com/package/${packageName}`,
        error: 'not_found'
      };
    }

    const {
      description, keywords, time, versions,
      'dist-tags': distTags = {},
      homepage, repository, license, author, maintainers
    } = packageData;

    const latestVersion = distTags.latest;
    const latestVersionData = latestVersion && versions ? versions[latestVersion] : null;

    return {
      name: packageName,
      description: description || latestVersionData?.description || null,
      keywords: Array.isArray(keywords) 
        ? keywords.join(',') 
        : Array.isArray(latestVersionData?.keywords) 
          ? latestVersionData.keywords.join(',') 
          : null,
      latest_version: latestVersion || null,
      publish_time: latestVersion 
        ? time?.[latestVersion] 
        : time?.modified || time?.created || null,
      dependencies_count: Object.keys(latestVersionData?.dependencies || {}).length,
      file_count: latestVersionData?.dist?.fileCount || 0,
      unpacked_size: latestVersionData?.dist?.unpackedSize || 0,
      homepage: homepage || latestVersionData?.homepage || null,
      repository: typeof repository === 'string' 
        ? repository 
        : repository?.url || null,
      license: typeof license === 'string' 
        ? license 
        : license?.type || latestVersionData?.license || null,
      author: typeof author === 'string' 
        ? author 
        : author?.name || null,
      maintainers_count: Array.isArray(maintainers) ? maintainers.length : 0,
      npm_url: `https://www.npmjs.com/package/${packageName}`
    };
  }

  async enrichAll(targetStates = ['indexed', 'synced']) {
    await ensureDataDir();

    // Count packages to enrich
    let totalToEnrich = 0;
    for (const state of targetStates) {
      const count = await this.storage.countByState(state);
      totalToEnrich += count;
      log.info('ENRICH', 'State "%s": %s packages', state, formatNumber(count));
    }

    if (totalToEnrich === 0) {
      log.info('ENRICH', '✅ No packages to enrich');
      return { processed: 0, enriched: 0, failed: 0 };
    }

    log.info('ENRICH', 'Starting: %s packages | Concurrency: %d',
      formatNumber(totalToEnrich), CONFIG.ENRICH_CONCURRENCY);

    let processed = 0;
    let batchNum = 0;
    const startTime = Date.now();
    this.stats = { success: 0, failed: 0, skipped: 0 };

    while (processed < totalToEnrich) {
      batchNum++;

      // Fetch batch from all target states
      let batch = [];
      for (const state of targetStates) {
        const stateBatch = await this.storage.getPackagesByState(
          state,
          CONFIG.BATCH_SIZE
        );
        batch = batch.concat(stateBatch);
        if (batch.length >= CONFIG.BATCH_SIZE) break;
      }

      if (batch.length === 0) break;

      // Process batch with queue
      const updatesMap = new Map();

      await Promise.all(
        batch.map(pkg =>
          this.queue.add(async () => {
            try {
              const packageData = await this.fetchPackageMetadata(pkg.name);
              const metadata = this.extractMetadata(packageData, pkg.name);

              updatesMap.set(pkg.name, {
                ...pkg,
                ...metadata,
                state: packageData ? 'enriched' : 'failed',
                enriched_at: new Date().toISOString()
              });

              if (packageData) {
                this.stats.success++;
              } else {
                this.stats.failed++;
              }
            } catch (error) {
              log.error('ENRICH', 'Error: %s - %s', pkg.name, error.message);
              this.stats.failed++;
              updatesMap.set(pkg.name, {
                ...pkg,
                state: 'failed',
                error: error.message
              });
            }
          })
        )
      );

      // Batch update storage
      await this.storage.updatePackagesBatch(updatesMap);
      processed += batch.length;

      // Progress reporting
      const progress = ((processed / totalToEnrich) * 100).toFixed(1);
      const elapsed = Date.now() - startTime;
      const rate = (this.stats.success / (elapsed / 1000)).toFixed(1);
      const eta = totalToEnrich > processed
        ? formatDuration(((totalToEnrich - processed) / rate) * 1000)
        : '0s';

      log.info('ENRICH', 'Batch %d | Progress: %s/%s (%s%%) | Success: %s | Failed: %s | Rate: %s/s | ETA: %s',
        batchNum, formatNumber(processed), formatNumber(totalToEnrich), progress,
        formatNumber(this.stats.success), formatNumber(this.stats.failed), rate, eta);

      // Save checkpoint
      const checkpoint = await this.storage.getCheckpoint();
      await this.storage.saveCheckpoint({
        ...checkpoint,
        enriched_count: this.stats.success,
        last_enriched: new Date().toISOString()
      });
    }

    const duration = Date.now() - startTime;
    log.info('ENRICH', '✅ Complete!');
    log.info('ENRICH', 'Success: %s | Failed: %s | Duration: %s',
      formatNumber(this.stats.success), formatNumber(this.stats.failed), 
      formatDuration(duration));

    return {
      processed,
      enriched: this.stats.success,
      failed: this.stats.failed,
      duration
    };
  }
}

// ============================================================================
// CSV EXPORTER CLASS
// ============================================================================

class CSVExporter {
  constructor() {
    this.storage = new FileStorage();
  }

  shouldIncludePackage(pkg, filters) {
    if (filters.state && pkg.state !== filters.state) return false;
    if (filters.minSize && (pkg.unpacked_size || 0) < filters.minSize) return false;
    if (filters.maxSize && (pkg.unpacked_size || 0) > filters.maxSize) return false;
    if (filters.minDeps && (pkg.dependencies_count || 0) < filters.minDeps) return false;
    if (filters.maxDeps && (pkg.dependencies_count || 0) > filters.maxDeps) return false;

    if (filters.publishedAfter && pkg.publish_time) {
      if (new Date(pkg.publish_time) < new Date(filters.publishedAfter)) return false;
    }

    if (filters.publishedBefore && pkg.publish_time) {
      if (new Date(pkg.publish_time) > new Date(filters.publishedBefore)) return false;
    }

    return true;
  }

  async export({ filters = {}, output = CSV_FILE } = {}) {
    log.info('EXPORT', '📄 Exporting to: %s', output);

    let rowCount = 0;
    const startTime = Date.now();

    const writeStream = createWriteStream(output);
    const csvStream = csvFormat({
      headers: true,
      quoteColumns: true,
      quoteHeaders: true
    });

    // Progress tracking transform
    const progressTransform = new Transform({
      objectMode: true,
      transform(chunk, encoding, callback) {
        rowCount++;
        if (rowCount % 10000 === 0) {
          const elapsed = Date.now() - startTime;
          const rate = Math.round(rowCount / (elapsed / 1000));
          log.info('EXPORT', 'Progress: %s rows | Rate: %d rows/s',
            formatNumber(rowCount), rate);
        }
        callback(null, chunk);
      }
    });

    // Create readable stream from storage
    const storage = this.storage;
    const shouldInclude = this.shouldIncludePackage.bind(this);

    const packagesStream = new Readable({
      objectMode: true,
      async read() {
        try {
          for await (const pkg of storage.streamPackages()) {
            if (!shouldInclude(pkg, filters)) continue;

            this.push({
              package_name: pkg.name,
              state: pkg.state || 'unknown',
              npm_url: pkg.npm_url || `https://www.npmjs.com/package/${pkg.name}`,
              latest_version: pkg.latest_version || '',
              file_count: pkg.file_count || 0,
              unpacked_size: pkg.unpacked_size || 0,
              dependencies: pkg.dependencies_count || 0,
              publish_time: pkg.publish_time || '',
              description: (pkg.description || '').substring(0, 500),
              keywords: (pkg.keywords || '').substring(0, 200),
              homepage: pkg.homepage || '',
              repository: pkg.repository || '',
              license: pkg.license || '',
              author: pkg.author || '',
              maintainers: pkg.maintainers_count || 0
            });
          }
          this.push(null);
        } catch (error) {
          this.destroy(error);
        }
      }
    });

    try {
      await pipeline(
        packagesStream,
        progressTransform,
        csvStream,
        writeStream
      );

      const duration = Date.now() - startTime;
      log.info('EXPORT', '✅ Complete!');
      log.info('EXPORT', 'Rows: %s | Duration: %s',
        formatNumber(rowCount), formatDuration(duration));

      // Update checkpoint
      const checkpoint = await this.storage.getCheckpoint();
      await this.storage.saveCheckpoint({
        ...checkpoint,
        csv_exported: true,
        csv_row_count: rowCount,
        csv_last_export: new Date().toISOString()
      });

      return { rowCount, output, duration };
    } catch (error) {
      log.error('EXPORT', 'Export failed: %s', error.message);
      throw error;
    }
  }
}

// ============================================================================
// CLI SETUP
// ============================================================================

const program = new Command();

program
  .name('npm-indexer')
  .description('Production-grade NPM registry indexer with CNPM mirror support')
  .version('2.0.0')
  .option('--index', 'Run full index or incremental sync')
  .option('--enrich', 'Enrich package metadata')
  .option('--export', 'Export to CSV')
  .option('--auto', 'Run full workflow: index → enrich → export')
  .option('--status', 'Show current status')
  .option('--output <file>', 'CSV output file path', CSV_FILE)
  .option('--state <state>', 'Filter by state (indexed/synced/enriched/failed)')
  .option('--published-after <date>', 'Filter by publish date (YYYY-MM-DD)')
  .option('--published-before <date>', 'Filter by publish date (YYYY-MM-DD)')
  .option('--min-size <bytes>', 'Minimum package size', parseInt)
  .option('--max-size <bytes>', 'Maximum package size', parseInt)
  .option('--min-deps <count>', 'Minimum dependencies', parseInt)
  .option('--max-deps <count>', 'Maximum dependencies', parseInt)
  .parse(process.argv);

const opts = program.opts();

// ============================================================================
// MAIN EXECUTION
// ============================================================================

async function main() {
  const startTime = Date.now();

  try {
    await ensureDataDir();

    const storage = new FileStorage();
    const indexer = new RegistryIndexer();
    const enricher = new MetadataEnricher();
    const exporter = new CSVExporter();

    // Show status
    if (opts.status) {
      const checkpoint = await storage.getCheckpoint();
      const stats = await storage.getStats();

      console.log('\n═══════════════════════════════════════════════════════');
      console.log('📊 NPM REGISTRY INDEXER STATUS');
      console.log('═══════════════════════════════════════════════════════');
      console.log('\n📦 Registry Checkpoint:');
      console.log('  Last sequence:', formatNumber(checkpoint.last_sequence));
      console.log('  Total packages:', formatNumber(checkpoint.total_packages));
      console.log('  Last updated:', checkpoint.last_updated || 'Never');
      console.log('\n📈 Packages by State:');
      console.log('  Indexed:', formatNumber(stats.indexed));
      console.log('  Synced:', formatNumber(stats.synced));
      console.log('  Enriched:', formatNumber(stats.enriched));
      console.log('  Failed:', formatNumber(stats.failed));
      console.log('  Total:', formatNumber(stats.total));
      console.log('\n🔍 Enrichment Progress:');
      console.log('  Enriched count:', formatNumber(checkpoint.enriched_count || 0));
      console.log('  Last enriched:', checkpoint.last_enriched || 'Never');
      console.log('\n📄 CSV Export:');
      console.log('  Last export:', checkpoint.csv_last_export || 'Never');
      console.log('  Last row count:', formatNumber(checkpoint.csv_row_count || 0));
      console.log('═══════════════════════════════════════════════════════\n');
      return;
    }

    // Auto workflow
    if (opts.auto || (!opts.index && !opts.enrich && !opts.export)) {
      log.info('MAIN', '🚀 Running full workflow');

      await indexer.runFullIndex();
      await enricher.enrichAll(['indexed', 'synced']);
      await exporter.export({ filters: {}, output: opts.output });

      const duration = Date.now() - startTime;
      log.info('MAIN', '✅ Workflow complete! Duration: %s', formatDuration(duration));
      return;
    }

    // Individual operations
    if (opts.index) {
      await indexer.runFullIndex();
    }

    if (opts.enrich) {
      await enricher.enrichAll(['indexed', 'synced']);
    }

    if (opts.export) {
      const filters = {};
      if (opts.state) filters.state = opts.state;
      if (opts.publishedAfter) filters.publishedAfter = opts.publishedAfter;
      if (opts.publishedBefore) filters.publishedBefore = opts.publishedBefore;
      if (opts.minSize) filters.minSize = opts.minSize;
      if (opts.maxSize) filters.maxSize = opts.maxSize;
      if (opts.minDeps) filters.minDeps = opts.minDeps;
      if (opts.maxDeps) filters.maxDeps = opts.maxDeps;

      await exporter.export({ filters, output: opts.output });
    }

    const duration = Date.now() - startTime;
    log.info('MAIN', '✅ Done! Duration: %s', formatDuration(duration));

  } catch (error) {
    log.error('MAIN', '❌ Fatal error: %s', error.message);
    console.error('\nStack trace:');
    console.error(error.stack);
    process.exit(1);
  }
}

// Run main function
main();

