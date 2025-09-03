#!/usr/bin/env node

import { Command } from 'commander';
import { ConfigManager } from './config';
import { Logger } from './utils';
import { createAuthCommands } from './commands/auth';
import { createSessionCommands } from './commands/sessions';
import { createIngestionCommands } from './commands/ingestion';
import { createQueryCommands } from './commands/query';

const packageJson = require('../../package.json');

export function createCLI(): Command {
  const program = new Command();
  const configManager = new ConfigManager();

  program
    .name('brandgpt')
    .description('BrandGPT CLI - Interact with BrandGPT RAG API')
    .version(packageJson.version);

  // Global options
  program
    .option('--config-path', 'Show config file path')
    .option('--debug', 'Enable debug output')
    .hook('preAction', (thisCommand) => {
      const opts = thisCommand.opts();
      
      if (opts.debug) {
        process.env.DEBUG = '1';
      }
      
      if (opts.configPath) {
        console.log(`Config file: ${configManager.getConfigPath()}`);
        process.exit(0);
      }
    });

  // Register command groups
  createAuthCommands(program, configManager);
  createSessionCommands(program, configManager);
  createIngestionCommands(program, configManager);
  createQueryCommands(program, configManager);

  // Config commands
  const config = program
    .command('config')
    .description('Configuration management');

  config
    .command('show')
    .description('Show current configuration')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .action((options) => {
      const { OutputFormatter } = require('./utils');
      const currentConfig = configManager.load();
      
      // Mask API key for security
      const displayConfig = { ...currentConfig };
      if (displayConfig.apiKey) {
        displayConfig.apiKey = displayConfig.apiKey.substring(0, 8) + '...';
      }
      
      const output = OutputFormatter.format(displayConfig, {
        format: options.format as any,
        pretty: true
      });
      
      console.log(output);
    });

  config
    .command('set <key> <value>')
    .description('Set a configuration value')
    .action((key, value) => {
      try {
        const validKeys = ['baseUrl', 'defaultTimeout', 'outputFormat'];
        
        if (!validKeys.includes(key)) {
          Logger.error(`Invalid config key. Valid keys: ${validKeys.join(', ')}`);
          process.exit(1);
        }
        
        const updates: any = {};
        
        if (key === 'defaultTimeout') {
          updates[key] = parseInt(value);
        } else {
          updates[key] = value;
        }
        
        configManager.update(updates);
        Logger.success(`Configuration updated: ${key} = ${value}`);
      } catch (error: any) {
        Logger.error('Failed to update configuration:', error.message);
        process.exit(1);
      }
    });

  config
    .command('clear')
    .description('Clear all configuration')
    .action(async () => {
      const inquirer = require('inquirer');
      
      const { confirm } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'confirm',
          message: 'Are you sure you want to clear all configuration?',
          default: false
        }
      ]);

      if (confirm) {
        configManager.clear();
        Logger.success('Configuration cleared');
      } else {
        Logger.info('Configuration clear cancelled');
      }
    });

  // Health check command
  program
    .command('health')
    .description('Check API server health')
    .option('-s, --server <url>', 'Server URL to check')
    .action(async (options) => {
      const ora = require('ora');
      const { BrandGPTClient } = require('../client');
      
      try {
        const config = configManager.load();
        const serverUrl = options.server || config.baseUrl;

        if (!serverUrl) {
          Logger.error('No server URL configured. Use --server option or login first.');
          process.exit(1);
        }

        const spinner = ora(`Checking health of ${serverUrl}`).start();

        const client = new BrandGPTClient({ baseUrl: serverUrl });
        const health = await client.health();

        spinner.stop();

        Logger.success('Server is healthy!');
        console.log(JSON.stringify(health, null, 2));

      } catch (error: any) {
        Logger.error('Health check failed:', error.message);
        process.exit(1);
      }
    });

  // Help command enhancement
  program.on('--help', () => {
    console.log('');
    console.log('Examples:');
    console.log('  $ brandgpt auth login');
    console.log('  $ brandgpt sessions create --name "My Session"');
    console.log('  $ brandgpt ingest file document.pdf --session <id>');
    console.log('  $ brandgpt query ask "What is this document about?" --session <id>');
    console.log('  $ brandgpt query chat --session <id>');
    console.log('');
    console.log('For more information on a specific command:');
    console.log('  $ brandgpt <command> --help');
    console.log('');
    console.log('Configuration:');
    console.log(`  Config file: ${configManager.getConfigPath()}`);
    console.log('');
  });

  // Error handling
  program.exitOverride();

  return program;
}

// CLI entry point
export function runCLI(): void {
  const program = createCLI();
  
  try {
    program.parse();
  } catch (error: any) {
    if (error.code === 'commander.help' || error.code === 'commander.helpDisplayed') {
      process.exit(0);
    } else if (error.code === 'commander.version') {
      process.exit(0);
    } else {
      Logger.error('CLI Error:', error.message);
      process.exit(1);
    }
  }
}

// Run CLI if this file is executed directly
if (require.main === module) {
  runCLI();
}