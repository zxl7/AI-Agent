import { Controller, Get, Post, Put, Delete, Body, Res } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBody } from '@nestjs/swagger';
import type { Response } from 'express';
import { AppService } from './app.service';
import { VectorService } from './chroma/vector.service';
import { LlmService } from './llm/llm.service';
import type { LlmStreamChunk } from './llm/llm.service';
import { AddVectorDto, UpdateVectorDto, DeleteVectorDto, ChatDto } from './dto/api.dto';

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
   * 示例：基于向量检索的大模型对话 (RAG 核心流程)
   */
  @Post('chat')
  @ApiOperation({
    summary: 'RAG 问答对话',
    description: '结合向量库知识的流式问答对话（SSE）',
  })
  @ApiBody({ type: ChatDto })
  @ApiResponse({ status: 201, description: '成功返回流式生成结果' })
  async chatWithRag(@Body() body: ChatDto, @Res() response: Response) {
    // 提升向量检索的命中数量，默认返回最相关的 5 条记录作为上下文
    const docs = await this.vectorService.similaritySearch(body.question, 50);
    const context = docs.map((doc) => doc.pageContent).join('\n\n');
    const prompt = `你是一个有帮助的 AI 助手。请根据以下提供的参考知识回答用户的问题。如果上下文中没有相关信息，请如实回答不知道。
    
【参考知识】：
${context}

【用户问题】：
${body.question}`;

    response.setHeader('Content-Type', 'text/event-stream; charset=utf-8');
    response.setHeader('Cache-Control', 'no-cache, no-transform');
    response.setHeader('Connection', 'keep-alive');
    response.setHeader('X-Accel-Buffering', 'no');
    response.flushHeaders();

    const writeEvent = (payload: Record<string, unknown>) => {
      response.write(`data: ${JSON.stringify(payload)}\n\n`);
    };

    try {
      writeEvent({
        type: 'context',
        retrievedContext: docs,
      });

      writeEvent({
        type: 'status',
        phase: 'thinking',
      });

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
