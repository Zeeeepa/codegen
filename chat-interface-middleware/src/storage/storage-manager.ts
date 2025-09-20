import { promises as fs } from 'fs';
import { join, dirname } from 'path';
import { createHash } from 'crypto';
import { Logger } from '../../utils/logger.js';

export interface StorageOptions {
  baseDir: string;
  enableEncryption?: boolean;
  encryptionKey?: string;
  maxFileSize?: number;
  enableCompression?: boolean;
}

export interface StorageMetadata {
  id: string;
  originalName: string;
  size: number;
  type: string;
  createdAt: Date;
  updatedAt: Date;
  checksum: string;
  encrypted: boolean;
  compressed: boolean;
}

export class StorageManager {
  private logger: Logger;
  private metadataCache: Map<string, StorageMetadata> = new Map();

  constructor(private options: StorageOptions) {
    this.logger = new Logger('StorageManager');
    this.ensureBaseDirectory();
  }

  /**
   * Save data to storage
   */
  async save(
    key: string, 
    data: any, 
    options?: { 
      type?: string; 
      encrypt?: boolean;
      compress?: boolean;
    }
  ): Promise<string> {
    try {
      const storageId = this.generateStorageId(key);
      const filePath = this.getFilePath(storageId);
      
      // Ensure directory exists
      await fs.mkdir(dirname(filePath), { recursive: true });

      // Serialize data
      let content = this.serializeData(data);

      // Apply compression if enabled
      if (options?.compress || this.options.enableCompression) {
        content = await this.compress(content);
      }

      // Apply encryption if enabled
      if (options?.encrypt || this.options.enableEncryption) {
        content = await this.encrypt(content);
      }

      // Check file size limit
      if (this.options.maxFileSize && content.length > this.options.maxFileSize) {
        throw new Error(`Data exceeds maximum file size: ${this.options.maxFileSize}`);
      }

      // Write to file
      await fs.writeFile(filePath, content);

      // Create metadata
      const metadata: StorageMetadata = {
        id: storageId,
        originalName: key,
        size: content.length,
        type: options?.type || 'application/json',
        createdAt: new Date(),
        updatedAt: new Date(),
        checksum: this.calculateChecksum(content),
        encrypted: options?.encrypt || this.options.enableEncryption || false,
        compressed: options?.compress || this.options.enableCompression || false,
      };

      // Save metadata
      await this.saveMetadata(storageId, metadata);
      this.metadataCache.set(storageId, metadata);

      this.logger.debug(`Saved data to storage: ${key} -> ${storageId}`);
      return storageId;
    } catch (error) {
      this.logger.error(`Failed to save data for key ${key}:`, error);
      throw error;
    }
  }

  /**
   * Load data from storage
   */
  async load<T = any>(keyOrId: string): Promise<T | null> {
    try {
      const storageId = keyOrId.includes('_') ? keyOrId : this.generateStorageId(keyOrId);
      const filePath = this.getFilePath(storageId);

      // Check if file exists
      try {
        await fs.access(filePath);
      } catch {
        this.logger.debug(`File not found: ${keyOrId}`);
        return null;
      }

      // Load metadata
      const metadata = await this.loadMetadata(storageId);
      if (!metadata) {
        this.logger.warn(`Metadata not found for: ${keyOrId}`);
        return null;
      }

      // Read file
      let content = await fs.readFile(filePath);

      // Verify checksum
      const currentChecksum = this.calculateChecksum(content);
      if (currentChecksum !== metadata.checksum) {
        this.logger.error(`Checksum mismatch for: ${keyOrId}`);
        throw new Error('Data integrity check failed');
      }

      // Apply decryption if needed
      if (metadata.encrypted) {
        content = await this.decrypt(content);
      }

      // Apply decompression if needed
      if (metadata.compressed) {
        content = await this.decompress(content);
      }

      // Deserialize data
      const data = this.deserializeData(content.toString());

      this.logger.debug(`Loaded data from storage: ${keyOrId}`);
      return data;
    } catch (error) {
      this.logger.error(`Failed to load data for key ${keyOrId}:`, error);
      throw error;
    }
  }

