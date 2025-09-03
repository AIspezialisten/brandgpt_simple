import { Command } from 'commander';
import inquirer from 'inquirer';
import ora from 'ora';
import { BrandGPTClient } from '../../client';
import { ConfigManager } from '../config';
import { Logger, OutputFormatter } from '../utils';

export function createAuthCommands(program: Command, configManager: ConfigManager): Command {
  const auth = program
    .command('auth')
    .description('Authentication commands');

  // Login command
  auth
    .command('login')
    .description('Login with username and password')
    .option('-u, --username <username>', 'Username')
    .option('-p, --password <password>', 'Password')
    .option('-s, --server <url>', 'BrandGPT server URL')
    .action(async (options) => {
      try {
        const config = configManager.load();
        
        // Prompt for missing information
        const answers = await inquirer.prompt([
          {
            type: 'input',
            name: 'username',
            message: 'Username:',
            when: !options.username
          },
          {
            type: 'password',
            name: 'password',
            message: 'Password:',
            when: !options.password
          },
          {
            type: 'input',
            name: 'server',
            message: 'BrandGPT server URL:',
            default: config.baseUrl || 'https://api.brandgpt.com',
            when: !options.server && !config.baseUrl
          }
        ]);

        const username = options.username || answers.username;
        const password = options.password || answers.password;
        const server = options.server || answers.server || config.baseUrl;

        const spinner = ora('Logging in...').start();

        const client = new BrandGPTClient({ baseUrl: server });
        
        // Login with credentials
        const tokenResponse = await client.auth.login({ username, password });
        
        // Set the token for subsequent requests
        client.setApiKey(tokenResponse.access_token);
        
        // Get user information
        const user = await client.auth.getCurrentUser();
        
        spinner.stop();

        Logger.success('Login successful!');
        Logger.info(`Welcome, ${user.username} (${user.email})`);

        // Save server URL to config
        configManager.update({ baseUrl: server });

        // Ask if user wants to generate and save an API key
        const { generateApiKey } = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'generateApiKey',
            message: 'Would you like to generate and save an API key for future use?',
            default: true
          }
        ]);

        if (generateApiKey) {
          const apiSpinner = ora('Generating API key...').start();
          const apiKeyResponse = await client.auth.generateApiKey();
          apiSpinner.stop();

          configManager.update({ apiKey: apiKeyResponse.api_key });
          Logger.success('API key generated and saved to config');
          Logger.info('You can now use the CLI without logging in again');
        }

      } catch (error: any) {
        Logger.error('Login failed:', error.message);
        process.exit(1);
      }
    });

  // Register command
  auth
    .command('register')
    .description('Register a new user account')
    .option('-u, --username <username>', 'Username')
    .option('-e, --email <email>', 'Email address')
    .option('-p, --password <password>', 'Password')
    .option('-s, --server <url>', 'BrandGPT server URL')
    .action(async (options) => {
      try {
        const config = configManager.load();

        const answers = await inquirer.prompt([
          {
            type: 'input',
            name: 'username',
            message: 'Username:',
            when: !options.username,
            validate: (input) => input.length >= 3 || 'Username must be at least 3 characters'
          },
          {
            type: 'input',
            name: 'email',
            message: 'Email:',
            when: !options.email,
            validate: (input) => /\S+@\S+\.\S+/.test(input) || 'Please enter a valid email address'
          },
          {
            type: 'password',
            name: 'password',
            message: 'Password:',
            when: !options.password,
            validate: (input) => input.length >= 6 || 'Password must be at least 6 characters'
          },
          {
            type: 'input',
            name: 'server',
            message: 'BrandGPT server URL:',
            default: config.baseUrl || 'https://api.brandgpt.com',
            when: !options.server && !config.baseUrl
          }
        ]);

        const username = options.username || answers.username;
        const email = options.email || answers.email;
        const password = options.password || answers.password;
        const server = options.server || answers.server || config.baseUrl;

        const spinner = ora('Registering user...').start();

        const client = new BrandGPTClient({ baseUrl: server });
        
        const user = await client.auth.register({
          username,
          email,
          password
        });

        spinner.stop();

        Logger.success('Registration successful!');
        Logger.info(`User created: ${user.username} (${user.email})`);

        // Save server URL
        configManager.update({ baseUrl: server });

        // Auto-login and generate API key
        const { autoLogin } = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'autoLogin',
            message: 'Would you like to login and generate an API key now?',
            default: true
          }
        ]);

        if (autoLogin) {
          const loginSpinner = ora('Logging in...').start();
          const tokenResponse = await client.auth.login({ username, password });
          client.setApiKey(tokenResponse.access_token);
          
          const apiKeyResponse = await client.auth.generateApiKey();
          loginSpinner.stop();

          configManager.update({ apiKey: apiKeyResponse.api_key });
          Logger.success('Logged in and API key saved to config');
        }

      } catch (error: any) {
        Logger.error('Registration failed:', error.message);
        process.exit(1);
      }
    });

  // Set API key command
  auth
    .command('set-key')
    .description('Set API key for authentication')
    .option('-k, --key <apikey>', 'API key')
    .action(async (options) => {
      try {
        let apiKey = options.key;

        if (!apiKey) {
          const answers = await inquirer.prompt([
            {
              type: 'password',
              name: 'apiKey',
              message: 'API Key:',
              validate: (input) => input.startsWith('bgpt_') || 'API key should start with "bgpt_"'
            }
          ]);
          apiKey = answers.apiKey;
        }

        configManager.update({ apiKey });
        Logger.success('API key saved to config');

      } catch (error: any) {
        Logger.error('Failed to set API key:', error.message);
        process.exit(1);
      }
    });

  // Generate API key command
  auth
    .command('generate-key')
    .description('Generate a new API key (requires existing authentication)')
    .option('-s, --server <url>', 'BrandGPT server URL')
    .action(async (options) => {
      try {
        const config = configManager.load();
        const server = options.server || config.baseUrl;

        if (!server) {
          Logger.error('No server URL configured. Use --server option or login first.');
          process.exit(1);
        }

        if (!config.apiKey) {
          Logger.error('No authentication found. Please login first.');
          process.exit(1);
        }

        const spinner = ora('Generating new API key...').start();

        const client = new BrandGPTClient({
          baseUrl: server,
          apiKey: config.apiKey
        });

        const apiKeyResponse = await client.auth.generateApiKey();
        
        spinner.stop();

        configManager.update({ apiKey: apiKeyResponse.api_key });
        
        Logger.success('New API key generated and saved');
        Logger.info('Previous API key has been replaced');

      } catch (error: any) {
        Logger.error('Failed to generate API key:', error.message);
        process.exit(1);
      }
    });

  // Who am I command
  auth
    .command('whoami')
    .description('Show current user information')
    .option('-s, --server <url>', 'BrandGPT server URL')
    .option('--format <format>', 'Output format (json, table, yaml)', 'table')
    .action(async (options) => {
      try {
        const config = configManager.load();
        const server = options.server || config.baseUrl;

        if (!server) {
          Logger.error('No server URL configured. Use --server option or login first.');
          process.exit(1);
        }

        if (!config.apiKey) {
          Logger.error('No authentication found. Please login first.');
          process.exit(1);
        }

        const spinner = ora('Getting user information...').start();

        const client = new BrandGPTClient({
          baseUrl: server,
          apiKey: config.apiKey
        });

        const user = await client.auth.getCurrentUser();
        
        spinner.stop();

        const output = OutputFormatter.format(user, { 
          format: options.format as any,
          pretty: true 
        });
        
        console.log(output);

      } catch (error: any) {
        Logger.error('Failed to get user information:', error.message);
        process.exit(1);
      }
    });

  // Logout command
  auth
    .command('logout')
    .description('Clear stored authentication')
    .action(async () => {
      try {
        const config = configManager.load();
        
        if (!config.apiKey) {
          Logger.info('No authentication found');
          return;
        }

        const { confirm } = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'confirm',
            message: 'Are you sure you want to logout and clear stored credentials?',
            default: false
          }
        ]);

        if (confirm) {
          // Keep server URL but remove API key
          configManager.update({ apiKey: undefined });
          Logger.success('Logged out successfully');
          Logger.info('API key removed from config');
        }

      } catch (error: any) {
        Logger.error('Logout failed:', error.message);
        process.exit(1);
      }
    });

  return auth;
}