import type { ChatRequestPayload } from "../types"
import { iterateSseData } from "../utils/stream"

export type ChatStreamEvent =
  | { type: "delta"; content: string }
  | { type: "done" }
  | { type: "error"; error: string }

/**
 * 过滤模型的 <think>...</think> 思考段落（纯函数）。
 */
export const stripThinkBlocks = (text: string): string => text.replace(/<think>[\s\S]*?<\/think>\s*/g, "")

/**
 * 发起 /api/chat 的流式请求并将 SSE 转为结构化事件。
 * - 只负责协议层解析（[DONE]/error/delta）
 * - 不管理 UI 状态，不做 DOM 操作
 */
export const streamChat = async function* (options: {
  apiBase: string
  payload: ChatRequestPayload
  signal: AbortSignal
}): AsyncGenerator<ChatStreamEvent> {
  const response = await fetch(`${options.apiBase}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal: options.signal,
    body: JSON.stringify(options.payload),
  })

  if (!response.ok) {
    const text = await response.text().catch(() => "")
    yield { type: "error", error: text || `请求失败（HTTP ${response.status}）` }
    return
  }

  if (!response.body) {
    yield { type: "error", error: "响应不支持流式输出" }
    return
  }

  for await (const data of iterateSseData(response.body)) {
    if (data === "[DONE]") {
      yield { type: "done" }
      return
    }

    let payload: any = null
    try {
      payload = JSON.parse(data)
    } catch {
      continue
    }

    if (payload?.error) {
      yield { type: "error", error: String(payload.error) }
      return
    }

    const chunk = payload?.choices?.[0]?.delta?.content
    if (typeof chunk === "string" && chunk.length > 0) {
      yield { type: "delta", content: chunk }
    }
  }

  yield { type: "done" }
}

