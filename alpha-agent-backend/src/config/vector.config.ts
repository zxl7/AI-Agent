import { Chroma } from '@langchain/community/vectorstores/chroma';
import { embeddings } from './llm.config';
import { ChromaClient } from 'chromadb';

// 固定配置，避免变量错误
const CHROMA_URL = 'http://localhost:8000';
const COLLECTION_NAME = 'alpha_agent';

export async function createVectorStore() {
  // 1. 初始化Chroma客户端，明确指定服务地址
  const client = new ChromaClient({
    path: CHROMA_URL,
  });

  // 2. 安全获取/创建集合（避免集合不存在报错）

  let collection: any;
  try {
    collection = await client.getCollection({ name: COLLECTION_NAME });
    console.log(`✅ 已连接到Chroma集合: ${COLLECTION_NAME}`);
  } catch {
    // 集合不存在则创建
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    collection = await client.createCollection({ name: COLLECTION_NAME });
    console.log(`✅ 新建Chroma集合: ${COLLECTION_NAME}`);
  }

  // 3. 正确初始化Chroma向量库
  // LangChain 的 Chroma 类接收 index 作为外部传入的 client 实例
  return new Chroma(embeddings, {
    collectionName: COLLECTION_NAME,
    index: client,
  });
}
