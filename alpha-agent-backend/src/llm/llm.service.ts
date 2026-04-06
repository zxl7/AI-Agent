import { Injectable, Logger } from '@nestjs/common';

export type LlmStreamChunk =
  | { type: 'reasoning'; content: string }
  | { type: 'delta'; content: string };

/**
 * 纯函数：从 OpenAI 兼容 SSE block 中提取 data 文本
 * @param block 单个 SSE block
 * @returns data 字符串
 */
const extractSseData = (block: string): string => {
  return block
    .split('\n')
    .map((line) => line.trimEnd())
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice(5).trimStart())
    .join('\n');
};

/**
 * 纯函数：按 SSE 事件边界拆分 buffer
 * @param buffer 当前缓冲区
 * @returns 已完成 block 与剩余未完成内容
 */
const splitSseBlocks = (buffer: string): { blocks: string[]; rest: string } => {
  const parts = buffer.split('\n\n');
  const rest = parts.pop() ?? '';
  return {
    blocks: parts,
    rest,
  };
};

/**
 * 纯函数：从 OpenAI 兼容 chunk 中提取 reasoning / answer 内容
 * @param payload LLM 返回的 chunk JSON
 * @returns 可渲染的增量片段数组
 */
const parseStreamPayload = (
  payload: Record<string, unknown>,
): LlmStreamChunk[] => {
  const choices = payload.choices as
    | Array<{
        delta?: {
          content?: string;
          reasoning?: string;
          reasoning_content?: string;
        };
      }>
    | undefined;

  const delta = choices?.[0]?.delta;
  const chunks: LlmStreamChunk[] = [];
  if (!delta) return chunks;

  const reasoning = delta.reasoning_content ?? delta.reasoning;
  if (typeof reasoning === 'string' && reasoning.length > 0) {
    chunks.push({ type: 'reasoning', content: reasoning });
  }

  if (typeof delta.content === 'string' && delta.content.length > 0) {
    chunks.push({ type: 'delta', content: delta.content });
  }

  return chunks;
};

@Injectable()
export class LlmService {
  private readonly logger = new Logger(LlmService.name);
  private readonly apiUrl = 'http://127.0.0.1:1234/v1/chat/completions';

  /**
   * 调用本地 LLM 的非流式接口
   * @param prompt 拼接好的 Prompt
   * @returns 大模型完整回答
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
          model: 'local-model',
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

  /**
   * 调用本地 LLM 的流式接口
   * @param prompt 拼接好的 Prompt
   * @returns 按 token / reasoning 产出的异步流
   */
  async *generateResponseStream(
    prompt: string,
  ): AsyncGenerator<LlmStreamChunk> {
    this.logger.log(`正在以流式方式调用本地 LLM 服务: ${this.apiUrl}`);

    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'local-model',
          messages: [{ role: 'user', content: prompt }],
          temperature: 0.7,
          stream: true,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(
          `请求本地大模型失败: ${response.status} ${response.statusText}`,
        );
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const { blocks, rest } = splitSseBlocks(buffer);
        buffer = rest;

        for (const block of blocks) {
          const data = extractSseData(block);
          if (!data || data === '[DONE]') {
            continue;
          }

          let payload: Record<string, unknown>;
          try {
            payload = JSON.parse(data) as Record<string, unknown>;
          } catch {
            continue;
          }

          for (const chunk of parseStreamPayload(payload)) {
            yield chunk;
          }
        }
      }
    } catch (error) {
      this.logger.error('❌ 本地大模型流式调用失败', error);
      throw new Error(
        '无法连接到本地大模型流式接口，请确保 http://127.0.0.1:1234 正在运行并支持 stream。',
      );
    }
  }
}
