#!/usr/bin/env node

// Check if we're in development or if TypeScript files exist
const fs = require('fs');
const path = require('path');

const distPath = path.join(__dirname, '..', 'dist', 'cli', 'index.js');
const srcPath = path.join(__dirname, '..', 'src', 'cli', 'index.ts');

if (fs.existsSync(distPath)) {
  // Use compiled version
  const { runCLI } = require(distPath);
  runCLI();
} else if (fs.existsSync(srcPath)) {
  // Development mode - use ts-node if available
  try {
    require('ts-node/register');
    const { runCLI } = require(srcPath);
    runCLI();
  } catch (error) {
    console.error('ERROR: TypeScript source found but ts-node is not available.');
    console.error('Please run "npm run build" first or install ts-node for development.');
    console.error('');
    console.error('To install ts-node: npm install -g ts-node typescript');
    process.exit(1);
  }
} else {
  console.error('ERROR: CLI entry point not found.');
  console.error('Please run "npm run build" first.');
  process.exit(1);
}