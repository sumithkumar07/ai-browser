import fetch from 'node-fetch';
import { EventEmitter } from 'events';
import * as https from 'https';
import * as http from 'http';

export interface CrossOriginRequest {
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  followRedirects?: boolean;
}

export interface CrossOriginResponse {
  success: boolean;
  status?: number;
  statusText?: string;
  headers?: Record<string, string>;
  data?: any;
  error?: string;
  url: string;
  responseTime: number;
}

export class CrossOriginHandler extends EventEmitter {
  private userAgent: string;
  private defaultHeaders: Record<string, string>;
  private httpsAgent: https.Agent;
  private httpAgent: http.Agent;

  constructor() {
    super();
    
    this.userAgent = 'AETHER Desktop Browser/2.0 (Cross-Origin Handler)';
    this.defaultHeaders = {
      'User-Agent': this.userAgent,
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      'Accept-Language': 'en-US,en;q=0.5',
      'Accept-Encoding': 'gzip, deflate, br',
      'Connection': 'keep-alive',
      'Upgrade-Insecure-Requests': '1'
    };

    // Create agents that ignore SSL errors for maximum compatibility
    this.httpsAgent = new https.Agent({
      rejectUnauthorized: false,
      keepAlive: true,
      timeout: 30000
    });

    this.httpAgent = new http.Agent({
      keepAlive: true,
      timeout: 30000
    });
  }

  async initialize(): Promise<void> {
    console.log('🔒 Initializing Cross-Origin Handler...');
    console.log('✅ Cross-Origin Handler initialized with unrestricted access');
  }

  async makeRequest(config: CrossOriginRequest): Promise<CrossOriginResponse> {
    const startTime = Date.now();
    
    try {
      console.log(`🌐 Making cross-origin request: ${config.method} ${config.url}`);

      // Prepare request options
      const options: any = {
        method: config.method,
        headers: {
          ...this.defaultHeaders,
          ...config.headers
        },
        timeout: config.timeout || 30000,
        agent: config.url.startsWith('https:') ? this.httpsAgent : this.httpAgent
      };

      // Add body for POST/PUT/PATCH requests
      if (config.body && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
        if (typeof config.body === 'object') {
          options.body = JSON.stringify(config.body);
          options.headers['Content-Type'] = 'application/json';
        } else {
          options.body = config.body;
        }
      }

      // Make the request
      const response = await fetch(config.url, options);
      const responseTime = Date.now() - startTime;

      // Parse response data
      let data;
      const contentType = response.headers.get('content-type') || '';
      
      if (contentType.includes('application/json')) {
        data = await response.json();
      } else if (contentType.includes('text/')) {
        data = await response.text();
      } else {
        data = await response.buffer();
      }

      // Convert headers to object
      const responseHeaders: Record<string, string> = {};
      response.headers.forEach((value, key) => {
        responseHeaders[key] = value;
      });

      const result: CrossOriginResponse = {
        success: response.ok,
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
        data,
        url: config.url,
        responseTime
      };

      this.emit('request-completed', result);
      return result;

    } catch (error) {
      const responseTime = Date.now() - startTime;
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      console.error('❌ Cross-origin request failed:', errorMessage);

      const result: CrossOriginResponse = {
        success: false,
        error: errorMessage,
        url: config.url,
        responseTime
      };

      this.emit('request-failed', result);
      return result;
    }
  }

  async bypassCors(url: string): Promise<CrossOriginResponse> {
    // Attempt to bypass CORS by making the request from desktop
    return await this.makeRequest({
      url,
      method: 'GET'
    });
  }

  async proxyRequest(targetUrl: string, originalRequest: CrossOriginRequest): Promise<CrossOriginResponse> {
    // Act as a proxy to bypass CORS restrictions
    console.log(`🔄 Proxying request to: ${targetUrl}`);

    // Add proxy headers
    const proxyHeaders = {
      ...originalRequest.headers,
      'X-Proxy-Target': targetUrl,
      'X-Proxy-Source': 'aether-desktop'
    };

    return await this.makeRequest({
      ...originalRequest,
      url: targetUrl,
      headers: proxyHeaders
    });
  }

  async bulkRequest(requests: CrossOriginRequest[]): Promise<CrossOriginResponse[]> {
    console.log(`📦 Processing ${requests.length} bulk cross-origin requests`);

    // Process requests in parallel with concurrency limit
    const concurrencyLimit = 5;
    const results: CrossOriginResponse[] = [];
    
    for (let i = 0; i < requests.length; i += concurrencyLimit) {
      const batch = requests.slice(i, i + concurrencyLimit);
      const batchPromises = batch.map(request => this.makeRequest(request));
      const batchResults = await Promise.allSettled(batchPromises);
      
      for (const result of batchResults) {
        if (result.status === 'fulfilled') {
          results.push(result.value);
        } else {
          results.push({
            success: false,
            error: result.reason instanceof Error ? result.reason.message : 'Unknown error',
            url: 'unknown',
            responseTime: 0
          });
        }
      }
    }

    return results;
  }

  async downloadFile(url: string, savePath: string): Promise<{ success: boolean; path?: string; error?: string }> {
    try {
      console.log(`💾 Downloading file from: ${url}`);

      const response = await this.makeRequest({
        url,
        method: 'GET'
      });

      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to download file');
      }

      // Save file
      const fs = await import('fs/promises');
      await fs.writeFile(savePath, response.data);

      console.log(`✅ File downloaded to: ${savePath}`);
      return { success: true, path: savePath };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('❌ File download failed:', errorMessage);
      return { success: false, error: errorMessage };
    }
  }

  async testConnection(urls: string[] = ['https://httpbin.org/get']): Promise<{ success: boolean; results: any[] }> {
    console.log('🔍 Testing cross-origin connectivity...');

    const testRequests = urls.map(url => ({
      url,
      method: 'GET' as const
    }));

    const results = await this.bulkRequest(testRequests);
    const successCount = results.filter(r => r.success).length;

    console.log(`✅ Cross-origin test completed: ${successCount}/${urls.length} successful`);

    return {
      success: successCount > 0,
      results
    };
  }

  setUserAgent(userAgent: string): void {
    this.userAgent = userAgent;
    this.defaultHeaders['User-Agent'] = userAgent;
    console.log(`🔧 User agent updated: ${userAgent}`);
  }

  addDefaultHeader(key: string, value: string): void {
    this.defaultHeaders[key] = value;
    console.log(`🔧 Default header added: ${key}=${value}`);
  }

  removeDefaultHeader(key: string): void {
    delete this.defaultHeaders[key];
    console.log(`🔧 Default header removed: ${key}`);
  }

  getStats(): any {
    return {
      userAgent: this.userAgent,
      defaultHeaders: this.defaultHeaders,
      httpAgent: {
        keepAlive: this.httpAgent.keepAlive,
        timeout: this.httpAgent.timeout
      },
      httpsAgent: {
        keepAlive: this.httpsAgent.keepAlive,
        timeout: this.httpsAgent.timeout
      }
    };
  }
}