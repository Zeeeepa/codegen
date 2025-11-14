# NPM Registry Indexer

Production-grade npm registry indexer with CNPM mirror support.

## Features

- **Memory-Efficient**: Streams JSONL files line-by-line using `readline`
- **Official npm Library**: Uses `npm-registry-fetch` for robust API calls
- **Intelligent Batching**: Map-based updates for O(1) lookups
- **Atomic Operations**: Safe file writes with temp files
- **Beautiful CLI**: Rich progress tracking with ETA calculations
- **Resume Capability**: Checkpoint saving every 100 batches

## Quick Start

```bash
# Install dependencies
npm install

# Show status
npm run status

# Index packages from registry
npm run index

# Enrich with metadata
npm run enrich

# Export to CSV
npm run export

# Run full workflow
npm run auto
```

## Usage

```bash
# Individual commands
node indexer.js --status                   # Show current status
node indexer.js --index                    # Sync from CNPM registry
node indexer.js --enrich                   # Enrich package metadata
node indexer.js --export                   # Export to CSV
node indexer.js --auto                     # Run full workflow

# With filters
node indexer.js --export --state enriched --published-after 2024-01-01
node indexer.js --export --min-size 1000000 --min-deps 10
```

## Configuration

Set environment variables to customize behavior:

```bash
export NPM_REGISTRY_URL=https://registry.npmmirror.com
export NPM_CHANGES_URL=https://r.cnpmjs.org
export DATA_DIR=./data
export BATCH_SIZE=1000
export ENRICH_CONCURRENCY=20
export REQUEST_TIMEOUT=30000
export MAX_RETRIES=3
export LOG_LEVEL=info
```

## Architecture

- **Single File**: 819 lines of production-ready code
- **JSONL Storage**: Efficient line-by-line processing
- **Streaming**: No memory issues even with millions of packages
- **Checkpoints**: Resume from failures automatically

## License

MIT

