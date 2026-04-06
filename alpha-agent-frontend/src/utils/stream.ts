/**
 * 流式响应处理工具：
 * - 只做「字节流 -> SSE data 字符串」的转换
 * - 不关心具体业务协议字段，保持单一职责
 */

/**
 * 从文本行中提取 data: 后的内容（纯函数）。
 */
export const extractSseData = (line: string): string | null => {
  const trimmed = line.trim()
  if (trimmed.startsWith("data:")) {
    return trimmed.slice(5).trimStart()
  }
  return null
}

/**
 * 迭代 ReadableStream 中的 SSE data 内容（副作用：读取流）。
 * - 每次 yield 的是单个 data 行的内容（可能是 JSON，也可能是 [DONE]）
 * - 不做 JSON 解析，由上层决定如何消费
 */
export const iterateSseData = async function* (
  body: ReadableStream<Uint8Array>,
  options?: { decoder?: TextDecoder }
): AsyncGenerator<string> {
  const decoder = options?.decoder ?? new TextDecoder("utf-8")
  const reader = body.getReader()

  let buffer = ""
  while (true) {
    const { value, done } = await reader.read()
    if (value) {
      buffer += decoder.decode(value, { stream: !done })
      
      // 按行分割，保留最后一部分（可能是不完整的行）
      const lines = buffer.split(/\r?\n/)
      buffer = lines.pop() ?? ""

      for (const line of lines) {
        const data = extractSseData(line)
        if (data) yield data
      }
    }
    if (done) {
      // 处理最后残留的 buffer
      if (buffer.trim()) {
        const data = extractSseData(buffer)
        if (data) yield data
      }
      break
    }
  }
}

