import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { createVectorStore } from '../config/vector.config';
import { Chroma } from '@langchain/community/vectorstores/chroma';
import { Document } from '@langchain/core/documents';
import { ChromaClient } from 'chromadb';

@Injectable()
export class VectorService implements OnModuleInit {
  private readonly logger = new Logger(VectorService.name);
  private vectorStore: Chroma;

  /**
   * 模块初始化时，自动连接到 ChromaDB 并准备好 LangChain 的 VectorStore
   */
  async onModuleInit() {
    try {
      this.vectorStore = await createVectorStore();
      this.logger.log('✅ LangChain VectorStore 初始化成功');
    } catch (error) {
      this.logger.error('❌ LangChain VectorStore 初始化失败', error);
    }
  }

  /**
   * 获取向量库中的所有数据（用于预览和调试）
   * @param limit 返回的最大数量，默认 100 条
   */
  async getAllData(limit: number = 100) {
    try {
      // 独立创建一个 ChromaClient 实例获取数据，避免直接访问 LangChain 私有属性导致报错
      const client = new ChromaClient({ path: 'http://localhost:8000' });
      const collection = await client.getCollection({ name: 'alpha_agent' });
      const data = await collection.get({ limit });
      this.logger.log(
        `成功获取向量库中的数据预览，共 ${data?.ids?.length || 0} 条`,
      );
      // 返回友好的格式
      return {
        ids: data.ids,
        documents: data.documents,
        metadatas: data.metadatas || [],
      };
    } catch (error) {
      this.logger.error('获取向量库数据失败', error);
      throw new Error('无法连接到 Chroma 数据库获取数据');
    }
  }

  /**
   * 添加文档到向量数据库
   * @param texts 文本数组
   * @param metadatas 元数据数组
   */
  async addTexts(texts: string[], metadatas?: Record<string, any>[]) {
    if (!this.vectorStore) {
      throw new Error(
        'VectorStore is not initialized yet. Please check your ChromaDB connection.',
      );
    }

    const documents = texts.map((text, index) => {
      // ChromaDB 最新版本规定，如果不传 metadata，应该是不提供该字段，或者提供至少含有一个键值对的对象。
      // 不能传空对象 `{}`，否则会报 Expected metadata to be non-empty。
      const meta = metadatas?.[index];
      // 避免 LangChain 或 Chroma 内部将 metadata 默认转换为空对象 {} 而报错
      // 这里强制至少包含一个默认的元数据键值对
      const finalMeta =
        meta && Object.keys(meta).length > 0 ? meta : { source: 'api_upload' };

      return {
        pageContent: text,
        metadata: finalMeta,
      };
    }) as Document[];

    await this.vectorStore.addDocuments(documents);
    this.logger.log(`成功添加 ${documents.length} 条文档到向量库`);
  }

  /**
   * 更新文档内容
   * @param id 文档ID
   * @param text 新的文本内容
   * @param metadata 新的元数据
   */
  async updateDocument(
    id: string,
    text: string,
    metadata?: Record<string, any>,
  ) {
    if (!this.vectorStore) {
      throw new Error('VectorStore is not initialized yet.');
    }

    try {
      const finalMeta =
        metadata && Object.keys(metadata).length > 0
          ? metadata
          : { source: 'api_upload' };
      // 使用 LangChain 的 addDocuments 并指定 ids 选项。
      // 由于底层的 Chroma 具有 upsert 特性，这会使用配置好的 Embedding 模型
      // 为新文本生成新的向量，并覆盖对应 ID 的旧记录。
      await this.vectorStore.addDocuments(
        [{ pageContent: text, metadata: finalMeta }],
        { ids: [id] },
      );
      this.logger.log(`成功更新向量库中文档 ID: ${id}`);
    } catch (error) {
      this.logger.error(`更新向量库文档 ${id} 失败`, error);
      throw new Error('更新向量库文档失败');
    }
  }

  /**
   * 删除文档
   * @param ids 要删除的文档ID数组
   */
  async deleteDocuments(ids: string[]) {
    try {
      const client = new ChromaClient({ path: 'http://localhost:8000' });
      const collection = await client.getCollection({ name: 'alpha_agent' });

      await collection.delete({ ids });
      this.logger.log(`成功从向量库中删除 ${ids.length} 条文档`);
    } catch (error) {
      this.logger.error(`删除向量库文档失败`, error);
      throw new Error('删除向量库文档失败');
    }
  }

  /**
   * 使用相似度搜索查询相关文档
   * @param query 查询语句
   * @param k 返回的最大结果数量
   * @returns 相似的文档列表
   */
  async similaritySearch(query: string, k: number = 2): Promise<Document[]> {
    if (!this.vectorStore) {
      throw new Error(
        'VectorStore is not initialized yet. Please check your ChromaDB connection.',
      );
    }

    const results = await this.vectorStore.similaritySearch(query, k);
    this.logger.log(`成功检索到 ${results.length} 条与 "${query}" 相关的文档`);
    return results;
  }
}