  /**
   * Check if data exists
   */
  async exists(keyOrId: string): Promise<boolean> {
    const storageId = keyOrId.includes('_') ? keyOrId : this.generateStorageId(keyOrId);
    const filePath = this.getFilePath(storageId);
    
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Delete data from storage
   */
  async delete(keyOrId: string): Promise<boolean> {
    try {
      const storageId = keyOrId.includes('_') ? keyOrId : this.generateStorageId(keyOrId);
      const filePath = this.getFilePath(storageId);
      const metadataPath = this.getMetadataPath(storageId);

      // Delete main file
      try {
        await fs.unlink(filePath);
      } catch (error) {
        this.logger.debug(`Main file not found for deletion: ${keyOrId}`);
      }

      // Delete metadata file
      try {
        await fs.unlink(metadataPath);
      } catch (error) {
        this.logger.debug(`Metadata file not found for deletion: ${keyOrId}`);
      }

      // Remove from cache
      this.metadataCache.delete(storageId);

      this.logger.debug(`Deleted data from storage: ${keyOrId}`);
      return true;
    } catch (error) {
      this.logger.error(`Failed to delete data for key ${keyOrId}:`, error);
      return false;
    }
  }

  /**
   * List all stored items
   */
  async list(pattern?: string): Promise<StorageMetadata[]> {
    try {
      const metadataDir = join(this.options.baseDir, 'metadata');
      
      try {
        const files = await fs.readdir(metadataDir);
        const metadataFiles = files.filter(file => file.endsWith('.json'));
        
        const items: StorageMetadata[] = [];
        
        for (const file of metadataFiles) {
          const storageId = file.replace('.json', '');
          const metadata = await this.loadMetadata(storageId);
          
          if (metadata && (!pattern || metadata.originalName.includes(pattern))) {
            items.push(metadata);
          }
        }
        
        return items.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
      } catch (error) {
        return [];
      }
    } catch (error) {
      this.logger.error('Failed to list storage items:', error);
      return [];
    }
  }

  /**
   * Get storage statistics
   */
  async getStats(): Promise<{
    totalItems: number;
    totalSize: number;
    oldestItem: Date | null;
    newestItem: Date | null;
  }> {
    const items = await this.list();
    
    const totalSize = items.reduce((sum, item) => sum + item.size, 0);
    const dates = items.map(item => item.createdAt).sort((a, b) => a.getTime() - b.getTime());
    
    return {
      totalItems: items.length,
      totalSize,
      oldestItem: dates.length > 0 ? dates[0] : null,
      newestItem: dates.length > 0 ? dates[dates.length - 1] : null,
    };
  }

  /**
   * Clean up old files
   */
  async cleanup(maxAge?: number, maxItems?: number): Promise<number> {
    const items = await this.list();
    let deletedCount = 0;

    // Delete by age
    if (maxAge) {
      const cutoffDate = new Date(Date.now() - maxAge);
      const oldItems = items.filter(item => item.createdAt < cutoffDate);
      
      for (const item of oldItems) {
        await this.delete(item.id);
        deletedCount++;
      }
    }

    // Delete by count
    if (maxItems && items.length > maxItems) {
      const sortedItems = items.sort((a, b) => a.createdAt.getTime() - b.createdAt.getTime());
      const itemsToDelete = sortedItems.slice(0, sortedItems.length - maxItems);
      
      for (const item of itemsToDelete) {
        await this.delete(item.id);
        deletedCount++;
      }
    }

    this.logger.info(`Cleaned up ${deletedCount} storage items`);
    return deletedCount;
  }

  /**
   * Save cookies specifically
   */
  async saveCookies(interfaceName: string, cookies: any[]): Promise<string> {
    return await this.save(`cookies/${interfaceName}`, cookies, { type: 'application/json' });
  }

  /**
   * Load cookies specifically
   */
  async loadCookies(interfaceName: string): Promise<any[] | null> {
    return await this.load(`cookies/${interfaceName}`);
  }

  /**
   * Save screenshot
   */
  async saveScreenshot(
    interfaceName: string, 
    screenshot: Buffer | string,
    filename?: string
  ): Promise<string> {
    const key = `screenshots/${interfaceName}/${filename || Date.now()}`;
    return await this.save(key, screenshot, { type: 'image/png' });
  }

  /**
   * Save snapshot (state + screenshot)
   */
  async saveSnapshot(
    interfaceName: string,
    snapshot: {
      screenshot?: Buffer | string;
      cookies?: any[];
      localStorage?: any;
      sessionStorage?: any;
      url?: string;
      timestamp?: string;
    },
    name?: string
  ): Promise<string> {
    const key = `snapshots/${interfaceName}/${name || Date.now()}`;
    const snapshotData = {
      ...snapshot,
      timestamp: snapshot.timestamp || new Date().toISOString(),
    };
    
    return await this.save(key, snapshotData, { type: 'application/json' });
  }

  /**
   * Load snapshot
   */
  async loadSnapshot(interfaceName: string, name?: string): Promise<any | null> {
    if (name) {
      return await this.load(`snapshots/${interfaceName}/${name}`);
    }
    
    // Load the most recent snapshot
    const items = await this.list(`snapshots/${interfaceName}`);
    if (items.length === 0) return null;
    
    const mostRecent = items.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime())[0];
    return await this.load(mostRecent.id);
  }

