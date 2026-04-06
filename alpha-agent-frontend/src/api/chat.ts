import type { ChatRequestPayload, RetrievedContextItem } from "../types"
import { iterateSseData } from "../utils/stream"

export type ChatStreamEvent =
  | { type: "status"; phase: "thinking" | "answering" }
  | { type: "context"; retrievedContext: RetrievedContextItem[] }
  | { type: "reasoning"; content: string }
  | { type: "delta"; content: string }
  | { type: "done" }
  | { type: "error"; error: string }

/**
 * 过滤模型的 <think>...</think> 思考段落（纯函数）。
 */
export const stripThinkBlocks = (text: string): string => text.replace(/<think>[\s\S]*?<\/think>\s*/g, "")

/**
 * 发起 /api/chat 的流式请求并消费 SSE 事件。
 * - 与后端约定 data: JSON + data: [DONE] 协议
 * - 只负责协议解析，不管理组件状态
 */
export const streamChat = async function* (options: {
  apiBase: string
  payload: ChatRequestPayload
  signal: AbortSignal
}): AsyncGenerator<ChatStreamEvent> {
  try {
    const response = await fetch(`${options.apiBase}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      signal: options.signal,
      body: JSON.stringify({ question: options.payload.message }),
    })

    if (!response.ok) {
      const text = await response.text().catch(() => "")
      yield { type: "error", error: text || `请求失败（HTTP ${response.status}）` }
      return
    }

    if (!response.body) {
      yield { type: "error", error: "当前浏览器不支持流式响应" }
      return
    }

    for await (const data of iterateSseData(response.body)) {
      if (data === "[DONE]") {
        yield { type: "done" }
        return
      }

      let payload: unknown
      try {
        payload = JSON.parse(data)
      } catch {
        continue
      }

      if (!payload || typeof payload !== "object") {
        continue
      }

      const event = payload as Record<string, unknown>

      if (event.type === "error") {
        yield {
          type: "error",
          error: typeof event.error === "string" ? event.error : "请求失败",
        }
        return
      }

      if (
        event.type === "status" &&
        (event.phase === "thinking" || event.phase === "answering")
      ) {
        yield { type: "status", phase: event.phase }
        continue
      }

      if (event.type === "context" && Array.isArray(event.retrievedContext)) {
        yield {
          type: "context",
          retrievedContext: event.retrievedContext as RetrievedContextItem[],
        }
        continue
      }

      if (event.type === "reasoning" && typeof event.content === "string") {
        yield {
          type: "reasoning",
          content: event.content,
        }
        continue
      }

      if (event.type === "delta" && typeof event.content === "string") {
        yield {
          type: "delta",
          content: event.content,
        }
      }
    }
  } catch (err: any) {
    if (err?.name === "AbortError") {
      throw err
    }
    yield { type: "error", error: err?.message || "网络异常" }
  }
}
