import { Command } from 'commander';
import inquirer from 'inquirer';
import ora from 'ora';
import { BrandGPTClient } from '../../client';
import { ConfigManager } from '../config';
import { Logger, OutputFormatter, validateFile, parseJsonFile } from '../utils';

export function createSessionCommands(program: Command, configManager: ConfigManager): Command {
  const sessions = program
    .command('sessions')
    .alias('session')
    .description('Session management commands');

  // List sessions
  sessions
    .command('list')
    .alias('ls')
    .description('List all sessions')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .option('--limit <number>', 'Limit number of sessions to show')
    .action(async (options) => {
      try {
        const config = configManager.load();

        if (!config.baseUrl || !config.apiKey) {
          Logger.error('No authentication found. Please login first.');
          process.exit(1);
        }

        const spinner = ora('Loading sessions...').start();

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        const allSessions = await client.sessions.list();
        let sessions = allSessions;
        
        if (options.limit) {
          const limit = parseInt(options.limit);
          sessions = sessions.slice(0, limit);
        }

        spinner.stop();

        if (sessions.length === 0) {
          Logger.info('No sessions found');
          return;
        }

        const output = OutputFormatter.format(sessions, {
          format: options.format as any,
          pretty: true
        });

        console.log(output);
        Logger.info(`Showing ${sessions.length} of ${allSessions.length} sessions`);

      } catch (error: any) {
        Logger.error('Failed to list sessions:', error.message);
        process.exit(1);
      }
    });

  // Create session
  sessions
    .command('create')
    .description('Create a new session')
    .option('-n, --name <name>', 'Session name')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .action(async (options) => {
      try {
        const config = configManager.load();

        if (!config.baseUrl || !config.apiKey) {
          Logger.error('No authentication found. Please login first.');
          process.exit(1);
        }

        let sessionName = options.name;

        if (!sessionName) {
          const answers = await inquirer.prompt([
            {
              type: 'input',
              name: 'name',
              message: 'Session name:',
              validate: (input) => input.trim().length > 0 || 'Session name is required'
            }
          ]);
          sessionName = answers.name;
        }

        const spinner = ora('Creating session...').start();

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        const session = await client.sessions.create({ name: sessionName });
        
        spinner.stop();

        Logger.success(`Session created: ${session.id}`);

        const output = OutputFormatter.format(session, {
          format: options.format as any,
          pretty: true
        });

        console.log(output);

      } catch (error: any) {
        Logger.error('Failed to create session:', error.message);
        process.exit(1);
      }
    });

  // Get session details
  sessions
    .command('get <session-id>')
    .description('Get session details')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .option('--include-docs', 'Include document list')
    .action(async (sessionId, options) => {
      try {
        const config = configManager.load();

        if (!config.baseUrl || !config.apiKey) {
          Logger.error('No authentication found. Please login first.');
          process.exit(1);
        }

        const spinner = ora('Loading session details...').start();

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        const session = await client.sessions.get(sessionId);
        
        if (options.includeDocs) {
          const documents = await client.documents.listBySession(sessionId);
          (session as any).documents = documents;
        }
        
        spinner.stop();

        const output = OutputFormatter.format(session, {
          format: options.format as any,
          pretty: true
        });

        console.log(output);

      } catch (error: any) {
        Logger.error('Failed to get session:', error.message);
        process.exit(1);
      }
    });

  // Update session
  sessions
    .command('update <session-id>')
    .description('Update session name')
    .option('-n, --name <name>', 'New session name')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .action(async (sessionId, options) => {
      try {
        const config = configManager.load();

        if (!config.baseUrl || !config.apiKey) {
          Logger.error('No authentication found. Please login first.');
          process.exit(1);
        }

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        let newName = options.name;

        if (!newName) {
          const current = await client.sessions.get(sessionId);
          const answers = await inquirer.prompt([
            {
              type: 'input',
              name: 'name',
              message: 'New session name:',
              default: current.name,
              validate: (input) => input.trim().length > 0 || 'Session name is required'
            }
          ]);
          newName = answers.name;
        }

        const spinner = ora('Updating session...').start();

        const session = await client.sessions.update(sessionId, { name: newName });
        
        spinner.stop();

        Logger.success('Session updated successfully');

        const output = OutputFormatter.format(session, {
          format: options.format as any,
          pretty: true
        });

        console.log(output);

      } catch (error: any) {
        Logger.error('Failed to update session:', error.message);
        process.exit(1);
      }
    });

  // Delete session
  sessions
    .command('delete <session-id>')
    .alias('rm')
    .description('Delete a session and all its documents')
    .option('-f, --force', 'Skip confirmation prompt')
    .action(async (sessionId, options) => {
      try {
        const config = configManager.load();

        if (!config.baseUrl || !config.apiKey) {
          Logger.error('No authentication found. Please login first.');
          process.exit(1);
        }

        const client = new BrandGPTClient({
          baseUrl: config.baseUrl,
          apiKey: config.apiKey
        });

        if (!options.force) {
          const session = await client.sessions.get(sessionId);
          const documents = await client.documents.listBySession(sessionId);
          
          Logger.warn(`This will permanently delete session "${session.name}" and ${documents.length} associated documents.`);
          
          const { confirm } = await inquirer.prompt([
            {
              type: 'confirm',
              name: 'confirm',
              message: 'Are you sure you want to delete this session?',
              default: false
            }
          ]);

          if (!confirm) {
            Logger.info('Deletion cancelled');
            return;
          }
        }

        const spinner = ora('Deleting session...').start();

        await client.sessions.delete(sessionId);
        
        spinner.stop();

        Logger.success('Session deleted successfully');

      } catch (error: any) {
        Logger.error('Failed to delete session:', error.message);
        process.exit(1);
      }
    });

  // List documents in session
  sessions
    .command('docs <session-id>')
    .description('List documents in a session')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .action(async (sessionId, options) => {
      try {
        const config = configManager.load();

        if (!config.baseUrl || !config.apiKey) {
          Logger.error('No authentication found. Please login first.');
          process.exit(1);
        }

        const spinner = ora('Loading documents...').start();

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

        const output = OutputFormatter.format(documents, {
          format: options.format as any,
          pretty: true
        });

        console.log(output);
        Logger.info(`Found ${documents.length} documents`);

      } catch (error: any) {
        Logger.error('Failed to list documents:', error.message);
        process.exit(1);
      }
    });

  return sessions;
}