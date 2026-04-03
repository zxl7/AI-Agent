import { Controller, Get, Post, Body } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBody } from '@nestjs/swagger';
import { AppService } from './app.service';
import { VectorService } from './chroma/vector.service';
import { LlmService } from './llm/llm.service';
import { AddVectorDto, ChatDto } from './dto/api.dto';

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
   * 示例：基于向量检索的大模型对话 (RAG 核心流程)
   */
  @Post('chat')
  @ApiOperation({
    summary: 'RAG 问答对话',
    description: '结合向量库知识的对话问答',
  })
  @ApiBody({ type: ChatDto })
  @ApiResponse({ status: 201, description: '成功返回生成的回答' })
  async chatWithRag(@Body() body: ChatDto) {
    // 1. 从 Chroma 向量库检索相关上下文 (基于用户提问)
    const docs = await this.vectorService.similaritySearch(body.question, 2);

    // 2. 提取文本，拼装知识库上下文
    const context = docs.map((doc) => doc.pageContent).join('\n\n');

    // 3. 构建给本地大模型的 Prompt
    const prompt = `你是一个有帮助的 AI 助手。请根据以下提供的参考知识回答用户的问题。如果上下文中没有相关信息，请如实回答不知道。
    
【参考知识】：
${context}

【用户问题】：
${body.question}`;

    // 4. 调用本地大模型 (http://127.0.0.1:1234/v1/responses)
    const answer = await this.llmService.generateResponse(prompt);

    return {
      success: true,
      answer,
      retrievedContext: docs, // 一并返回命中的知识片段以便调试
    };
  }
}
