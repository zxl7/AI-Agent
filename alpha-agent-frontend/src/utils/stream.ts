/**
 * 流式响应处理工具：
 * - 只做「字节流 -> SSE data 字符串」的转换
 * - 不关心具体业务协议字段，保持单一职责
 */

/**
 * 从 SSE block 中抽取 data: 行并合并为单个 data 字符串（纯函数）。
 */
export const extractSseDataLines = (block: string): string =>
  block
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart())
    .join("\n")

/**
 * 按 SSE 事件分隔符切块（纯函数）。
 * SSE 事件之间通常以空行（\\n\\n）分隔。
 */
export const splitSseBlocks = (buffer: string): { blocks: string[]; rest: string } => {
  const parts = buffer.split("\n\n")
  const rest = parts.pop() ?? ""
  return { blocks: parts, rest }
}

/**
 * 迭代 ReadableStream 中的 SSE data 内容（副作用：读取流）。
 * - 每次 yield 的是某个事件的 data 字符串（可能是 JSON，也可能是 [DONE]）
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
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const { blocks, rest } = splitSseBlocks(buffer)
    buffer = rest

    for (const block of blocks) {
      const data = extractSseDataLines(block)
      if (data) yield data
    }
  }
}

