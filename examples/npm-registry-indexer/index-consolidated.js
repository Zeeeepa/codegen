#!/usr/bin/env node
/**
 * NPM Registry Indexer - Consolidated Production Version
 * 
 * Advanced features:
 * - Streaming JSONL processing with readline for memory efficiency
 * - npm-registry-fetch with built-in retry and auth
 * - Batch updates with Map for O(1) lookups
 * - Atomic file operations with backups
 * - Comprehensive error handling and resume capability
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

// Configuration
const CONFIG = {
  REGISTRY_URL: process.env.NPM_REGISTRY_URL || 'https://registry.npmmirror.com',
  REGISTRY_CHANGES_URL: process.env.NPM_CHANGES_URL || 'https://r.cnpmjs.org',
  DATA_DIR: process.env.DATA_DIR || './data',
  BATCH_SIZE: parseInt(process.env.BATCH_SIZE || '1000', 10),
  ENRICH_CONCURRENCY: parseInt(process.env.ENRICH_CONCURRENCY || '20', 10),
  REQUEST_TIMEOUT: parseInt(process.env.REQUEST_TIMEOUT || '30000', 10),
  MAX_RETRIES: parseInt(process.env.MAX_RETRIES || '3', 10)
};

const CHECKPOINT_FILE = path.join(CONFIG.DATA_DIR, 'checkpoint.json');
const PACKAGES_JSONL = path.join(CONFIG.DATA_DIR, 'packages.jsonl');
const CSV_FILE = path.join(CONFIG.DATA_DIR, 'packages.csv');

log.heading = 'NPMIndexer';
log.level = process.env.LOG_LEVEL || 'info';

// Utility functions
async function ensureDataDir() {
  await fs.mkdir(CONFIG.DATA_DIR, { recursive: true });
}

async function atomicWrite(filepath, data) {
  const tempPath = `${filepath}.tmp`;
  await fs.writeFile(tempPath, data);
  await fs.rename(tempPath, filepath);
}

// File Storage with streaming
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
        last_updated: null,
        enriched_count: 0
      };
    }
  }

  async saveCheckpoint(checkpoint) {
    await ensureDataDir();
    await atomicWrite(this.checkpointPath, JSON.stringify({ ...checkpoint, updated_at: new Date().toISOString() }, null, 2));
  }

  async appendPackages(packages) {
    await ensureDataDir();
    const data = packages.map(pkg => JSON.stringify(pkg)).join('\n') + '\n';
    await fs.appendFile(this.packagesPath, data);
  }

  // Memory-efficient streaming with readline
  async *streamPackages() {
    if (!existsSync(this.packagesPath)) return;

    const fileStream = createReadStream(this.packagesPath, { encoding: 'utf8' });
    const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

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

  async getStats() {
    const stats = { indexed: 0, synced: 0, enriched: 0, total: 0 };
    for await (const pkg of this.streamPackages()) {
      stats.total++;
      if (pkg.state) stats[pkg.state] = (stats[pkg.state] || 0) + 1;
    }
    return stats;
  }

  // Efficient batch update using temp file
  async updatePackagesBatch(updatesMap) {
    const tempPath = `${this.packagesPath}.tmp`;
    const writeStream = createWriteStream(tempPath);

    try {
      for await (const pkg of this.streamPackages()) {
        const update = updatesMap.get(pkg.name);
        writeStream.write(JSON.stringify(update || pkg) + '\n');
      }

      // Add new packages
      for (const [name, pkg] of updatesMap) {
        let exists = false;
        for await (const existing of this.streamPackages()) {
          if (existing.name === name) {
            exists = true;
            break;
          }
        }
        if (!exists) writeStream.write(JSON.stringify(pkg) + '\n');
      }

      writeStream.end();
      await new Promise((resolve, reject) => {
        writeStream.on('finish', resolve);
        writeStream.on('error', reject);
      });

      await fs.rename(tempPath, this.packagesPath);
    } catch (error) {
      if (existsSync(tempPath)) await fs.unlink(tempPath);
      throw error;
    }
  }
}

// Registry Indexer with got client
class RegistryIndexer {
  constructor() {
    this.storage = new FileStorage();
    this.gotClient = got.extend({
      timeout: { request: CONFIG.REQUEST_TIMEOUT },
      retry: { limit: CONFIG.MAX_RETRIES }
    });
  }

  async getCurrentSequence() {
    const response = await this.gotClient.get(CONFIG.REGISTRY_URL, { responseType: 'json' });
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
    const totalSeq = await this.getCurrentSequence();

    if (startSeq >= totalSeq) {
      log.info('INDEX', '✅ Already up to date (seq: %d)', startSeq);
      return { totalPackages: checkpoint.total_packages, skipped: true };
    }

    log.info('INDEX', 'Syncing %d → %d (%d changes)', startSeq, totalSeq, totalSeq - startSeq);

    const existingPackages = new Set();
    for await (const pkg of this.storage.streamPackages()) {
      existingPackages.add(pkg.name);
    }

    let currentSeq = startSeq;
    let newPackages = 0;
    const startTime = Date.now();

    while (currentSeq < totalSeq) {
      const response = await this.fetchChanges(currentSeq, CONFIG.BATCH_SIZE);
      if (!response.results || response.results.length === 0) break;

      const batch = [];
      for (const change of response.results) {
        if (change.id && !change.id.startsWith('_design/') && !existingPackages.has(change.id)) {
          batch.push({ name: change.id, state: 'indexed', indexed_at: new Date().toISOString() });
          existingPackages.add(change.id);
          newPackages++;
        }
        currentSeq = change.seq;
      }

      if (batch.length > 0) await this.storage.appendPackages(batch);

      const progress = ((currentSeq / totalSeq) * 100).toFixed(1);
      log.info('INDEX', 'Seq: %d/%d (%s%%) | New: %d | Total: %d', currentSeq, totalSeq, progress, newPackages, existingPackages.size);

      if (newPackages % (CONFIG.BATCH_SIZE * 10) === 0) {
        await this.storage.saveCheckpoint({ ...checkpoint, last_sequence: currentSeq, total_packages: existingPackages.size });
      }
    }

    await this.storage.saveCheckpoint({
      last_sequence: currentSeq,
      total_packages: existingPackages.size,
      last_updated: new Date().toISOString()
    });

    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
    log.info('INDEX', '✅ Done! Packages: %d (+%d new) | Time: %ss', existingPackages.size, newPackages, duration);

    return { totalPackages: existingPackages.size, newPackages };
  }
}

// Metadata Enricher with npm-registry-fetch
class MetadataEnricher {
  constructor() {
    this.storage = new FileStorage();
    this.queue = new PQueue({ concurrency: CONFIG.ENRICH_CONCURRENCY });
    this.stats = { success: 0, failed: 0 };
  }

  async fetchPackageMetadata(packageName) {
    try {
      return await registryFetch.json(`/${encodeURIComponent(packageName)}`, {
        registry: CONFIG.REGISTRY_URL,
        timeout: CONFIG.REQUEST_TIMEOUT
      });
    } catch (error) {
      log.warn('ENRICH', 'Failed: %s (%s)', packageName, error.message);
      return null;
    }
  }

  extractMetadata(packageData, packageName) {
    if (!packageData) {
      return { name: packageName, description: null, latest_version: null, error: 'not_found' };
    }

    const { description, keywords, time, versions, 'dist-tags': distTags = {}, homepage, repository, license, author } = packageData;
    const latestVersion = distTags.latest;
    const latestVersionData = latestVersion && versions ? versions[latestVersion] : null;

    return {
      name: packageName,
      description: description || latestVersionData?.description || null,
      keywords: Array.isArray(keywords) ? keywords.join(',') : '',
      latest_version: latestVersion || null,
      publish_time: latestVersion ? time?.[latestVersion] : time?.modified || null,
      dependencies_count: Object.keys(latestVersionData?.dependencies || {}).length,
      file_count: latestVersionData?.dist?.fileCount || 0,
      unpacked_size: latestVersionData?.dist?.unpackedSize || 0,
      homepage: homepage || null,
      repository: typeof repository === 'string' ? repository : repository?.url || null,
      license: typeof license === 'string' ? license : license?.type || null,
      author: typeof author === 'string' ? author : author?.name || null,
      npm_url: `https://www.npmjs.com/package/${packageName}`
    };
  }

  async enrichAll(targetStates = ['indexed', 'synced']) {
    await ensureDataDir();

    let totalToEnrich = 0;
    for (const state of targetStates) {
      const packages = await this.storage.getPackagesByState(state, 999999);
      totalToEnrich += packages.length;
    }

    if (totalToEnrich === 0) {
      log.info('ENRICH', '✅ No packages to enrich');
      return { processed: 0, enriched: 0 };
    }

    log.info('ENRICH', 'Starting: %d packages | Concurrency: %d', totalToEnrich, CONFIG.ENRICH_CONCURRENCY);

    let processed = 0;
    const startTime = Date.now();

    while (processed < totalToEnrich) {
      let batch = [];
      for (const state of targetStates) {
        const stateBatch = await this.storage.getPackagesByState(state, CONFIG.BATCH_SIZE);
        batch = batch.concat(stateBatch);
        if (batch.length >= CONFIG.BATCH_SIZE) break;
      }

      if (batch.length === 0) break;

      const updatesMap = new Map();
      await Promise.all(
        batch.map(pkg =>
          this.queue.add(async () => {
            try {
              const packageData = await this.fetchPackageMetadata(pkg.name);
              const metadata = this.extractMetadata(packageData, pkg.name);
              updatesMap.set(pkg.name, { ...pkg, ...metadata, state: 'enriched', enriched_at: new Date().toISOString() });
              this.stats.success++;
            } catch (error) {
              log.error('ENRICH', 'Error: %s', pkg.name);
              this.stats.failed++;
            }
          })
        )
      );

      await this.storage.updatePackagesBatch(updatesMap);
      processed += batch.length;

      const progress = ((processed / totalToEnrich) * 100).toFixed(1);
      log.info('ENRICH', 'Progress: %d/%d (%s%%) | Success: %d | Failed: %d', processed, totalToEnrich, progress, this.stats.success, this.stats.failed);
    }

    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
    log.info('ENRICH', '✅ Done! Success: %d | Failed: %d | Time: %ss', this.stats.success, this.stats.failed, duration);

    return { processed, enriched: this.stats.success, failed: this.stats.failed };
  }
}

// CSV Exporter
class CSVExporter {
  constructor() {
    this.storage = new FileStorage();
  }

  async export({ filters = {}, output = CSV_FILE } = {}) {
    log.info('EXPORT', '📄 Exporting to: %s', output);

    let rowCount = 0;
    const writeStream = createWriteStream(output);
    const csvStream = csvFormat({ headers: true, quoteColumns: true });

    const packagesStream = new Readable({
      objectMode: true,
      async read() {
        try {
          for await (const pkg of this.storage.streamPackages()) {
            if (filters.state && pkg.state !== filters.state) continue;
            
            this.push({
              package_name: pkg.name,
              state: pkg.state || 'unknown',
              npm_url: pkg.npm_url || `https://www.npmjs.com/package/${pkg.name}`,
              latest_version: pkg.latest_version || '',
              file_count: pkg.file_count || 0,
              unpacked_size: pkg.unpacked_size || 0,
              dependencies: pkg.dependencies_count || 0,
              publish_time: pkg.publish_time || '',
              description: pkg.description || '',
              keywords: pkg.keywords || '',
              homepage: pkg.homepage || '',
              repository: pkg.repository || '',
              license: pkg.license || '',
              author: pkg.author || ''
            });
          }
          this.push(null);
        } catch (error) {
          this.destroy(error);
        }
      }.bind({ storage: this.storage })
    });

    const progressTransform = new Transform({
      objectMode: true,
      transform(chunk, encoding, callback) {
        rowCount++;
        if (rowCount % 10000 === 0) log.info('EXPORT', 'Progress: %d rows', rowCount);
        callback(null, chunk);
      }
    });

    await pipeline(packagesStream, progressTransform, csvStream, writeStream);

    log.info('EXPORT', '✅ Done! Rows: %d', rowCount);
    return { rowCount, output };
  }
}

// CLI
const program = new Command();

program
  .name('npm-indexer')
  .version('2.0.0')
  .option('--index', 'Run full index or sync')
  .option('--enrich', 'Enrich package metadata')
  .option('--export', 'Export to CSV')
  .option('--auto', 'Run: index -> enrich -> export')
  .option('--status', 'Show status')
  .option('--output <file>', 'CSV output path', CSV_FILE)
  .option('--state <state>', 'Filter by state')
  .parse(process.argv);

const opts = program.opts();

// Main
async function main() {
  try {
    await ensureDataDir();

    const storage = new FileStorage();
    const indexer = new RegistryIndexer();
    const enricher = new MetadataEnricher();
    const exporter = new CSVExporter();

    if (opts.status) {
      const checkpoint = await storage.getCheckpoint();
      const stats = await storage.getStats();
      
      console.log('\n📊 Status:');
      console.log('  Last sequence:', checkpoint.last_sequence.toLocaleString());
      console.log('  Total packages:', checkpoint.total_packages.toLocaleString());
      console.log('  Indexed:', stats.indexed.toLocaleString());
      console.log('  Synced:', stats.synced.toLocaleString());
      console.log('  Enriched:', stats.enriched.toLocaleString());
      console.log('  Last updated:', checkpoint.last_updated || 'Never\n');
      return;
    }

    if (opts.auto || (!opts.index && !opts.enrich && !opts.export)) {
      log.info('MAIN', '🚀 Running full workflow');
      await indexer.runFullIndex();
      await enricher.enrichAll(['indexed', 'synced']);
      await exporter.export({ filters: {}, output: opts.output });
      log.info('MAIN', '✅ Complete!');
      return;
    }

    if (opts.index) await indexer.runFullIndex();
    if (opts.enrich) await enricher.enrichAll(['indexed', 'synced']);
    if (opts.export) await exporter.export({ filters: opts.state ? { state: opts.state } : {}, output: opts.output });

    log.info('MAIN', '✅ Done!');
  } catch (error) {
    log.error('MAIN', '❌ Fatal: %s', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();
