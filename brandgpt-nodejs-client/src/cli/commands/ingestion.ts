import { Command } from 'commander';
import inquirer from 'inquirer';
import ora from 'ora';
import * as fs from 'fs';
import * as path from 'path';
import { BrandGPTClient } from '../../client';
import { ConfigManager } from '../config';
import { Logger, OutputFormatter, validateFile, parseJsonFile, formatBytes } from '../utils';

export function createIngestionCommands(program: Command, configManager: ConfigManager): Command {
  const ingest = program
    .command('ingest')
    .description('Data ingestion commands');

  // Upload file
  ingest
    .command('file <file-path>')
    .description('Upload and process a file')
    .option('-s, --session <session-id>', 'Session ID (required)')
    .option('-g, --group-id <group-id>', 'Group ID for organizing content')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .option('--wait', 'Wait for processing to complete')
    .action(async (filePath, options) => {
      try {
        const config = configManager.load();

        if (!config.baseUrl || !config.apiKey) {
          Logger.error('No authentication found. Please login first.');
          process.exit(1);
        }

        if (!options.session) {
          Logger.error('Session ID is required. Use --session <session-id>');
          process.exit(1);
        }

        // Validate file exists
        validateFile(filePath);
        const stats = fs.statSync(filePath);
        const fileName = path.basename(filePath);

        Logger.info(`Uploading file: ${fileName} (${formatBytes(stats.size)})`);

        const spinner = ora('Uploading file...').start();

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        const fileBuffer = fs.readFileSync(filePath);
        const uploadOptions: any = { groupId: options.groupId };

        const result = await client.ingestion.uploadFile(
          fileBuffer,
          fileName,
          options.session,
          uploadOptions
        );

        spinner.stop();

        Logger.success('File uploaded successfully');

        const output = OutputFormatter.format(result, {
          format: options.format as any,
          pretty: true
        });

        console.log(output);

        if (options.wait) {
          const waitSpinner = ora('Waiting for processing to complete...').start();
          
          // Poll for processing completion
          let attempts = 0;
          const maxAttempts = 30; // 5 minutes max
          
          while (attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
            
            try {
              const documents = await client.documents.listBySession(options.session);
              const doc = documents.find(d => d.id === result.document_id);
              
              if (doc && doc.processed) {
                waitSpinner.stop();
                Logger.success('File processing completed');
                break;
              }
              
              attempts++;
            } catch (error) {
              // Continue waiting on errors
              attempts++;
            }
          }
          
          if (attempts >= maxAttempts) {
            waitSpinner.stop();
            Logger.warn('Timeout waiting for processing. Check status manually.');
          }
        }

      } catch (error: any) {
        Logger.error('Failed to upload file:', error.message);
        process.exit(1);
      }
    });

  // Upload URL
  ingest
    .command('url <url>')
    .description('Scrape and ingest content from a URL')
    .option('-s, --session <session-id>', 'Session ID (required)')
    .option('-g, --group-id <group-id>', 'Group ID for organizing content')
    .option('-d, --depth <depth>', 'Scraping depth (default: 1)', '1')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .option('--wait', 'Wait for processing to complete')
    .action(async (url, options) => {
      try {
        const config = configManager.load();

        if (!config.baseUrl || !config.apiKey) {
          Logger.error('No authentication found. Please login first.');
          process.exit(1);
        }

        if (!options.session) {
          Logger.error('Session ID is required. Use --session <session-id>');
          process.exit(1);
        }

        // Validate URL format
        try {
          new URL(url);
        } catch {
          Logger.error('Invalid URL format');
          process.exit(1);
        }

        const depth = parseInt(options.depth) || 1;
        Logger.info(`Scraping URL: ${url} (depth: ${depth})`);

        const spinner = ora('Scraping URL...').start();

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        const result = await client.ingestion.ingestUrl(url, {
          sessionId: options.session,
          groupId: options.groupId,
          maxDepth: depth
        });

        spinner.stop();

        Logger.success('URL content scraped successfully');

        const output = OutputFormatter.format(result, {
          format: options.format as any,
          pretty: true
        });

        console.log(output);

        if (options.wait) {
          const waitSpinner = ora('Waiting for processing to complete...').start();
          
          // Poll for processing completion
          let attempts = 0;
          const maxAttempts = 60; // 10 minutes max for URL scraping
          
          while (attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
            
            try {
              const documents = await client.documents.listBySession(options.session);
              const doc = documents.find(d => d.id === result.document_id);
              
              if (doc && doc.processed) {
                waitSpinner.stop();
                Logger.success('URL processing completed');
                break;
              }
              
              attempts++;
            } catch (error) {
              // Continue waiting on errors
              attempts++;
            }
          }
          
          if (attempts >= maxAttempts) {
            waitSpinner.stop();
            Logger.warn('Timeout waiting for processing. Check status manually.');
          }
        }

      } catch (error: any) {
        Logger.error('Failed to ingest URL:', error.message);
        process.exit(1);
      }
    });

  // Ingest structured data
  ingest
    .command('data [json-file]')
    .description('Ingest structured JSON data')
    .option('-s, --session <session-id>', 'Session ID (required)')
    .option('-g, --group-id <group-id>', 'Group ID for organizing content')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .option('--stdin', 'Read JSON from stdin')
    .action(async (jsonFile, options) => {
      try {
        const config = configManager.load();

        if (!config.baseUrl || !config.apiKey) {
          Logger.error('No authentication found. Please login first.');
          process.exit(1);
        }

        if (!options.session) {
          Logger.error('Session ID is required. Use --session <session-id>');
          process.exit(1);
        }

        let data: any;

        if (options.stdin) {
          // Read from stdin
          const stdin = process.stdin;
          stdin.setEncoding('utf8');
          
          let input = '';
          for await (const chunk of stdin) {
            input += chunk;
          }
          
          try {
            data = JSON.parse(input);
          } catch (error) {
            Logger.error('Invalid JSON input from stdin');
            process.exit(1);
          }
        } else if (jsonFile) {
          // Read from file
          data = parseJsonFile(jsonFile);
        } else {
          // Interactive input
          const answers = await inquirer.prompt([
            {
              type: 'editor',
              name: 'jsonData',
              message: 'Enter JSON data (this will open your default editor):',
              validate: (input) => {
                try {
                  JSON.parse(input);
                  return true;
                } catch {
                  return 'Please enter valid JSON';
                }
              }
            }
          ]);
          
          data = JSON.parse(answers.jsonData);
        }

        Logger.info('Ingesting structured data...');

        const spinner = ora('Processing structured data...').start();

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        const result = await client.ingestion.ingestStructuredData({
          data,
          sessionId: options.session,
          groupId: options.groupId,
          metadata: {
            source: jsonFile ? path.basename(jsonFile) : 'cli_input',
            ingestion_method: 'cli'
          }
        });

        spinner.stop();

        Logger.success('Structured data ingested successfully');

        const output = OutputFormatter.format(result, {
          format: options.format as any,
          pretty: true
        });

        console.log(output);

      } catch (error: any) {
        Logger.error('Failed to ingest structured data:', error.message);
        process.exit(1);
      }
    });

  // Batch upload files
  ingest
    .command('batch <directory>')
    .description('Upload all files in a directory')
    .option('-s, --session <session-id>', 'Session ID (required)')
    .option('-g, --group-id <group-id>', 'Group ID for organizing content')
    .option('--pattern <pattern>', 'File pattern to match (e.g., "*.pdf")', '*')
    .option('--recursive', 'Process subdirectories recursively')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .action(async (directory, options) => {
      try {
        const config = configManager.load();

        if (!config.baseUrl || !config.apiKey) {
          Logger.error('No authentication found. Please login first.');
          process.exit(1);
        }

        if (!options.session) {
          Logger.error('Session ID is required. Use --session <session-id>');
          process.exit(1);
        }

        if (!fs.existsSync(directory)) {
          Logger.error(`Directory not found: ${directory}`);
          process.exit(1);
        }

        const stats = fs.statSync(directory);
        if (!stats.isDirectory()) {
          Logger.error(`Path is not a directory: ${directory}`);
          process.exit(1);
        }

        // Find files to upload
        const glob = require('glob');
        const pattern = path.join(directory, options.recursive ? '**/' + options.pattern : options.pattern);
        const files = glob.sync(pattern, { nodir: true });

        if (files.length === 0) {
          Logger.info('No files found matching the pattern');
          return;
        }

        Logger.info(`Found ${files.length} files to upload`);

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        const results = [];
        let successful = 0;
        let failed = 0;

        for (const filePath of files) {
          try {
            const fileName = path.basename(filePath);
            const fileStats = fs.statSync(filePath);
            
            console.log(`Uploading: ${fileName} (${formatBytes(fileStats.size)})`);

            const fileBuffer = fs.readFileSync(filePath);
            const uploadOptions: any = { groupId: options.groupId };

            const result = await client.ingestion.uploadFile(
              fileBuffer,
              fileName,
              options.session,
              uploadOptions
            );

            results.push({ file: fileName, result_status: 'success', ...result });
            successful++;
            Logger.success(`✓ ${fileName}`);

          } catch (error: any) {
            results.push({ file: path.basename(filePath), result_status: 'error', error: error.message });
            failed++;
            Logger.error(`✗ ${path.basename(filePath)}: ${error.message}`);
          }
        }

        Logger.info(`\nBatch upload completed: ${successful} successful, ${failed} failed`);

        if (options.format !== 'table') {
          const output = OutputFormatter.format(results, {
            format: options.format as any,
            pretty: true
          });
          console.log(output);
        }

      } catch (error: any) {
        Logger.error('Batch upload failed:', error.message);
        process.exit(1);
      }
    });

  // Check processing status
  ingest
    .command('status <session-id>')
    .description('Check processing status of documents in a session')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .action(async (sessionId, options) => {
      try {
        const config = configManager.load();

        if (!config.baseUrl || !config.apiKey) {
          Logger.error('No authentication found. Please login first.');
          process.exit(1);
        }

        const spinner = ora('Checking processing status...').start();

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        const documents = await client.documents.listBySession(sessionId);
        
        spinner.stop();

        if (documents.length === 0) {
          Logger.info('No documents found in this session');
          return;
        }

        // Add status summary
        const processed = documents.filter(d => d.processed).length;
        const pending = documents.length - processed;

        const statusData = documents.map(doc => ({
          id: doc.id,
          filename: doc.filename || 'Structured Data',
          content_type: doc.content_type,
          processed: doc.processed ? 'Yes' : 'Pending',
          created_at: doc.created_at
        }));

        const output = OutputFormatter.format(statusData, {
          format: options.format as any,
          pretty: true
        });

        console.log(output);
        Logger.info(`Status: ${processed} processed, ${pending} pending`);

      } catch (error: any) {
        Logger.error('Failed to check status:', error.message);
        process.exit(1);
      }
    });

  return ingest;
}