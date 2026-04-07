import { Controller, Get, Post, Put, Delete, Body, Res } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBody } from '@nestjs/swagger';
import type { Response } from 'express';
import { AppService } from './app.service';
import { VectorService } from './chroma/vector.service';
import { LlmService, LlmStreamChunk } from './llm/llm.service';
import { Document } from '@langchain/core/documents';
import { AddVectorDto, UpdateVectorDto, DeleteVectorDto, ChatDto } from './dto/api.dto';
import { DuckDuckGoSearch } from '@langchain/community/tools/duckduckgo_search';

@ApiTags('Agent RAG')
@Controller()
export class AppController {
  constructor(
    private readonly appService: AppService,
    private readonly vectorService: VectorService,
    private readonly llmService: LlmService,
  ) {}

  @Get()
  @ApiOperation({ summary: '测试服务联通性' })
  getHello(): string {
    return this.appService.getHello();
  }

  // --------------------------------------------------------------------------
  // 以下是向量数据库与本地大模型联合使用的 RAG 示例接口
  // --------------------------------------------------------------------------

  /**
   * 示例：获取向量库中的数据预览
   */
  @Get('vector/data')
  @ApiOperation({
    summary: '查看知识库数据',
    description: '获取当前 Chroma 向量库中的文档数据预览（默认前100条）',
  })
  @ApiResponse({ status: 200, description: '成功返回向量库数据' })
  async getVectorData() {
    const data = await this.vectorService.getAllData(100);
    return {
      success: true,
      data,
    };
  }

  /**
   * 示例：向向量数据库中添加知识库文档
   */
  @Post('vector/add')
  @ApiOperation({
    summary: '录入知识库',
    description: '将文本切片添加到 Chroma 向量库中',
  })
  @ApiBody({ type: AddVectorDto })
  @ApiResponse({ status: 201, description: '成功入库' })
  async addData(@Body() body: AddVectorDto) {
    await this.vectorService.addTexts(body.texts, body.metadatas);
    return { success: true, message: '知识已成功入库' };
  }

  /**
   * 示例：更新知识库文档
   */
  @Put('vector/update')
  @ApiOperation({
    summary: '更新知识库片段',
    description: '更新向量库中的指定文档',
  })
  @ApiBody({ type: UpdateVectorDto })
  @ApiResponse({ status: 200, description: '成功更新' })
  async updateData(@Body() body: UpdateVectorDto) {
    await this.vectorService.updateDocument(body.id, body.text, body.metadata);
    return { success: true, message: '知识已成功更新' };
  }

  /**
   * 示例：删除知识库文档
   */
  @Delete('vector/delete')
  @ApiOperation({
    summary: '删除知识库片段',
    description: '从向量库中删除指定的文档',
  })
  @ApiBody({ type: DeleteVectorDto })
  @ApiResponse({ status: 200, description: '成功删除' })
  async deleteData(@Body() body: DeleteVectorDto) {
    await this.vectorService.deleteDocuments(body.ids);
    return { success: true, message: '知识已成功删除' };
  }

