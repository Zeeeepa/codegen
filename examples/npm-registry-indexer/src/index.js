#!/usr/bin/env node
/**
 * NPM Registry Indexer v2.0
 * Production-grade indexer with sharded storage, intelligent enrichment, and streaming export
 */

import { Command } from 'commander';
import log from 'npmlog';
import got from 'got';
import PQueue from 'p-queue';
import fastcsv from 'fast-csv';
import { createWriteStream } from 'fs';
import { pipeline } from 'stream/promises';
import { Transform, Readable } from 'stream';
import { ShardedStorage } from './storage.js';

const { format: csvStringify } = fastcsv;

// Configuration
const REGISTRY_URL = 'https://registry.npmmirror.com';
const REGISTRY_CHANGES_URL = 'https://r.cnpmjs.org';
const BATCH_SIZE = 1000;
const ENRICH_CONCURRENCY = 10;
const REQUEST_TIMEOUT = 30000;
const REQUEST_DELAY = 5;
const CHECKPOINT_INTERVAL = 100;

log.heading = 'NPMIndexer';
log.level = 'info';

class RegistryIndexer {
  constructor(storage) {
    this.storage = storage;
  }

  async getRegistryStatus() {
    const { body } = await got(REGISTRY_URL, { 
      responseType: 'json', 
      timeout: { request: REQUEST_TIMEOUT } 
    });
    return {
      update_seq: body.update_seq,
      doc_count: body.doc_count,
      last_package: body.last_package,
      last_package_version: body.last_package_version,
      instance_start_time: body.instance_start_time,
      cache_time: body.cache_time
    };
  }

  async fetchChanges(since, limit = BATCH_SIZE) {
    try {
      const { body } = await got(`${REGISTRY_CHANGES_URL}/_changes`, {
        searchParams: { since, limit, feed: 'longpoll' },
        responseType: 'json',
        timeout: { request: REQUEST_TIMEOUT }
      });
      return body;
    } catch (error) {
      log.warn('Sync', 'Request failed, retrying...');
      await new Promise(resolve => setTimeout(resolve, 2000));
      const { body } = await got(`${REGISTRY_CHANGES_URL}/_changes`, {
        searchParams: { since, limit },
        responseType: 'json',
        timeout: { request: REQUEST_TIMEOUT }
      });
      return body;
    }
  }

  async sync({ fullIndex = false } = {}) {
    log.info('Sync', '🌏 CNPM Mirror: %s', REGISTRY_CHANGES_URL);
    
    const state = await this.storage.loadState();
    const registryStatus = await this.getRegistryStatus();
    
    let currentSeq = fullIndex ? 0 : state.last_sequence;
    const targetSeq = registryStatus.update_seq;
    
    log.info('Sync', 'Registry seq: %d | Local seq: %d', targetSeq, currentSeq);
    
    if (currentSeq >= targetSeq && !fullIndex) {
      log.info('Sync', '✓ Already up to date');
      return { synced: 0, lastSeq: currentSeq };
    }

    const allPackages = new Set();
    let recordCount = 0, lastSeq = currentSeq, checkpointCounter = 0;
    const startTime = Date.now();

    while (lastSeq < targetSeq) {
      const response = await this.fetchChanges(lastSeq, BATCH_SIZE);
      if (!response.results || response.results.length === 0) break;

      for (const change of response.results) {
        if (change.id && !change.id.startsWith('_design/')) {
          allPackages.add(change.id);
          await this.storage.writePackage(change.id, {
            name: change.id,
            state: fullIndex ? 'indexed' : 'synced',
            synced_at: new Date().toISOString(),
            seq: change.seq
          });
        }
        recordCount++;
        lastSeq = change.seq;
      }

      checkpointCounter++;
      if (checkpointCounter >= CHECKPOINT_INTERVAL) {
        await this.storage.saveState({
          ...state,
          last_sequence: lastSeq,
          total_packages: allPackages.size,
          last_updated: new Date().toISOString(),
          registry_update_seq: targetSeq,
          registry_doc_count: registryStatus.doc_count
        });
        checkpointCounter = 0;
      }

      const progress = ((lastSeq / targetSeq) * 100).toFixed(1);
      const elapsed = (Date.now() - startTime) / 1000;
      const rate = Math.round(recordCount / elapsed);
      log.info('Sync', 'Records: %d | Unique: %d | Progress: %s%% | Rate: %d/s', 
        recordCount, allPackages.size, progress, rate);
    }

    await this.storage.saveState({
      last_sequence: lastSeq,
      total_packages: allPackages.size,
      last_updated: new Date().toISOString(),
      registry_update_seq: targetSeq,
      registry_doc_count: registryStatus.doc_count
    });

    log.info('Sync', '✅ Complete! Synced: %d packages', allPackages.size);
    return { synced: allPackages.size, lastSeq };
  }
}

