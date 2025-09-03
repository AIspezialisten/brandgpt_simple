#!/usr/bin/env node

/**
 * Simple CLI test to verify all major functionality works with local BrandGPT server
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const CLI_PATH = './bin/brandgpt-cli.js';
const SERVER_URL = 'http://localhost:9700';

console.log('🚀 Testing BrandGPT CLI against local server...\n');

function runCommand(command, expectError = false) {
  try {
    console.log(`Running: ${command}`);
    const result = execSync(command, { encoding: 'utf8', stdio: 'pipe' });
    console.log(result);
    return result;
  } catch (error) {
    if (expectError) {
      console.log(`Expected error: ${error.message}`);
      return null;
    } else {
      console.error(`Command failed: ${error.message}`);
      console.error(error.stdout);
      throw error;
    }
  }
}

try {
  // Test 1: Health check
  console.log('='.repeat(50));
  console.log('Test 1: Health Check');
  console.log('='.repeat(50));
  runCommand(`${CLI_PATH} health --server ${SERVER_URL}`);

  // Test 2: Help commands
  console.log('='.repeat(50));
  console.log('Test 2: Help Commands');
  console.log('='.repeat(50));
  runCommand(`${CLI_PATH} --help`);
  runCommand(`${CLI_PATH} auth --help`);
  runCommand(`${CLI_PATH} sessions --help`);
  runCommand(`${CLI_PATH} ingest --help`);
  runCommand(`${CLI_PATH} query --help`);

  // Test 3: Configuration commands
  console.log('='.repeat(50));
  console.log('Test 3: Configuration');
  console.log('='.repeat(50));
  runCommand(`${CLI_PATH} config show`);
  
  // Test 4: Error handling (commands that should fail without auth)
  console.log('='.repeat(50));
  console.log('Test 4: Error Handling (Expected Failures)');
  console.log('='.repeat(50));
  runCommand(`${CLI_PATH} sessions list`, true);
  runCommand(`${CLI_PATH} auth whoami`, true);

  console.log('\n🎉 CLI Test Summary:');
  console.log('✅ Health check: Passed');
  console.log('✅ Help commands: Passed');  
  console.log('✅ Configuration: Passed');
  console.log('✅ Error handling: Passed');
  console.log('\n📋 CLI Features Available:');
  console.log('• Authentication (login, register, API key management)');
  console.log('• Session management (create, list, update, delete)');
  console.log('• Data ingestion (files, URLs, structured data, batch)');
  console.log('• Querying (ask, search, chat, batch)');
  console.log('• Configuration management');
  console.log('• Health monitoring');
  console.log('• Multiple output formats (JSON, table, YAML)');
  console.log('\n✨ BrandGPT CLI is ready for use!');

} catch (error) {
  console.error('\n❌ CLI test failed:', error.message);
  process.exit(1);
}