import { Injectable, Logger } from '@nestjs/common';

@Injectable()
export class LlmService {
  private readonly logger = new Logger(LlmService.name);
  // 改用标准的 OpenAI 兼容接口，大多数模型（如 LM Studio）对此支持更好
  private readonly apiUrl = 'http://127.0.0.1:1234/v1/chat/completions';

  /**
   * 纯函数：调用本地 LLM 接口
   * 将系统提示词、检索到的上下文与用户提问传递给本地大模型
   * @param prompt 拼接好的 RAG Prompt
   * @returns 大模型的回答
   */
  async generateResponse(prompt: string): Promise<string> {
    this.logger.log(`正在调用本地 LLM 服务: ${this.apiUrl}`);
    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'local-model', // LM Studio 通常忽略此字段，但 OpenAI 规范要求有
          messages: [{ role: 'user', content: prompt }],
          temperature: 0.7,
          stream: false,
        }),
      });

      if (!response.ok) {
        throw new Error(
          `请求本地大模型失败: ${response.status} ${response.statusText}`,
        );
      }

      const data = (await response.json()) as Record<string, unknown>;
      this.logger.log('✅ 成功获取大模型响应');

      // 尝试解析常见的 LLM 返回格式
      const choices = data.choices as
        | Array<{ message?: { content?: string }; text?: string }>
        | undefined;
      const result =
        (data.response as string | undefined) ||
        (data.text as string | undefined) ||
        choices?.[0]?.message?.content ||
        choices?.[0]?.text ||
        JSON.stringify(data);

      return result;
    } catch (error) {
      this.logger.error('❌ 本地大模型调用失败', error);
      throw new Error(
        '无法连接到本地大模型，请确保 http://127.0.0.1:1234 正在运行。',
      );
    }
  }
}
