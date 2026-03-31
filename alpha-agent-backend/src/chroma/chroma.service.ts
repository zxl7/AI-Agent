import { Injectable, Logger } from '@nestjs/common';
import { ChromaClient, Collection } from 'chromadb';

/**
 * 纯函数：创建并返回 ChromaDB 客户端实例
 * 保持无副作用，根据输入返回确定性实例
 * @param host ChromaDB 服务的域名或 IP
 * @param port ChromaDB 服务的端口
 * @returns ChromaClient 实例
 */
export const createChromaClient = (
  host: string,
  port: number,
): ChromaClient => {
  return new ChromaClient({ host, port });
};

/**
 * 纯函数：获取或创建 ChromaDB 集合 (Collection)
 * 将集合的获取逻辑隔离在单一函数中，易于测试和复用
 * @param client ChromaDB 客户端实例
 * @param name 集合名称
 * @returns 集合对象 Promise
 */
export const getOrCreateCollection = async (
  client: ChromaClient,
  name: string,
): Promise<Collection> => {
  return await client.getOrCreateCollection({ name });
};

/**
 * 纯函数：向 ChromaDB 集合中添加文档
 * 不修改外部状态，只负责将输入数据添加到传入的 collection 中
 * @param collection 目标集合
 * @param ids 文档的唯一标识符数组
 * @param documents 文本内容数组
 * @returns 添加操作的响应结果
 */
export const addDocumentsToCollection = async (
  collection: Collection,
  ids: string[],
  documents: string[],
) => {
  return await collection.add({
    ids,
    documents,
  });
};

/**
 * 纯函数：查询 ChromaDB 集合中的相似文档
 * 专注于执行查询并返回结果，不涉及内部服务状态
 * @param collection 目标集合
 * @param queryTexts 查询文本数组
 * @param nResults 返回的匹配结果数量，默认 2
 * @returns 匹配的文档与距离信息
 */
export const queryCollection = async (
  collection: Collection,
  queryTexts: string[],
  nResults: number = 2,
) => {
  return await collection.query({
    queryTexts,
    nResults,
  });
};

@Injectable()
export class ChromaService {
  private readonly logger = new Logger(ChromaService.name);
  private client: ChromaClient;

  constructor() {
    // 默认连接本地开启的 Chroma 服务 (端口 8000 是 Chroma 默认端口)
    this.client = createChromaClient('localhost', 8000);
    this.logger.log('ChromaDB 客户端已初始化 (目标: http://localhost:8000)');
  }

  /**
   * 初始化并获取集合
   * @param collectionName 集合名称
   * @returns 集合对象
   */
  async getCollection(collectionName: string): Promise<Collection> {
    return await getOrCreateCollection(this.client, collectionName);
  }

  /**
   * 添加文档到指定的集合中
   * @param collectionName 集合名称
   * @param ids 文档 ID 列表
   * @param documents 文档内容列表
   */
  async addDocuments(
    collectionName: string,
    ids: string[],
    documents: string[],
  ) {
    const collection = await this.getCollection(collectionName);
    const result = await addDocumentsToCollection(collection, ids, documents);
    this.logger.log(
      `成功将 ${documents.length} 条文档加入集合 ${collectionName}`,
    );
    return result;
  }

  /**
   * 检索指定集合中的相似内容
   * @param collectionName 集合名称
   * @param queries 查询内容列表
   * @param limit 限制返回数量
   */
  async queryDocuments(
    collectionName: string,
    queries: string[],
    limit: number = 2,
  ) {
    const collection = await this.getCollection(collectionName);
    const result = await queryCollection(collection, queries, limit);
    this.logger.log(`成功在集合 ${collectionName} 中查询到结果`);
    return result;
  }
}
