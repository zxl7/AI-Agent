import { OpenAIEmbeddings } from '@langchain/openai';

/**
 * 真实的 Embeddings 实现
 * 借用 OpenAI 的规范，但将请求转发到本地的大模型服务 (如 LM Studio/Ollama)
 */
export const embeddings = new OpenAIEmbeddings({
  // 本地模型不需要真实的 API Key，填入任意字符串即可
  openAIApiKey: 'local-api-key',
  // 模型名称，对于多数本地服务可填任意值，但填入真实的 Embedding 模型名更安全
  modelName: 'text-embedding-nomic-embed-text-v1.5',
  configuration: {
    // 指向你本地的 LM Studio 接口
    baseURL: 'http://127.0.0.1:1234/v1',
  },
});
