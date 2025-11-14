#!/usr/bin/env node

/**
 * NPM Registry Indexer v3.0.0
 * 
 * Production-grade npm registry indexer with CNPM mirror support
 * Features: Incremental sync, parallel enrichment, streaming CSV export
 */

import fs from 'fs/promises';
import { createReadStream, createWriteStream, existsSync } from 'fs';
import path from 'path';
import log from 'npmlog';
import PQueue from 'p-queue';
import got from 'got';
import registryFetch from 'npm-registry-fetch';
import { Command } from 'commander';
import { format as csvFormat } from 'fast-csv';
import { pipeline as streamPipeline } from 'stream/promises';
import { Transform, Readable } from 'stream';
import readline from 'readline';

// ============================================================================
// CONFIGURATION
// ============================================================================

const CONFIG = {
  REGISTRY_URL: process.env.NPM_REGISTRY_URL || 'https://registry.npmmirror.com',
  REGISTRY_CHANGES_URL: process.env.NPM_CHANGES_URL || 'https://r.cnpmjs.org',
  DATA_DIR: process.env.DATA_DIR || './data',
  BATCH_SIZE: parseInt(process.env.BATCH_SIZE || '1000'),
  ENRICH_CONCURRENCY: parseInt(process.env.ENRICH_CONCURRENCY || '20'),
  REQUEST_TIMEOUT: parseInt(process.env.REQUEST_TIMEOUT || '30000'),
  MAX_RETRIES: parseInt(process.env.MAX_RETRIES || '3'),
  CHECKPOINT_INTERVAL: 100 // Save checkpoint every N batches
};

const CHECKPOINT_FILE = path.join(CONFIG.DATA_DIR, 'checkpoint.json');
const PACKAGES_JSONL = path.join(CONFIG.DATA_DIR, 'packages.jsonl');

// Logging setup
log.heading = 'NPMIndexer';
log.level = process.env.LOG_LEVEL || 'info';

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

async function ensureDataDir() {
  await fs.mkdir(CONFIG.DATA_DIR, { recursive: true });
}

async function safeUnlink(filepath) {
  try {
    if (existsSync(filepath)) {
      await fs.unlink(filepath);
    }
  } catch (error) {
    log.warn('FileSystem', `Failed to delete ${filepath}: ${error.message}`);
  }
}

async function atomicWrite(filepath, data) {
  const tempPath = `${filepath}.tmp`;
  const backupPath = `${filepath}.backup`;
  
  try {
    await fs.writeFile(tempPath, data);
    
    if (existsSync(filepath)) {
      await fs.rename(filepath, backupPath);
    }
    
    await fs.rename(tempPath, filepath);
    await safeUnlink(backupPath);
  } catch (error) {
    if (existsSync(backupPath)) {
      await fs.rename(backupPath, filepath);
    }
    throw error;
  } finally {
    await safeUnlink(tempPath);
  }
}

function formatNumber(num) {
  return num.toLocaleString();
}

