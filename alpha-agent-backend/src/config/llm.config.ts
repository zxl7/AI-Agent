import { Embeddings } from '@langchain/core/embeddings';
import { AsyncCaller } from '@langchain/core/utils/async_caller';

/**
 * 这是一个占位的 Embeddings 实现。
 * 请替换为你实际使用的 LLM Embeddings（例如 OpenAIEmbeddings 等）。
 */
export const embeddings: Embeddings = {
  caller: new AsyncCaller({}),
  embedDocuments: async (documents: string[]) => {
    return Promise.resolve(documents.map(() => [0.1, 0.2, 0.3]));
  },
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  embedQuery: async (_document: string) => {
    return Promise.resolve([0.1, 0.2, 0.3]);
  },
};