  /**
   * 示例：基于 Agentic RAG 的高级问答对话
   */
  @Post('chat')
  @ApiOperation({
    summary: 'Agentic RAG 问答对话',
    description: '结合向量库知识的流式问答对话（SSE），带有多路召回与 Rerank 模拟',
  })
  @ApiBody({ type: ChatDto })
  @ApiResponse({ status: 201, description: '成功返回流式生成结果' })
  async chatWithRag(@Body() body: ChatDto, @Res() response: Response) {
    response.setHeader('Content-Type', 'text/event-stream; charset=utf-8');
    response.setHeader('Cache-Control', 'no-cache, no-transform');
    response.setHeader('Connection', 'keep-alive');
    response.setHeader('X-Accel-Buffering', 'no');
    response.flushHeaders();

    const writeEvent = (payload: Record<string, unknown>) => {
      response.write(`data: ${JSON.stringify(payload)}\n\n`);
    };

    try {
      writeEvent({ type: 'status', phase: 'thinking' });
      writeEvent({ type: 'reasoning', content: '【系统调度】启动 Agentic RAG 工作流...\n' });

      // ==========================================
      // 策略 1 & 2: 多路召回 (Query Expansion) 与混合检索模拟
      // ==========================================
      writeEvent({ type: 'reasoning', content: '\n➤ 步骤 1: 正在分析用户意图，扩展多维检索词 (Multi-Query)...\n' });
      const queries = [body.question];
      try {
        const expanded = await this.llmService.expandQuery(body.question);
        if (expanded.length > 0) {
          queries.push(...expanded);
          writeEvent({ type: 'reasoning', content: `  ↳ 生成扩展查询：${expanded.join(', ')}\n` });
        }
      } catch (e) {
        writeEvent({ type: 'reasoning', content: `  ↳ 查询扩展失败，降级使用原始查询\n` });
      }

      writeEvent({ type: 'reasoning', content: '\n➤ 步骤 2: 执行混合检索 (多路向量召回)...\n' });
      const allDocs: Document[] = [];
      for (const q of queries) {
        // 每路召回 5 条
        const docs = await this.vectorService.similaritySearch(q, 5);
        allDocs.push(...docs);
      }
      writeEvent({ type: 'reasoning', content: `  ↳ 多路召回总计获取 ${allDocs.length} 条初始片段\n` });

      // ==========================================
      // 策略 3: 补充互联网搜索 (Web Search Tool)
      // ==========================================
      writeEvent({ type: 'reasoning', content: '\n➤ 步骤 3: 尝试调用外挂工具进行联网检索 (Web Search)...\n' });
      try {
        const searchTool = new DuckDuckGoSearch({ maxResults: 3 });
        // 调用工具查询互联网，补充时效性数据
        const webResultStr = await searchTool.invoke(body.question);
        if (webResultStr && webResultStr.length > 0 && webResultStr !== 'No good result found.') {
          allDocs.push(
            new Document({
              pageContent: webResultStr,
              metadata: { source: 'DuckDuckGo Web Search' },
            })
          );
          writeEvent({ type: 'reasoning', content: `  ↳ 成功从互联网工具获取实时补充数据\n` });
        } else {
          writeEvent({ type: 'reasoning', content: `  ↳ 互联网未匹配到强相关数据，仅使用本地库\n` });
        }
      } catch (e) {
        writeEvent({ type: 'reasoning', content: `  ↳ 互联网搜索服务连接超时，跳过此步骤\n` });
      }

      // ==========================================
      // 策略 4: 重排序 (Rerank) 与去重模拟
      // ==========================================
      writeEvent({ type: 'reasoning', content: '\n➤ 步骤 4: 启动重排序 (Rerank) 与上下文压缩...\n' });
      const uniqueDocsMap = new Map<string, Document>();
      // 简单模拟 Rerank：按内容去重，并保留最先召回（最相关）的记录
      for (const doc of allDocs) {
        if (!uniqueDocsMap.has(doc.pageContent)) {
          uniqueDocsMap.set(doc.pageContent, doc);
        }
      }
      // 提取 Top 10 作为最终上下文
      const finalDocs = Array.from(uniqueDocsMap.values()).slice(0, 10);
      writeEvent({ type: 'reasoning', content: `  ↳ Rerank 完毕，筛选出最核心的 ${finalDocs.length} 条高价值片段注入上下文\n` });

      writeEvent({
        type: 'context',
        retrievedContext: finalDocs,
      });

      // ==========================================
      // 策略 5: 最终大模型生成
      // ==========================================
      writeEvent({ type: 'reasoning', content: '\n➤ 步骤 5: 调用大模型进行深度阅读与逻辑生成...\n' });

      const context = finalDocs.map((doc) => doc.pageContent).join('\n\n');
      const prompt = `你是一个有帮助的 AI 助手。
请优先根据以下【参考知识】来回答用户的问题。
如果【参考知识】中没有提供足够的相关信息，你可以结合你自身的知识库进行补充回答，并在回答中委婉地说明这是你的补充建议，而不是直接说不知道。

【参考知识】：
${context}

【用户问题】：
${body.question}`;

      const stream = this.llmService.generateResponseStream(
        prompt,
      ) as unknown as AsyncGenerator<LlmStreamChunk>;
      let hasStartedAnswer = false;

      for await (const chunk of stream) {
        if (chunk.type === 'delta' && !hasStartedAnswer) {
          hasStartedAnswer = true;
          writeEvent({
            type: 'status',
            phase: 'answering',
          });
        }

        writeEvent(chunk as unknown as Record<string, unknown>);
      }

      response.write('data: [DONE]\n\n');
      response.end();
    } catch (error) {
      writeEvent({
        type: 'error',
        error:
          error instanceof Error
            ? error.message
            : 'RAG 流式生成过程中出现未知错误',
      });
      response.write('data: [DONE]\n\n');
      response.end();
    }
  }
}