function formatDuration(seconds) {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}min`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

// ============================================================================
// FILE STORAGE (JSONL-based with streaming)
// ============================================================================

class FileStorage {
  constructor() {
    this.checkpointPath = CHECKPOINT_FILE;
    this.packagesPath = PACKAGES_JSONL;
  }

  async getCheckpoint() {
    try {
      const data = await fs.readFile(this.checkpointPath, 'utf8');
      return JSON.parse(data);
    } catch (error) {
      return {
        last_sequence: 0,
        total_packages: 0,
        last_updated: null,
        enriched_count: 0,
        last_enriched: null,
        csv_last_export: null,
        csv_row_count: 0,
        version: '3.0.0'
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
    if (!existsSync(this.packagesPath)) {
      return;
    }

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
        log.warn('Storage', `Invalid JSON: ${line.substring(0, 50)}...`);
      }
    }
  }

  async getPackagesByState(state, limit = CONFIG.BATCH_SIZE, offset = 0) {
    const packages = [];
    let count = 0;

    for await (const pkg of this.streamPackages()) {
      if (pkg.state === state) {
        if (count >= offset && packages.length < limit) {
          packages.push(pkg);
        }
        count++;
        if (packages.length >= limit) break;
      }
    }

    return packages;
  }

  async getPackageCountByState(state) {
    let count = 0;
    for await (const pkg of this.streamPackages()) {
      if (pkg.state === state) count++;
    }
    return count;
  }

  async updatePackagesBatch(updatesMap) {
    await ensureDataDir();
    const tempPath = `${this.packagesPath}.tmp`;
    const tempStream = createWriteStream(tempPath);
    let updated = 0;

    try {
      for await (const pkg of this.streamPackages()) {
        const update = updatesMap.get(pkg.name);
        const toWrite = update || pkg;
        if (update) updated++;
        tempStream.write(JSON.stringify(toWrite) + '\n');
      }

      // Add new packages not in original file
      for (const [name, pkg] of updatesMap) {
        let found = false;
        for await (const existing of this.streamPackages()) {
          if (existing.name === name) {
            found = true;
            break;
          }
        }
        if (!found) {
          tempStream.write(JSON.stringify(pkg) + '\n');
        }
      }

      tempStream.end();
      await new Promise((resolve, reject) => {
        tempStream.on('finish', resolve);
        tempStream.on('error', reject);
      });

      await fs.rename(tempPath, this.packagesPath);
      return updated;
    } catch (error) {
      await safeUnlink(tempPath);
      throw error;
    }
  }

  async getStats() {
    const stats = { indexed: 0, synced: 0, enriched: 0, failed: 0, total: 0 };

    for await (const pkg of this.streamPackages()) {
      stats.total++;
      if (pkg.state) {
        stats[pkg.state] = (stats[pkg.state] || 0) + 1;
      }
    }

    return stats;
  }

  csvExists() {
    return existsSync(path.join(CONFIG.DATA_DIR, 'packages.csv'));
  }
}

// ============================================================================
// REGISTRY INDEXER
// ============================================================================

class RegistryIndexer {
  constructor() {
    this.storage = new FileStorage();
    this.gotClient = got.extend({
      timeout: { request: CONFIG.REQUEST_TIMEOUT },
      retry: { limit: CONFIG.MAX_RETRIES },
      hooks: {
        beforeRetry: [
          (error, retryCount) => {
            log.warn('INDEX', `Retry ${retryCount}: ${error.message}`);
          }
        ]
      }
    });
  }

  async getCurrentSequence() {
    try {
      const response = await this.gotClient.get(CONFIG.REGISTRY_URL, {
        responseType: 'json'
      });
      return response.body.update_seq;
    } catch (error) {
      throw new Error(`Cannot connect to registry: ${error.message}`);
    }
  }

  async fetchChanges(since, limit = CONFIG.BATCH_SIZE) {
    const response = await this.gotClient.get(`${CONFIG.REGISTRY_CHANGES_URL}/_changes`, {
      searchParams: { since, limit },
      responseType: 'json'
    });
    return response.body;
  }

  async runFullIndex({ resume = true } = {}) {
    log.info('INDEX', '🌏 Registry: %s', CONFIG.REGISTRY_CHANGES_URL);
    await ensureDataDir();

    const checkpoint = await this.storage.getCheckpoint();
    const startSeq = resume ? checkpoint.last_sequence : 0;
    
    const totalSeq = await this.getCurrentSequence();
    
    if (startSeq >= totalSeq) {
      log.info('INDEX', '✅ Registry is up to date (seq: %s)', formatNumber(startSeq));
      return { totalPackages: checkpoint.total_packages, lastSequence: startSeq, skipped: true };
    }

    log.info('INDEX', 'Syncing from %s → %s (%s changes)',
      formatNumber(startSeq), formatNumber(totalSeq), formatNumber(totalSeq - startSeq));

    // Build existing packages set
    const existingPackages = new Set();
    for await (const pkg of this.storage.streamPackages()) {
      existingPackages.add(pkg.name);
    }

    let currentSeq = startSeq;
    let newPackages = 0;
    let batchNum = 0;
    const startTime = Date.now();

    while (currentSeq < totalSeq) {
      batchNum++;
      const response = await this.fetchChanges(currentSeq, CONFIG.BATCH_SIZE);
      
      if (!response.results || response.results.length === 0) break;

      const batch = [];
      for (const change of response.results) {
        if (change.id && !change.id.startsWith('_design/')) {
          if (!existingPackages.has(change.id)) {
            batch.push({
              name: change.id,
              state: 'indexed',
              indexed_at: new Date().toISOString(),
              seq: change.seq
            });
            existingPackages.add(change.id);
            newPackages++;
          }
        }
        currentSeq = change.seq;
      }

      if (batch.length > 0) {
        await this.storage.appendPackages(batch);
      }

      const rate = Math.round((currentSeq - startSeq) / ((Date.now() - startTime) / 1000));
      
      log.info('INDEX', 'Batch %d | Seq: %s/%s (%s%%) | New: %d | Total: %d | Rate: %d/s',
        batchNum,
        formatNumber(currentSeq),
        formatNumber(totalSeq),
        ((currentSeq / totalSeq) * 100).toFixed(1),
        newPackages,
        existingPackages.size,
        rate
      );

      // Save checkpoint periodically
      if (batchNum % CONFIG.CHECKPOINT_INTERVAL === 0) {
        await this.storage.saveCheckpoint({
          ...checkpoint,
          last_sequence: currentSeq,
          total_packages: existingPackages.size,
          last_updated: new Date().toISOString()
        });
      }
    }

    // Final checkpoint
    await this.storage.saveCheckpoint({
      ...checkpoint,
      last_sequence: currentSeq,
      total_packages: existingPackages.size,
      last_updated: new Date().toISOString()
    });

    const duration = (Date.now() - startTime) / 1000;
    log.info('INDEX', '✅ Complete! Packages: %s (+%s new) | Time: %s',
      formatNumber(existingPackages.size),
      formatNumber(newPackages),
      formatDuration(duration)
    );

    return { totalPackages: existingPackages.size, lastSequence: currentSeq, newPackages };
  }
}

// ============================================================================
// METADATA ENRICHER
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
        log.error('ENRICH', 'Failed %s: %s', packageName, error.message);
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
        dev_dependencies_count: 0,
        file_count: 0,
        unpacked_size: 0,
        homepage: null,
        repository: null,
        license: null,
        author: null,
        maintainers_count: 0,
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
      keywords: Array.isArray(keywords) ? keywords.join(',') :
                Array.isArray(latestVersionData?.keywords) ? latestVersionData.keywords.join(',') : null,
      latest_version: latestVersion || null,
      publish_time: latestVersion ? time?.[latestVersion] : time?.modified || time?.created || null,
      dependencies_count: Object.keys(latestVersionData?.dependencies || {}).length,
      dev_dependencies_count: Object.keys(latestVersionData?.devDependencies || {}).length,
      file_count: latestVersionData?.dist?.fileCount || 0,
      unpacked_size: latestVersionData?.dist?.unpackedSize || 0,
      homepage: homepage || latestVersionData?.homepage || null,
      repository: typeof repository === 'string' ? repository : repository?.url || null,
      license: typeof license === 'string' ? license :
               license?.type || latestVersionData?.license || null,
      author: typeof author === 'string' ? author : author?.name || null,
      maintainers_count: Array.isArray(maintainers) ? maintainers.length : 0,
      npm_url: `https://www.npmjs.com/package/${packageName}`
    };
  }

  async enrichAll(targetStates = ['indexed', 'synced']) {
    await ensureDataDir();

    // Count packages to enrich
    let totalToEnrich = 0;
    for (const state of targetStates) {
      const count = await this.storage.getPackageCountByState(state);
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
        const stateBatch = await this.storage.getPackagesByState(state, CONFIG.BATCH_SIZE, processed);
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
                state: 'enriched',
                enriched_at: new Date().toISOString()
              });

              this.stats.success++;
            } catch (error) {
              log.error('ENRICH', 'Error %s: %s', pkg.name, error.message);
              this.stats.failed++;
            }
          })
        )
      );

      // Batch update storage
      await this.storage.updatePackagesBatch(updatesMap);
      processed += batch.length;

      // Progress reporting
      const elapsed = (Date.now() - startTime) / 1000;
      const rate = (this.stats.success / elapsed).toFixed(1);
      const eta = totalToEnrich > processed ?
        ((totalToEnrich - processed) / rate / 60).toFixed(1) : 0;
      
      log.info('ENRICH', 'Batch %d | Progress: %s/%s (%s%%) | Enriched: %s | Failed: %s | Rate: %s/s | ETA: %s min',
        batchNum,
        formatNumber(processed),
        formatNumber(totalToEnrich),
        ((processed / totalToEnrich) * 100).toFixed(1),
        formatNumber(this.stats.success),
        formatNumber(this.stats.failed),
        rate,
        eta
      );

      // Save checkpoint
      if (batchNum % 10 === 0) {
        const checkpoint = await this.storage.getCheckpoint();
        await this.storage.saveCheckpoint({
          ...checkpoint,
          enriched_count: this.stats.success,
          last_enriched: new Date().toISOString()
        });
      }
    }

    const duration = (Date.now() - startTime) / 1000;
    log.info('ENRICH', '✅ Complete! Success: %s | Failed: %s | Time: %s',
      formatNumber(this.stats.success),
      formatNumber(this.stats.failed),
      formatDuration(duration)
    );

    // Final checkpoint
    const checkpoint = await this.storage.getCheckpoint();
    await this.storage.saveCheckpoint({
      ...checkpoint,
      enriched_count: this.stats.success,
      last_enriched: new Date().toISOString()
    });

    return {
      processed,
      enriched: this.stats.success,
      failed: this.stats.failed
    };
  }
}

