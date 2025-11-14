/**
 * Sharded File Storage System
 * 
 * Stores packages in sharded directories to avoid O(n²) rewrites.
 * Structure: data/pkgs/<shard>/<sanitized-name>.json
 * 
 * Sharding strategy: First 2 chars of normalized package name
 */

import fs from 'fs/promises';
import { createReadStream } from 'fs';
import path from 'path';
import { pipeline } from 'stream/promises';
import { Transform } from 'stream';

const DATA_DIR = './data';
const PKGS_DIR = path.join(DATA_DIR, 'pkgs');
const CHECKPOINT_FILE = path.join(DATA_DIR, 'checkpoint.json');

export class ShardedStorage {
  constructor(dataDir = DATA_DIR) {
    this.dataDir = dataDir;
    this.pkgsDir = path.join(dataDir, 'pkgs');
    this.checkpointFile = path.join(dataDir, 'checkpoint.json');
  }

  /**
   * Sanitize package name for filesystem
   */
  sanitizeName(name) {
    return name
      .replace(/@/g, '__at__')
      .replace(/\//g, '__slash__')
      .replace(/\\/g, '__bslash__')
      .replace(/:/g, '__colon__');
  }

  /**
   * Desanitize package name from filesystem
   */
  desanitizeName(sanitized) {
    return sanitized
      .replace(/__at__/g, '@')
      .replace(/__slash__/g, '/')
      .replace(/__bslash__/g, '\\')
      .replace(/__colon__/g, ':');
  }

  /**
   * Get shard key from package name (first 2 chars after normalization)
   */
  getShardKey(name) {
    const normalized = name.toLowerCase().replace(/^@/, '');
    return normalized.substring(0, 2) || 'default';
  }

  /**
   * Get path for a package file
   */
  getPackagePath(name) {
    const shard = this.getShardKey(name);
    const sanitized = this.sanitizeName(name);
    return path.join(this.pkgsDir, shard, `${sanitized}.json`);
  }

  /**
   * Ensure shard directory exists
   */
  async ensureShardDir(shard) {
    const shardPath = path.join(this.pkgsDir, shard);
    await fs.mkdir(shardPath, { recursive: true });
  }

  /**
   * Write a package to storage
   */
  async writePackage(name, data) {
    const shard = this.getShardKey(name);
    await this.ensureShardDir(shard);
    const pkgPath = this.getPackagePath(name);
    await fs.writeFile(pkgPath, JSON.stringify(data, null, 2));
  }

  /**
   * Read a package from storage
   */
  async readPackage(name) {
    try {
      const pkgPath = this.getPackagePath(name);
      const data = await fs.readFile(pkgPath, 'utf8');
      return JSON.parse(data);
    } catch (error) {
      if (error.code === 'ENOENT') return null;
      throw error;
    }
  }

  /**
   * Check if package exists
   */
  async hasPackage(name) {
    try {
      const pkgPath = this.getPackagePath(name);
      await fs.access(pkgPath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Update package metadata (merge with existing)
   */
  async updatePackage(name, updates) {
    const existing = await this.readPackage(name) || { name };
    const merged = { ...existing, ...updates };
    await this.writePackage(name, merged);
    return merged;
  }

  /**
   * Get all shard directories
   */
  async getShards() {
    try {
      await fs.mkdir(this.pkgsDir, { recursive: true });
      const entries = await fs.readdir(this.pkgsDir, { withFileTypes: true });
      return entries.filter(e => e.isDirectory()).map(e => e.name);
    } catch {
      return [];
    }
  }

  /**
   * Stream all packages (async generator)
   */
  async *packagesStream(filter = null) {
    const shards = await this.getShards();
    
    for (const shard of shards) {
      const shardPath = path.join(this.pkgsDir, shard);
      const files = await fs.readdir(shardPath);
      
      for (const file of files) {
        if (!file.endsWith('.json')) continue;
        
        try {
          const filePath = path.join(shardPath, file);
          const data = await fs.readFile(filePath, 'utf8');
          const pkg = JSON.parse(data);
          
          // Apply filter if provided
          if (filter && !filter(pkg)) continue;
          
          yield pkg;
        } catch (error) {
          // Skip corrupted files
          continue;
        }
      }
    }
  }

  /**
   * Count packages by state
   */
  async countByState(state) {
    let count = 0;
    for await (const pkg of this.packagesStream(p => p.state === state)) {
      count++;
    }
    return count;
  }

  /**
   * Get packages by state (with pagination)
   */
  async getPackagesByState(state, limit = 1000, offset = 0) {
    const packages = [];
    let skipped = 0;
    
    for await (const pkg of this.packagesStream(p => p.state === state)) {
      if (skipped < offset) {
        skipped++;
        continue;
      }
      
      packages.push(pkg);
      if (packages.length >= limit) break;
    }
    
    return packages;
  }

  /**
   * Load checkpoint state
   */
  async loadState() {
    try {
      const data = await fs.readFile(this.checkpointFile, 'utf8');
      return JSON.parse(data);
    } catch (error) {
      if (error.code === 'ENOENT') {
        return {
          last_sequence: 0,
          total_packages: 0,
          enriched_packages: 0,
          last_updated: null,
          registry_update_seq: null,
          registry_doc_count: null
        };
      }
      throw error;
    }
  }

  /**
   * Save checkpoint state
   */
  async saveState(state) {
    await fs.mkdir(this.dataDir, { recursive: true });
    await fs.writeFile(this.checkpointFile, JSON.stringify(state, null, 2));
  }

  /**
   * Get storage statistics
   */
  async getStats() {
    const shards = await this.getShards();
    let totalPackages = 0;
    let totalSize = 0;
    let stateCount = {};

    for (const shard of shards) {
      const shardPath = path.join(this.pkgsDir, shard);
      const files = await fs.readdir(shardPath);
      
      for (const file of files) {
        if (!file.endsWith('.json')) continue;
        totalPackages++;
        
        try {
          const filePath = path.join(shardPath, file);
          const stats = await fs.stat(filePath);
          totalSize += stats.size;
          
          const data = await fs.readFile(filePath, 'utf8');
          const pkg = JSON.parse(data);
          const state = pkg.state || 'unknown';
          stateCount[state] = (stateCount[state] || 0) + 1;
        } catch {
          // Skip corrupted files
        }
      }
    }

    return {
      totalPackages,
      totalSize,
      shardCount: shards.length,
      stateCount,
      avgPackageSize: totalPackages > 0 ? Math.round(totalSize / totalPackages) : 0
    };
  }

  /**
   * Migrate from old JSONL format (if exists)
   */
  async migrateFromJSONL(jsonlPath) {
    try {
      const data = await fs.readFile(jsonlPath, 'utf8');
      const lines = data.trim().split('\n');
      let migrated = 0;

      for (const line of lines) {
        try {
          const pkg = JSON.parse(line);
          if (pkg.name) {
            await this.writePackage(pkg.name, pkg);
            migrated++;
          }
        } catch {
          // Skip invalid lines
        }
      }

      return migrated;
    } catch (error) {
      if (error.code === 'ENOENT') return 0;
      throw error;
    }
  }
}

export default ShardedStorage;

