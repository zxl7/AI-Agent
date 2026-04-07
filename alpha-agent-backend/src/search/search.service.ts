import { Injectable, Logger } from '@nestjs/common';
import HttpsProxyAgent from 'https-proxy-agent';
import { search } from 'duck-duck-scrape';
import { searchConfig } from '../config/search.config';

/**
 * 联网搜索服务类
 * 封装了 DuckDuckGo 搜索逻辑，并支持通过 HttpsProxyAgent 进行国内环境代理访问
 */
@Injectable()
export class SearchService {
  private readonly logger = new Logger(SearchService.name);
  private proxyAgent: any;

  constructor() {
    this.initProxy();
  }

  /**
   * 初始化代理配置
   */
  private initProxy() {
    if (searchConfig.proxyUrl) {
      this.logger.log(
        `检测到代理配置: ${searchConfig.proxyUrl}，正在初始化代理 Agent...`,
      );
      try {
        // HttpsProxyAgent v5 是一个工厂函数
        this.proxyAgent = (HttpsProxyAgent as any)(searchConfig.proxyUrl);
      } catch (error) {
        this.logger.error(
          `初始化代理 Agent 失败: ${error instanceof Error ? error.message : String(error)}`,
        );
      }
    }
  }

  /**
   * 执行联网搜索
   * @param query 搜索关键词
   * @returns 搜索结果文本，未找到则返回空字符串
   */
  async search(query: string): Promise<string> {
    try {
      this.logger.log(`正在执行联网搜索: "${query}"`);

      // 直接调用 duck-duck-scrape 的 search 函数
      // 第三个参数是 needleOptions，可以传入 agent
      const searchResults = await search(
        query,
        {},
        {
          agent: this.proxyAgent,
          timeout: 10000, // 增加超时时间
        },
      );

      if (
        !searchResults ||
        searchResults.noResults ||
        !searchResults.results.length
      ) {
        this.logger.warn(`搜索未命中相关结果: "${query}"`);
        return '';
      }

      // 格式化结果，模拟 DuckDuckGoSearch 原始输出格式
      const formattedResults = searchResults.results
        .slice(0, searchConfig.maxResults)
        .map((result) => ({
          title: result.title,
          link: result.url,
          snippet: result.description,
        }));

      return JSON.stringify(formattedResults);
    } catch (error) {
      this.logger.error(
        `联网搜索服务执行异常: ${error instanceof Error ? error.message : String(error)}`,
      );
      return '';
    }
  }
}