// ============================================================================
// CSV EXPORTER
// ============================================================================

class CSVExporter {
  constructor() {
    this.storage = new FileStorage();
  }

  shouldIncludePackage(pkg, filters) {
    if (filters.state && pkg.state !== filters.state) return false;
    if (filters.minSize && (pkg.unpacked_size || 0) < filters.minSize) return false;
    if (filters.maxSize && (pkg.unpacked_size || 0) > filters.maxSize) return false;
    if (filters.minDependencies && (pkg.dependencies_count || 0) < filters.minDependencies) return false;
    if (filters.maxDependencies && (pkg.dependencies_count || 0) > filters.maxDependencies) return false;
    
    if (filters.publishedAfter && pkg.publish_time) {
      if (new Date(pkg.publish_time) < new Date(filters.publishedAfter)) return false;
    }
    
    if (filters.publishedBefore && pkg.publish_time) {
      if (new Date(pkg.publish_time) > new Date(filters.publishedBefore)) return false;
    }

    if (filters.keyword && pkg.keywords) {
      if (!pkg.keywords.toLowerCase().includes(filters.keyword.toLowerCase())) return false;
    }

    if (filters.hasLicense && !pkg.license) return false;
    
    return true;
  }

  async export({ filters = {}, output = path.join(CONFIG.DATA_DIR, 'packages.csv') } = {}) {
    log.info('EXPORT', '📄 Exporting to: %s', output);
    
    let rowCount = 0;
    const startTime = Date.now();
    
    const writeStream = createWriteStream(output, { flags: 'w' });
    const csvStream = csvFormat({
      headers: true,
      quoteColumns: true,
      quoteHeaders: true
    });

    // Progress tracking
    const progressTransform = new Transform({
      objectMode: true,
      transform(chunk, encoding, callback) {
        rowCount++;
        if (rowCount % 10000 === 0) {
          const elapsed = (Date.now() - startTime) / 1000;
          const rate = (rowCount / elapsed).toFixed(0);
          log.info('EXPORT', 'Progress: %s rows | Rate: %s/s', formatNumber(rowCount), rate);
        }
        callback(null, chunk);
      }
    });

    // Create readable stream
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
              file_number: pkg.file_count || 0,
              unpacked_size: pkg.unpacked_size || 0,
              dependencies: pkg.dependencies_count || 0,
              dev_dependencies: pkg.dev_dependencies_count || 0,
              latest_release_published_at: pkg.publish_time || '',
              description: pkg.description || '',
              keywords: pkg.keywords || '',
              homepage: pkg.homepage || '',
              repository: pkg.repository || '',
              license: pkg.license || '',
              author: pkg.author || '',
              maintainers_count: pkg.maintainers_count || 0
            });
          }
          this.push(null);
        } catch (error) {
          this.destroy(error);
        }
      }
    });

    try {
      await streamPipeline(packagesStream, progressTransform, csvStream, writeStream);

      const duration = (Date.now() - startTime) / 1000;
      log.info('EXPORT', '✅ Complete! Rows: %s | Time: %s',
        formatNumber(rowCount), formatDuration(duration));

      // Update checkpoint
      const checkpoint = await this.storage.getCheckpoint();
      await this.storage.saveCheckpoint({
        ...checkpoint,
        csv_last_export: new Date().toISOString(),
        csv_row_count: rowCount
      });

      return { rowCount, output, duration };
    } catch (error) {
      log.error('EXPORT', 'Failed: %s', error.message);
      throw error;
    }
  }
}

