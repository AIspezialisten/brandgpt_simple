import { Command } from 'commander';
import inquirer from 'inquirer';
import ora from 'ora';
import * as fs from 'fs';
import { BrandGPTClient } from '../../client';
import { ConfigManager } from '../config';
import { Logger, OutputFormatter, formatDuration } from '../utils';

export function createQueryCommands(program: Command, configManager: ConfigManager): Command {
  const query = program
    .command('query')
    .alias('q')
    .description('Query and search commands');

  // Interactive query
  query
    .command('ask [question]')
    .description('Ask a question (interactive mode if no question provided)')
    .option('-s, --session <session-id>', 'Session ID (required)')
    .option('-g, --group-id <group-id>', 'Filter by group ID')
    .option('-m, --max-results <number>', 'Maximum number of results (default: 5)')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .option('--sources-only', 'Show only sources without generated answer')
    .option('--no-sources', 'Hide source references')
    .action(async (question, options) => {
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

        let queryText = question;

        if (!queryText) {
          // Interactive mode
          const answers = await inquirer.prompt([
            {
              type: 'input',
              name: 'question',
              message: 'What would you like to ask?',
              validate: (input) => input.trim().length > 0 || 'Question is required'
            }
          ]);
          queryText = answers.question;
        }

        const spinner = ora('Searching for answer...').start();
        const startTime = Date.now();

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        const queryOptions: any = {
          query: queryText,
          sessionId: options.session
        };

        if (options.groupId) {
          queryOptions.groupId = options.groupId;
        }

        if (options.maxResults) {
          queryOptions.maxResults = parseInt(options.maxResults);
        }

        const result = await client.query.query(queryOptions);
        const duration = Date.now() - startTime;

        spinner.stop();

        // Display results
        console.log('\n' + '='.repeat(60));
        console.log('QUERY RESULTS');
        console.log('='.repeat(60));
        console.log(`Query: ${queryText}`);
        console.log(`Session: ${options.session}`);
        console.log(`Response time: ${formatDuration(duration)}`);
        console.log(`Sources found: ${result.sources.length}`);
        console.log('='.repeat(60));

        if (!options.sourcesOnly && result.response) {
          console.log('\nANSWER:');
          console.log('-'.repeat(40));
          console.log(result.response);
        }

        if (!options.noSources && result.sources.length > 0) {
          console.log('\nSOURCES:');
          console.log('-'.repeat(40));

          if (options.format === 'json') {
            const output = OutputFormatter.format(result.sources, {
              format: 'json',
              pretty: true
            });
            console.log(output);
          } else {
            result.sources.forEach((source, index) => {
              console.log(`\n[${index + 1}] Score: ${source.score?.toFixed(3) || 'N/A'}`);
              console.log(`Type: ${source.content_type || 'Unknown'}`);
              if (source.filename) {
                console.log(`File: ${source.filename}`);
              }
              if (source.group_id) {
                console.log(`Group: ${source.group_id}`);
              }
              console.log(`Text: ${source.text}`);
              
              if (source.metadata) {
                console.log(`Metadata: ${JSON.stringify(source.metadata)}`);
              }
            });
          }
        }

        console.log('\n' + '='.repeat(60));

      } catch (error: any) {
        Logger.error('Query failed:', error.message);
        process.exit(1);
      }
    });

  // Batch query from file
  query
    .command('batch <questions-file>')
    .description('Run multiple queries from a file (one per line)')
    .option('-s, --session <session-id>', 'Session ID (required)')
    .option('-g, --group-id <group-id>', 'Filter by group ID')
    .option('-m, --max-results <number>', 'Maximum number of results per query')
    .option('--output <file>', 'Save results to file')
    .option('--format <format>', 'Output format (json, yaml)', 'json')
    .option('--delay <ms>', 'Delay between queries in milliseconds (default: 1000)', '1000')
    .action(async (questionsFile, options) => {
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

        if (!fs.existsSync(questionsFile)) {
          Logger.error(`Questions file not found: ${questionsFile}`);
          process.exit(1);
        }

        const questions = fs.readFileSync(questionsFile, 'utf8')
          .split('\n')
          .map(line => line.trim())
          .filter(line => line.length > 0 && !line.startsWith('#'));

        if (questions.length === 0) {
          Logger.error('No questions found in file');
          process.exit(1);
        }

        Logger.info(`Running ${questions.length} queries...`);

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        const results = [];
        const delay = parseInt(options.delay);

        for (let i = 0; i < questions.length; i++) {
          const question = questions[i];
          const spinner = ora(`Query ${i + 1}/${questions.length}: ${question.substring(0, 50)}...`).start();
          const startTime = Date.now();

          try {
            const queryOptions: any = {
              query: question,
              sessionId: options.session
            };

            if (options.groupId) {
              queryOptions.groupId = options.groupId;
            }

            if (options.maxResults) {
              queryOptions.maxResults = parseInt(options.maxResults);
            }

            const result = await client.query.query(queryOptions);
            const duration = Date.now() - startTime;

            results.push({
              question,
              response: result.response,
              sources: result.sources,
              duration,
              timestamp: new Date().toISOString()
            });

            spinner.stop();
            Logger.success(`✓ Query ${i + 1} completed (${formatDuration(duration)})`);

            // Delay before next query (except for last one)
            if (i < questions.length - 1) {
              await new Promise(resolve => setTimeout(resolve, delay));
            }

          } catch (error: any) {
            spinner.stop();
            Logger.error(`✗ Query ${i + 1} failed: ${error.message}`);
            
            results.push({
              question,
              error: error.message,
              timestamp: new Date().toISOString()
            });
          }
        }

        // Output results
        const output = OutputFormatter.format(results, {
          format: options.format as any,
          pretty: true
        });

        if (options.output) {
          fs.writeFileSync(options.output, output);
          Logger.success(`Results saved to: ${options.output}`);
        } else {
          console.log(output);
        }

        const successful = results.filter(r => !r.error).length;
        const failed = results.filter(r => r.error).length;
        Logger.info(`Batch query completed: ${successful} successful, ${failed} failed`);

      } catch (error: any) {
        Logger.error('Batch query failed:', error.message);
        process.exit(1);
      }
    });

  // Search for specific content
  query
    .command('search <terms>')
    .description('Search for specific terms in documents')
    .option('-s, --session <session-id>', 'Session ID (required)')
    .option('-g, --group-id <group-id>', 'Filter by group ID')
    .option('-m, --max-results <number>', 'Maximum number of results (default: 10)')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .option('--threshold <score>', 'Minimum similarity score (0-1)', '0.7')
    .action(async (searchTerms, options) => {
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

        const spinner = ora(`Searching for: ${searchTerms}`).start();

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        const queryOptions: any = {
          query: searchTerms,
          sessionId: options.session,
          maxResults: parseInt(options.maxResults) || 10
        };

        if (options.groupId) {
          queryOptions.groupId = options.groupId;
        }

        const result = await client.query.query(queryOptions);
        
        // Filter by threshold if specified
        const threshold = parseFloat(options.threshold);
        let sources = result.sources;
        if (threshold > 0) {
          sources = sources.filter(source => (source.score || 0) >= threshold);
        }

        spinner.stop();

        if (sources.length === 0) {
          Logger.info('No matching content found');
          return;
        }

        Logger.success(`Found ${sources.length} matching results`);

        const output = OutputFormatter.format(sources.map(source => ({
          score: source.score?.toFixed(3) || 'N/A',
          content_type: source.content_type,
          filename: source.filename || 'Structured Data',
          group_id: source.group_id || 'None',
          preview: source.text.substring(0, 200) + (source.text.length > 200 ? '...' : ''),
          full_text: options.format === 'json' ? source.text : undefined
        })), {
          format: options.format as any,
          pretty: true
        });

        console.log(output);

      } catch (error: any) {
        Logger.error('Search failed:', error.message);
        process.exit(1);
      }
    });

  // Interactive chat mode
  query
    .command('chat')
    .description('Start interactive chat session')
    .option('-s, --session <session-id>', 'Session ID (required)')
    .option('-g, --group-id <group-id>', 'Filter by group ID')
    .option('-m, --max-results <number>', 'Maximum number of results per query')
    .action(async (options) => {
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

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        console.log('\n🤖 Interactive Chat Mode');
        console.log('Type "exit", "quit", or press Ctrl+C to end the session');
        console.log('Type "help" for available commands');
        console.log('='.repeat(50));

        while (true) {
          const { question } = await inquirer.prompt([
            {
              type: 'input',
              name: 'question',
              message: '❓ Ask a question:',
              validate: (input) => input.trim().length > 0 || 'Question is required'
            }
          ]);

          const trimmedQuestion = question.trim().toLowerCase();

          if (trimmedQuestion === 'exit' || trimmedQuestion === 'quit') {
            Logger.info('Goodbye!');
            break;
          }

          if (trimmedQuestion === 'help') {
            console.log('\nAvailable commands:');
            console.log('  exit, quit - End the chat session');
            console.log('  help - Show this help message');
            console.log('  Any other input will be treated as a question\n');
            continue;
          }

          const spinner = ora('Thinking...').start();
          const startTime = Date.now();

          try {
            const queryOptions: any = {
              query: question,
              sessionId: options.session
            };

            if (options.groupId) {
              queryOptions.groupId = options.groupId;
            }

            if (options.maxResults) {
              queryOptions.maxResults = parseInt(options.maxResults);
            }

            const result = await client.query.query(queryOptions);
            const duration = Date.now() - startTime;

            spinner.stop();

            console.log(`\n🤖 Answer (${formatDuration(duration)}, ${result.sources.length} sources):`);
            console.log('-'.repeat(40));
            console.log(result.response || 'No response generated');

            if (result.sources.length > 0) {
              console.log(`\n📚 Top sources:`);
              result.sources.slice(0, 3).forEach((source, index) => {
                console.log(`  ${index + 1}. ${source.filename || 'Structured Data'} (${source.score?.toFixed(3) || 'N/A'})`);
              });
            }
            
            console.log('');

          } catch (error: any) {
            spinner.stop();
            Logger.error('Query failed:', error.message);
            console.log('');
          }
        }

      } catch (error: any) {
        if (error.message.includes('User force closed')) {
          Logger.info('\nGoodbye!');
          process.exit(0);
        }
        Logger.error('Chat session failed:', error.message);
        process.exit(1);
      }
    });

  return query;
}