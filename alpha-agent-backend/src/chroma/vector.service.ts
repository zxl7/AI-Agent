import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { createVectorStore } from '../config/vector.config';
import { Chroma } from '@langchain/community/vectorstores/chroma';
import { Document } from '@langchain/core/documents';

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
