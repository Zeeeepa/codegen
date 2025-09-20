#!/usr/bin/env node

import { readFileSync, writeFileSync, readdirSync, statSync } from 'fs';
import { join, dirname } from 'path';

function getAllTsFiles(dir, files = []) {
  const items = readdirSync(dir);
  
  for (const item of items) {
    const fullPath = join(dir, item);
    const stat = statSync(fullPath);
    
    if (stat.isDirectory() && !item.includes('node_modules') && !item.includes('.git')) {
      getAllTsFiles(fullPath, files);
    } else if (item.endsWith('.ts') || item.endsWith('.tsx')) {
      files.push(fullPath);
    }
  }
  
  return files;
}

function fixImportsInFile(filePath) {
  let content = readFileSync(filePath, 'utf8');
  let changed = false;

  // Replace @/ imports with relative paths
  const importRegex = /from ['""]@\/([^'""\s]+)['""];?/g;
  
  content = content.replace(importRegex, (match, importPath) => {
    // Calculate relative path
    const fileDir = dirname(filePath);
    const srcDir = join(process.cwd(), 'src');
    const relativeToSrc = fileDir.replace(srcDir, '').replace(/^\//, '');
    
    let relativePath = '';
    if (relativeToSrc) {
      const levels = relativeToSrc.split('/').length;
      relativePath = '../'.repeat(levels);
    } else {
      relativePath = './';
    }
    
    const newImport = `from '${relativePath}${importPath}';`;
    changed = true;
    return newImport;
  });

  if (changed) {
    writeFileSync(filePath, content);
    console.log(`Fixed imports in: ${filePath}`);
  }
}

// Fix all TypeScript files
const tsFiles = getAllTsFiles('./src');
tsFiles.forEach(fixImportsInFile);

console.log(`Processed ${tsFiles.length} TypeScript files`);