class MetadataEnricher {
  constructor(storage, concurrency = ENRICH_CONCURRENCY) {
    this.storage = storage;
    this.queue = new PQueue({ concurrency });
    this.stats = { processed: 0, enriched: 0, failed: 0, skipped: 0 };
  }

  async fetchPackageMetadata(name) {
    try {
      const { body } = await got(`${REGISTRY_URL}/${encodeURIComponent(name)}`, {
        responseType: 'json',
        timeout: { request: REQUEST_TIMEOUT }
      });
      return body;
    } catch (error) {
      if (error.response?.statusCode === 404) return null;
      log.warn('Enrich', 'Failed to fetch %s: %s', name, error.message);
      return null;
    }
  }

  async fetchDownloadStats(name) {
    try {
      const { body } = await got(`https://api.npmjs.org/downloads/point/last-week/${encodeURIComponent(name)}`, {
        responseType: 'json',
        timeout: { request: 10000 }
      });
      return body.downloads || 0;
    } catch {
      return null;
    }
  }

  extractMetadata(pkgData, name) {
    if (!pkgData) return { name, state: 'failed' };

    const distTags = pkgData['dist-tags'] || {};
    const latestVer = distTags.latest;
    const versions = pkgData.versions || {};
    const latestData = latestVer ? versions[latestVer] : null;
    const time = pkgData.time || {};

    return {
      name,
      description: (pkgData.description || latestData?.description || '').substring(0, 1000),
      keywords: ((pkgData.keywords || latestData?.keywords || []).join(',') || '').substring(0, 500),
      latest_version: latestVer || null,
      publish_time: latestVer ? time[latestVer] : time.modified || time.created || null,
      dependencies_count: Object.keys(latestData?.dependencies || {}).length,
      file_count: latestData?.dist?.fileCount || 0,
      unpacked_size: latestData?.dist?.unpackedSize || 0,
      license: latestData?.license || pkgData.license || null,
      repository_url: latestData?.repository?.url || pkgData.repository?.url || null,
      maintainers_count: (pkgData.maintainers || []).length,
      deprecated: latestData?.deprecated || false,
      has_types: !!(latestData?.types || latestData?.typings),
      scoped: name.startsWith('@'),
      npm_url: `https://www.npmjs.com/package/${name}`,
      state: 'enriched',
      enriched_at: new Date().toISOString()
    };
  }

  async enrichPackage(pkg) {
    try {
      if (pkg.state === 'enriched') {
        this.stats.skipped++;
        return false;
      }

      const pkgData = await this.fetchPackageMetadata(pkg.name);
      await new Promise(resolve => setTimeout(resolve, REQUEST_DELAY));
      
      const metadata = this.extractMetadata(pkgData, pkg.name);
      
      // Optionally fetch download stats
      const downloads = await this.fetchDownloadStats(pkg.name);
      if (downloads !== null) metadata.downloads_last_week = downloads;

      await this.storage.updatePackage(pkg.name, metadata);
      this.stats.enriched++;
      return true;
    } catch (error) {
      log.error('Enrich', 'Error enriching %s: %s', pkg.name, error.message);
      this.stats.failed++;
      return false;
    }
  }

