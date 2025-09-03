import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

export interface CliConfig {
  baseUrl?: string;
  apiKey?: string;
  defaultTimeout?: number;
  outputFormat?: 'json' | 'table' | 'yaml';
}

export class ConfigManager {
  private configPath: string;

  constructor() {
    const configDir = path.join(os.homedir(), '.brandgpt');
    this.configPath = path.join(configDir, 'config.json');
    
    // Ensure config directory exists
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }
  }

  load(): CliConfig {
    try {
      if (fs.existsSync(this.configPath)) {
        const configData = fs.readFileSync(this.configPath, 'utf8');
        return JSON.parse(configData);
      }
    } catch (error) {
      console.warn('Warning: Could not load config file, using defaults');
    }
    
    return {};
  }

  save(config: CliConfig): void {
    try {
      fs.writeFileSync(this.configPath, JSON.stringify(config, null, 2));
    } catch (error) {
      throw new Error(`Failed to save config: ${error}`);
    }
  }

  update(updates: Partial<CliConfig>): CliConfig {
    const config = this.load();
    const newConfig = { ...config, ...updates };
    this.save(newConfig);
    return newConfig;
  }

  clear(): void {
    try {
      if (fs.existsSync(this.configPath)) {
        fs.unlinkSync(this.configPath);
      }
    } catch (error) {
      throw new Error(`Failed to clear config: ${error}`);
    }
  }

  getConfigPath(): string {
    return this.configPath;
  }
}