  // Private helper methods

  private async ensureBaseDirectory(): Promise<void> {
    try {
      await fs.mkdir(this.options.baseDir, { recursive: true });
      await fs.mkdir(join(this.options.baseDir, 'metadata'), { recursive: true });
    } catch (error) {
      this.logger.error('Failed to create base directory:', error);
      throw error;
    }
  }

  private generateStorageId(key: string): string {
    const hash = createHash('sha256').update(key).digest('hex');
    return `${Date.now()}_${hash.substring(0, 16)}`;
  }

  private getFilePath(storageId: string): string {
    return join(this.options.baseDir, 'data', `${storageId}.bin`);
  }

  private getMetadataPath(storageId: string): string {
    return join(this.options.baseDir, 'metadata', `${storageId}.json`);
  }

  private serializeData(data: any): Buffer {
    if (Buffer.isBuffer(data)) {
      return data;
    }
    return Buffer.from(JSON.stringify(data), 'utf8');
  }

  private deserializeData(content: string): any {
    try {
      return JSON.parse(content);
    } catch {
      return content;
    }
  }

  private calculateChecksum(content: Buffer): string {
    return createHash('sha256').update(content).digest('hex');
  }

  private async saveMetadata(storageId: string, metadata: StorageMetadata): Promise<void> {
    const metadataPath = this.getMetadataPath(storageId);
    await fs.mkdir(dirname(metadataPath), { recursive: true });
    await fs.writeFile(metadataPath, JSON.stringify(metadata, null, 2));
  }

  private async loadMetadata(storageId: string): Promise<StorageMetadata | null> {
    try {
      // Check cache first
      if (this.metadataCache.has(storageId)) {
        return this.metadataCache.get(storageId)!;
      }

      const metadataPath = this.getMetadataPath(storageId);
      const content = await fs.readFile(metadataPath, 'utf8');
      const metadata: StorageMetadata = JSON.parse(content);
      
      // Convert date strings back to Date objects
      metadata.createdAt = new Date(metadata.createdAt);
      metadata.updatedAt = new Date(metadata.updatedAt);
      
      // Cache for future use
      this.metadataCache.set(storageId, metadata);
      
      return metadata;
    } catch {
      return null;
    }
  }

  private async compress(data: Buffer): Promise<Buffer> {
    // Implement compression (zlib, gzip, etc.)
    // For now, return as-is
    return data;
  }

  private async decompress(data: Buffer): Promise<Buffer> {
    // Implement decompression
    // For now, return as-is
    return data;
  }

  private async encrypt(data: Buffer): Promise<Buffer> {
    // Implement encryption
    // For now, return as-is
    return data;
  }

  private async decrypt(data: Buffer): Promise<Buffer> {
    // Implement decryption
    // For now, return as-is
    return data;
  }
}