  async enrichAll(targetStates = ['indexed', 'synced']) {
    log.info('Enrich', 'Starting enrichment...');
    const startTime = Date.now();

    let totalToEnrich = 0;
    for (const state of targetStates) {
      totalToEnrich += await this.storage.countByState(state);
    }

    if (totalToEnrich === 0) {
      log.info('Enrich', 'No packages to enrich');
      return this.stats;
    }

    log.info('Enrich', 'Total packages to enrich: %d', totalToEnrich);

    let processed = 0, batchNum = 0;
    while (processed < totalToEnrich) {
      batchNum++;
      let batch = [];
      
      for (const state of targetStates) {
        const stateBatch = await this.storage.getPackagesByState(state, BATCH_SIZE, 0);
        batch = batch.concat(stateBatch);
        if (batch.length >= BATCH_SIZE) break;
      }

      if (batch.length === 0) break;

      await Promise.all(batch.map(pkg => this.queue.add(() => this.enrichPackage(pkg))));

      this.stats.processed += batch.length;
      processed += batch.length;

      const elapsed = (Date.now() - startTime) / 1000;
      const rate = Math.round(this.stats.processed / elapsed);
      const progress = ((this.stats.processed / totalToEnrich) * 100).toFixed(1);
      const eta = totalToEnrich > this.stats.processed ? 
        ((totalToEnrich - this.stats.processed) / rate / 60).toFixed(1) : 0;

      log.info('Enrich', 'Batch %d | Progress: %d/%d (%s%%) | Enriched: %d | Rate: %d/s | ETA: %smin',
        batchNum, this.stats.processed, totalToEnrich, progress, this.stats.enriched, rate, eta);
    }

    const duration = ((Date.now() - startTime) / 60000).toFixed(2);
    log.info('Enrich', '✓✓✓ COMPLETE ✓✓✓');
    log.info('Enrich', 'Duration: %smin | Enriched: %d | Failed: %d', 
      duration, this.stats.enriched, this.stats.failed);

    return this.stats;
  }
}

class CSVExporter {
  constructor(storage) {
    this.storage = storage;
  }

  applyFilters(pkg, filters) {
    if (filters.state && pkg.state !== filters.state) return false;
    if (filters.minSize && pkg.unpacked_size < filters.minSize) return false;
    if (filters.maxSize && pkg.unpacked_size > filters.maxSize) return false;
    if (filters.minDependencies && pkg.dependencies_count < filters.minDependencies) return false;
    if (filters.maxDependencies && pkg.dependencies_count > filters.maxDependencies) return false;
    if (filters.publishedAfter && pkg.publish_time &&
        new Date(pkg.publish_time) < new Date(filters.publishedAfter)) return false;
    if (filters.publishedBefore && pkg.publish_time &&
        new Date(pkg.publish_time) > new Date(filters.publishedBefore)) return false;
    return true;
  }

  async export({ filters = {}, output = './data/packages.csv' }) {
    log.info('Export', 'Output: %s', output);
    log.info('Export', 'Filters: %j', filters);

    const columns = [
      'name', 'state', 'npm_url', 'file_count', 'unpacked_size', 'dependencies_count',
      'downloads_last_week', 'publish_time', 'description', 'keywords', 'latest_version',
      'license', 'repository_url', 'maintainers_count', 'deprecated', 'has_types', 'scoped'
    ];

    const writeStream = createWriteStream(output);
    const csvStream = csvStringify({ headers: columns, quoted: true, quoted_empty: true });

    let rowCount = 0, lastReport = Date.now();
    const startTime = Date.now();

    const progressTransform = new Transform({
      objectMode: true,
      transform(chunk, encoding, callback) {
        rowCount++;
        const now = Date.now();
        if (rowCount % 10000 === 0 || now - lastReport > 5000) {
          const elapsed = (now - startTime) / 1000;
          const rate = Math.round(rowCount / elapsed);
          log.info('Export', 'Progress: %d rows (%d/s)', rowCount, rate);
          lastReport = now;
        }
        callback(null, chunk);
      }
    });

    const packageStream = Readable.from((async function* (self) {
      for await (const pkg of self.storage.packagesStream()) {
        if (self.applyFilters(pkg, filters)) {
          yield pkg;
        }
      }
    })(this));

    log.info('Export', 'Starting streaming export...');
    await pipeline(packageStream, progressTransform, csvStream, writeStream);

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    log.info('Export', '✓✓✓ COMPLETE ✓✓✓');
    log.info('Export', 'Duration: %ss | Rows: %d', duration, rowCount);

    return { rowCount, duration, output };
  }
}

