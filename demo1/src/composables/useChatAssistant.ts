import { computed, nextTick, reactive, ref } from "vue"

/** 对话消息角色 */
export type ChatRole = "user" | "assistant"
/** 对话消息状态 */
export type ChatMessageStatus = "success" | "streaming" | "error"
/** UI 层消息模型（用于渲染与流式拼接） */
export type ChatMessage = {
  id: number
  role: ChatRole
  content: string
  rawContent?: string
  status?: ChatMessageStatus
}

/** 发送给后端的历史消息模型（system/user/assistant） */
export type ChatHistoryItem = { role: "user" | "assistant" | "system"; content: string }

type Options = {
  /** 后端基地址，例如 http://localhost:3001 */
  apiBase: string
  /** system 角色提示词，作为每次请求的第一条消息 */
  systemPrompt: ChatHistoryItem
  /** 初始欢迎语（assistant） */
  initialAssistantMessage?: string
}

/** 生成简单唯一 id（足够用于前端列表 key） */
const nowId = () => Date.now() + Math.floor(Math.random() * 1000)
/** 构造用户消息（纯函数） */
const createUserMessage = (content: string): ChatMessage => ({ id: nowId(), role: "user", content })
/** 构造 assistant 占位消息（纯函数） */
const createAssistantMessage = (status: ChatMessageStatus): ChatMessage => ({
  id: nowId(),
  role: "assistant",
  content: "",
  rawContent: "",
  status,
})

/** 从 SSE block 中抽取 data: 行（纯函数） */
const extractSseDataLines = (block: string) =>
  block
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart())
    .join("\n")

/** 过滤模型的 <think>...</think> 思考段落（纯函数） */
const stripThinkBlocks = (text: string) => text.replace(/<think>[\s\S]*?<\/think>\s*/g, "")

/**
 * 组合式对话助手：集中管理消息状态、SSE 流式接收、终止生成与滚动。
 * - 业务副作用仅集中在 send/stop/reset 中，便于测试与复用
 * - 其余为纯函数或计算属性，符合函数式与单一职责的拆分思路
 */
export const useChatAssistant = (options: Options) => {
  /** 输入框内容 */
  const inputText = ref("")
  /** 是否正在请求/流式生成中 */
  const isSending = ref(false)
  /** 用于中止当前请求 */
  const activeController = ref<AbortController | null>(null)
  /** 消息滚动容器引用 */
  const chatContainer = ref<HTMLElement | null>(null)

  /** 初始欢迎语 */
  const initialText = options.initialAssistantMessage || "你好，我是你的 AI 个人助手。你现在想做什么？"
  /** 初始消息列表（纯函数） */
  const initialHistory = (): ChatMessage[] => [{ id: nowId(), role: "assistant", content: initialText, status: "success" }]

  /** 消息列表（响应式） */
  const chatHistory = reactive<ChatMessage[]>(initialHistory())

  /** 可作为上下文发送的历史（排除 streaming 占位消息） */
  const visibleHistory = computed(() => chatHistory.filter((m) => m.status !== "streaming"))
  /** 是否进入对话模式（用于布局切换） */
  const isChatMode = computed(() => isSending.value || chatHistory.some((m) => m.role === "user"))

  /** 将滚动容器滚动到底部（副作用：读写 DOM） */
  const scrollToBottom = () => {
    if (!chatContainer.value) return
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }

  /** nextTick 后再滚动到底部，保证 DOM 已更新 */
  const scrollToBottomNextTick = async () => {
    await nextTick()
    scrollToBottom()
  }

  /** 组装请求所需的 history payload（纯函数） */
  const buildHistoryPayload = (messages: ChatMessage[]): ChatHistoryItem[] => [
    options.systemPrompt,
    ...messages.map((m) => ({ role: m.role, content: m.content })),
  ]

  /** 终止当前生成（副作用：AbortController） */
  const stopGenerating = () => {
    activeController.value?.abort()
    activeController.value = null
  }

  /** 重置对话到初始状态（副作用：修改 reactive 数组） */
  const resetConversation = () => {
    stopGenerating()
    chatHistory.splice(0, chatHistory.length, ...initialHistory())
  }

  /**
   * 发送用户输入并以 SSE 方式消费增量输出（副作用：网络请求 + 更新状态）
   * - 以 historySnapshot 固化本轮上下文，避免响应式变化导致重复上下文
   * - 将 rawContent 作为流式累积源，再派生出剥离 think 的 content
   */
  const send = async () => {
    if (isSending.value) return
    const message = inputText.value.trim()
    if (!message) return

    const historySnapshot = buildHistoryPayload(visibleHistory.value)

    chatHistory.push(createUserMessage(message))
    const assistantMsg = createAssistantMessage("streaming")
    chatHistory.push(assistantMsg)

    inputText.value = ""
    isSending.value = true
    await scrollToBottomNextTick()

    try {
      const controller = new AbortController()
      activeController.value = controller
      const response = await fetch(`${options.apiBase}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({ message, history: historySnapshot, temperature: 0.7 }),
      })

      if (!response.ok) {
        const text = await response.text().catch(() => "")
        assistantMsg.status = "error"
        assistantMsg.content = text || `请求失败（HTTP ${response.status}）`
        await scrollToBottomNextTick()
        return
      }

      if (!response.body) {
        assistantMsg.status = "error"
        assistantMsg.content = "响应不支持流式输出"
        await scrollToBottomNextTick()
        return
      }

      const decoder = new TextDecoder("utf-8")
      const reader = response.body.getReader()
      let buffer = ""

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const blocks = buffer.split("\n\n")
        buffer = blocks.pop() ?? ""

        for (const block of blocks) {
          const data = extractSseDataLines(block)
          if (!data) continue
          if (data === "[DONE]") {
            assistantMsg.status = "success"
            await scrollToBottomNextTick()
            return
          }

          let payload: any = null
          try {
            payload = JSON.parse(data)
          } catch (_) {
            continue
          }

          if (payload?.error) {
            assistantMsg.status = "error"
            assistantMsg.content = String(payload.error)
            await scrollToBottomNextTick()
            return
          }

          const chunk = payload?.choices?.[0]?.delta?.content
          if (typeof chunk === "string" && chunk.length > 0) {
            assistantMsg.rawContent = (assistantMsg.rawContent || "") + chunk
            assistantMsg.content = stripThinkBlocks(assistantMsg.rawContent || "")
            await scrollToBottomNextTick()
          }
        }
      }

      assistantMsg.status = assistantMsg.status === "error" ? "error" : "success"
      await scrollToBottomNextTick()
    } catch (e: any) {
      if (e?.name === "AbortError") {
        assistantMsg.status = assistantMsg.content ? "success" : "error"
        if (!assistantMsg.content) assistantMsg.content = "已停止生成"
      } else {
        assistantMsg.status = "error"
        assistantMsg.content = e?.message || "请求异常"
      }
      await scrollToBottomNextTick()
    } finally {
      isSending.value = false
      activeController.value = null
    }
  }

  /** 将快捷标签写入输入框（纯函数 + 轻微副作用：更新 ref） */
  const applyQuickTag = (label: string) => {
    if (isSending.value) return
    inputText.value = `帮我处理：${label}`
  }

  return {
    inputText,
    chatHistory,
    chatContainer,
    isSending,
    isChatMode,
    send,
    stopGenerating,
    applyQuickTag,
    resetConversation,
    scrollToBottom,
    scrollToBottomNextTick,
  }
}
