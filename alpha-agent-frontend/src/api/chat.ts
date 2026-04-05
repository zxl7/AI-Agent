import type { ChatRequestPayload } from "../types"

export type ChatStreamEvent =
  | { type: "delta"; content: string; retrievedContext?: any[] }
  | { type: "done" }
  | { type: "error"; error: string }

/**
 * 过滤模型的 <think>...</think> 思考段落（纯函数）。
 */
export const stripThinkBlocks = (text: string): string => text.replace(/<think>[\s\S]*?<\/think>\s*/g, "")

/**
 * 发起 /api/chat 的请求。
 * - 后端目前是非流式的，为了兼容组合式的 AsyncGenerator 签名，这里将其包装为一次性吐出的 Generator
 */
export const streamChat = async function* (options: {
  apiBase: string
  payload: ChatRequestPayload
  signal: AbortSignal
}): AsyncGenerator<ChatStreamEvent> {
  try {
    // 适配后端需要的参数格式
    const res = await fetch(`${options.apiBase}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: options.signal,
      body: JSON.stringify({ question: options.payload.message }),
    })

    if (!res.ok) {
      const text = await res.text().catch(() => "")
      yield { type: "error", error: text || `请求失败（HTTP ${res.status}）` }
      return
    }

    const data = await res.json()

    if (data.success && data.answer) {
      // 模拟流式：直接把整个回答作为一次 delta 发送
      // 去除首尾的多余空格和换行符，避免 UI 上出现异常的空行
      yield { 
        type: "delta", 
        content: data.answer.trim(),
        retrievedContext: data.retrievedContext
      }
      yield { type: "done" }
    } else {
      yield { type: "error", error: data.message || "请求失败" }
    }
  } catch (err: any) {
    if (err.name === "AbortError") {
      throw err // 向上抛出以中止
    }
    yield { type: "error", error: err.message || "网络异常" }
  }
}