async function showStatus(storage) {
  log.info('Status', 'Fetching registry and local status...');
  
  const indexer = new RegistryIndexer(storage);
  const registryStatus = await indexer.getRegistryStatus();
  const localState = await storage.loadState();
  const storageStats = await storage.getStats();

  console.log('\n═══════════════════════════════════════════════════════');
  console.log('📊 REGISTRY STATUS');
  console.log('═══════════════════════════════════════════════════════');
  console.log(`Registry Update Seq: ${registryStatus.update_seq.toLocaleString()}`);
  console.log(`Registry Doc Count:  ${registryStatus.doc_count.toLocaleString()}`);
  console.log(`Last Package:        ${registryStatus.last_package}`);
  console.log(`Cache Time:          ${registryStatus.cache_time}`);

  console.log('\n═══════════════════════════════════════════════════════');
  console.log('💾 LOCAL STATUS');
  console.log('═══════════════════════════════════════════════════════');
  console.log(`Last Synced Seq:     ${localState.last_sequence.toLocaleString()}`);
  console.log(`Total Packages:      ${storageStats.totalPackages.toLocaleString()}`);
  console.log(`Storage Size:        ${(storageStats.totalSize / 1024 / 1024).toFixed(2)} MB`);
  console.log(`Shard Count:         ${storageStats.shardCount}`);
  console.log(`Last Updated:        ${localState.last_updated || 'Never'}`);

  console.log('\n═══════════════════════════════════════════════════════');
  console.log('📈 PACKAGE STATES');
  console.log('═══════════════════════════════════════════════════════');
  Object.entries(storageStats.stateCount).forEach(([state, count]) => {
    console.log(`${state.padEnd(20)} ${count.toLocaleString()}`);
  });

  const behind = registryStatus.update_seq - localState.last_sequence;
  if (behind > 0) {
    console.log('\n⚠️  Local index is behind by %d sequences', behind);
    console.log('Run: npm run sync');
  } else {
    console.log('\n✓ Local index is up to date');
  }
  console.log('═══════════════════════════════════════════════════════\n');
}

async function main() {
  const program = new Command();
  
  program
    .name('npm-registry-indexer')
    .description('Production-grade npm registry indexer')
    .version('2.0.0')
    .option('--index', 'Full re-index from scratch')
    .option('--sync', 'Incremental sync (default behavior)')
    .option('--enrich', 'Enrich package metadata')
    .option('--export', 'Export to CSV')
    .option('--status', 'Show registry and local status')
    .option('--output <file>', 'CSV output file', './data/packages.csv')
    .option('--state <state>', 'Filter by package state')
    .option('--published-after <date>', 'Filter packages published after date')
    .option('--published-before <date>', 'Filter packages published before date')
    .option('--min-size <bytes>', 'Minimum package size', parseInt)
    .option('--max-size <bytes>', 'Maximum package size', parseInt)
    .option('--min-deps <count>', 'Minimum dependencies', parseInt)
    .option('--max-deps <count>', 'Maximum dependencies', parseInt)
    .option('--concurrency <n>', 'Enrichment concurrency', parseInt, ENRICH_CONCURRENCY);

  program.parse();
  const opts = program.opts();

  const storage = new ShardedStorage();
  
  try {
    if (opts.status) {
      await showStatus(storage);
      return;
    }

    const indexer = new RegistryIndexer(storage);
    const enricher = new MetadataEnricher(storage, opts.concurrency);
    const exporter = new CSVExporter(storage);

    if (opts.index) {
      await indexer.sync({ fullIndex: true });
    } else if (opts.sync || (!opts.enrich && !opts.export)) {
      await indexer.sync({ fullIndex: false });
    }

    if (opts.enrich) {
      await enricher.enrichAll();
    }

    if (opts.export) {
      const filters = {};
      if (opts.state) filters.state = opts.state;
      if (opts.publishedAfter) filters.publishedAfter = opts.publishedAfter;
      if (opts.publishedBefore) filters.publishedBefore = opts.publishedBefore;
      if (opts.minSize) filters.minSize = opts.minSize;
      if (opts.maxSize) filters.maxSize = opts.maxSize;
      if (opts.minDeps) filters.minDependencies = opts.minDeps;
      if (opts.maxDeps) filters.maxDependencies = opts.maxDeps;

      await exporter.export({ filters, output: opts.output });
    }

    log.info('Done', '✅ All operations complete');
  } catch (error) {
    log.error('Error', error.message);
    console.error(error);
    process.exit(1);
  }
}

main();

export { RegistryIndexer, MetadataEnricher, CSVExporter };
