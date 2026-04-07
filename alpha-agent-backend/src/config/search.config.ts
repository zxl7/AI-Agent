/**
 * 搜索相关的配置项
 */
export const searchConfig = {
  /**
   * 联网搜索的 HTTP 代理
   * 国内环境下访问 DuckDuckGo 可能需要代理
   */
  proxyUrl: process.env.HTTPS_PROXY || 'http://127.0.0.1:5173',

  /**
   * 默认召回的网页数量
   */
  maxResults: 3,
};
