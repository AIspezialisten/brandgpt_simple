import chalk from 'chalk';
import { table } from 'table';
import * as fs from 'fs';

export interface OutputOptions {
  format: 'json' | 'table' | 'yaml';
  pretty?: boolean;
}

export class OutputFormatter {
  static format(data: any, options: OutputOptions = { format: 'json' }): string {
    switch (options.format) {
      case 'table':
        return this.formatTable(data);
      case 'yaml':
        return this.formatYaml(data);
      case 'json':
      default:
        return options.pretty ? JSON.stringify(data, null, 2) : JSON.stringify(data);
    }
  }

  private static formatTable(data: any): string {
    if (!data) return 'No data';

    if (Array.isArray(data)) {
      if (data.length === 0) return 'No items found';
      
      const headers = Object.keys(data[0]);
      const rows = data.map(item => headers.map(header => String(item[header] || '')));
      const formattedHeaders = headers.map(h => chalk.bold(h));
      
      return table([formattedHeaders, ...rows]);
    } else if (typeof data === 'object') {
      const rows = Object.entries(data).map(([key, value]) => [key, String(value)]);
      const formattedHeaders = [chalk.bold('Property'), chalk.bold('Value')];
      return table([formattedHeaders, ...rows]);
    }

    return String(data);
  }

  private static formatYaml(data: any, indent = 0): string {
    const spaces = ' '.repeat(indent);
    
    if (data === null || data === undefined) {
      return 'null';
    }
    
    if (typeof data === 'string') {
      return data.includes('\n') ? `|\n${data.split('\n').map(line => spaces + '  ' + line).join('\n')}` : data;
    }
    
    if (typeof data === 'number' || typeof data === 'boolean') {
      return String(data);
    }
    
    if (Array.isArray(data)) {
      return data.map(item => spaces + '- ' + this.formatYaml(item, indent + 2)).join('\n');
    }
    
    if (typeof data === 'object') {
      return Object.entries(data)
        .map(([key, value]) => `${spaces}${key}: ${this.formatYaml(value, indent + 2)}`)
        .join('\n');
    }
    
    return String(data);
  }
}

export class Logger {
  static info(message: string, ...args: any[]): void {
    console.log(chalk.blue('ℹ'), message, ...args);
  }

  static success(message: string, ...args: any[]): void {
    console.log(chalk.green('✅'), message, ...args);
  }

  static warn(message: string, ...args: any[]): void {
    console.log(chalk.yellow('⚠️'), message, ...args);
  }

  static error(message: string, ...args: any[]): void {
    console.error(chalk.red('❌'), message, ...args);
  }

  static debug(message: string, ...args: any[]): void {
    if (process.env.DEBUG) {
      console.log(chalk.gray('🔍'), message, ...args);
    }
  }
}

export function validateFile(filePath: string): void {
  if (!fs.existsSync(filePath)) {
    throw new Error(`File not found: ${filePath}`);
  }
  
  const stats = fs.statSync(filePath);
  if (!stats.isFile()) {
    throw new Error(`Path is not a file: ${filePath}`);
  }
}

export function parseJsonFile(filePath: string): any {
  validateFile(filePath);
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    throw new Error(`Failed to parse JSON file ${filePath}: ${error}`);
  }
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function formatDuration(milliseconds: number): string {
  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}