// ============================================================================
// CLI
// ============================================================================

const program = new Command();

program
  .name('npm-indexer')
  .description('Production NPM Registry Indexer')
  .version('3.0.0')
  .option('--index', 'Run indexing (incremental sync)')
  .option('--enrich', 'Enrich package metadata')
  .option('--export', 'Export to CSV')
  .option('--auto', 'Run full workflow: index → enrich → export')
  .option('--status', 'Show current status')
  .option('--stats', 'Show package statistics')
  .option('--output <file>', 'CSV output file')
  .option('--state <state>', 'Filter by state')
  .option('--published-after <date>', 'Filter by publish date (YYYY-MM-DD)')
  .option('--published-before <date>', 'Filter by publish date (YYYY-MM-DD)')
  .option('--min-size <bytes>', 'Minimum package size', parseInt)
  .option('--max-size <bytes>', 'Maximum package size', parseInt)
  .option('--min-deps <count>', 'Minimum dependencies', parseInt)
  .option('--max-deps <count>', 'Maximum dependencies', parseInt)
  .option('--keyword <keyword>', 'Filter by keyword')
  .option('--has-license', 'Only packages with license')
  .parse(process.argv);

const opts = program.opts();

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  try {
    await ensureDataDir();

    const storage = new FileStorage();
    const indexer = new RegistryIndexer();
    const enricher = new MetadataEnricher();
    const exporter = new CSVExporter();

    // Show statistics
    if (opts.stats) {
      log.info('STATS', '📊 Calculating...');
      const stats = await storage.getStats();
      console.log('\n═══════════════════════════════════════════════════════');
      console.log('📊 Package Statistics');
      console.log('═══════════════════════════════════════════════════════');
      console.log('  Indexed:', formatNumber(stats.indexed || 0));
      console.log('  Synced:', formatNumber(stats.synced || 0));
      console.log('  Enriched:', formatNumber(stats.enriched || 0));
      console.log('  Failed:', formatNumber(stats.failed || 0));
      console.log('  Total:', formatNumber(stats.total || 0));
      console.log('═══════════════════════════════════════════════════════');
      return;
    }

    // Show status
    if (opts.status) {
      const checkpoint = await storage.getCheckpoint();
      const csvExists = storage.csvExists();
      const stats = await storage.getStats();

      console.log('\n═══════════════════════════════════════════════════════');
      console.log('📊 NPM REGISTRY INDEXER STATUS');
      console.log('═══════════════════════════════════════════════════════');
      console.log('\n📦 Registry Checkpoint:');
      console.log('  Last sequence:', formatNumber(checkpoint.last_sequence));
      console.log('  Total packages:', formatNumber(checkpoint.total_packages));
      console.log('  Last updated:', checkpoint.last_updated || 'Never');
      console.log('\n📈 Packages by State:');
      console.log('  Indexed:', formatNumber(stats.indexed || 0));
      console.log('  Synced:', formatNumber(stats.synced || 0));
      console.log('  Enriched:', formatNumber(stats.enriched || 0));
      console.log('  Failed:', formatNumber(stats.failed || 0));
      console.log('  Total:', formatNumber(stats.total));
      console.log('\n🔍 Enrichment Progress:');
      console.log('  Enriched count:', formatNumber(checkpoint.enriched_count));
      console.log('  Last enriched:', checkpoint.last_enriched || 'Never');
      console.log('\n📄 CSV Export:');
      console.log('  Last export:', checkpoint.csv_last_export || 'Never');
      console.log('  Last row count:', formatNumber(checkpoint.csv_row_count || 0));
      console.log('═══════════════════════════════════════════════════════');
      return;
    }

    // Run workflow
    if (opts.auto) {
      log.info('MAIN', '🚀 Running full workflow...');
      await indexer.runFullIndex();
      await enricher.enrichAll();
      await exporter.export({ output: opts.output });
      log.info('MAIN', '✅ Full workflow complete!');
      return;
    }

    if (opts.index) {
      await indexer.runFullIndex();
    }

    if (opts.enrich) {
      await enricher.enrichAll();
    }

    if (opts.export) {
      const filters = {
        state: opts.state,
        minSize: opts.minSize,
        maxSize: opts.maxSize,
        minDependencies: opts.minDeps,
        maxDependencies: opts.maxDeps,
        publishedAfter: opts.publishedAfter,
        publishedBefore: opts.publishedBefore,
        keyword: opts.keyword,
        hasLicense: opts.hasLicense
      };

      await exporter.export({ filters, output: opts.output });
    }

    // Default: show help
    if (!opts.index && !opts.enrich && !opts.export && !opts.auto && !opts.status && !opts.stats) {
      program.help();
    }

  } catch (error) {
    log.error('MAIN', 'Fatal error: %s', error.message);
    console.error(error);
    process.exit(1);
  }
}

main();

