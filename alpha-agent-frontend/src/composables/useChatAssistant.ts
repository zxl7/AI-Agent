import { computed, nextTick, reactive, ref } from "vue"
import { streamChat, stripThinkBlocks } from "../api/chat"
import type { ChatHistoryItem, ChatMessage, ChatMessageStatus, ChatRequestPayload } from "../types"
import { saveChatHistory, loadChatHistory } from "../utils/indexeddb"

export type { ChatHistoryItem, ChatMessage, ChatMessageStatus, ChatRole } from "../types"

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
  thinkingContent: "",
  streamPhase: "thinking",
  status,
})

/**
 * 组合式对话助手：集中管理消息状态、SSE 流式接收、终止生成与滚动。
 * - 业务副作用仅集中在 send/stop/reset 中，便于测试与复用
 * - 其余为纯函数或计算属性，符合函数式与单一职责的拆分思路
 */
export const useChatAssistant = (options: Options) => {
  /** 输入框内容（状态由当前组合函数持有） */
  const inputText = ref<string>("")
  /** 是否正在请求/流式生成中 */
  const isSending = ref<boolean>(false)
  /** 用于中止当前请求 */
  const activeController = ref<AbortController | null>(null)
  /** 消息滚动容器引用 */
  const chatContainer = ref<HTMLElement | null>(null)

  /** 初始欢迎语 */
  const initialText = options.initialAssistantMessage || "你好，我是你的 AI 个人助手。你现在想做什么？"
  /** 初始消息列表（纯函数） */
  const initialHistory = (): ChatMessage[] => [{ id: nowId(), role: "assistant", content: initialText, status: "success" }]

  /** 消息列表（响应式数组） */
  const chatHistory = reactive<ChatMessage[]>([])
  ;(async () => {
    try {
      const saved = await loadChatHistory<ChatMessage[]>("history")
      if (saved && saved.length > 0) chatHistory.splice(0, chatHistory.length, ...saved)
      if (chatHistory.length === 0) chatHistory.splice(0, chatHistory.length, ...initialHistory())
    } catch {
      if (chatHistory.length === 0) chatHistory.splice(0, chatHistory.length, ...initialHistory())
    }
  })()

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

  /** 智能滚动：只有当用户停留在底部（或距离底部很近）时，才会自动滚动，防止打断用户向上阅读 */
  const scrollToBottomIfNearBottom = async () => {
    if (!chatContainer.value) return
    const el = chatContainer.value
    // 在 DOM 更新前判断是否接近底部 (容差 150px)
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 150
    await nextTick()
    if (isNearBottom) {
      el.scrollTop = el.scrollHeight
    }
  }

  /** 组装请求 payload（纯函数） */
  const buildRequestPayload = (message: string, messages: ChatMessage[]): ChatRequestPayload => ({
    message,
    history: [options.systemPrompt, ...messages.map((m) => ({ role: m.role, content: m.content }))],
    temperature: 0.7,
  })

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

    const payload = buildRequestPayload(message, visibleHistory.value)

    chatHistory.push(createUserMessage(message))
    const assistantMsg = reactive(createAssistantMessage("streaming")) as ChatMessage
    chatHistory.push(assistantMsg)

    inputText.value = ""
    isSending.value = true
    await scrollToBottomNextTick()

    try {
      const controller = new AbortController()
      activeController.value = controller

      for await (const event of streamChat({ apiBase: options.apiBase, payload, signal: controller.signal })) {
        if (event.type === "status") {
          assistantMsg.streamPhase = event.phase
          assistantMsg.status = "streaming"
          await scrollToBottomIfNearBottom()
          continue
        }

        if (event.type === "context") {
          assistantMsg.retrievedContext = event.retrievedContext
          await scrollToBottomIfNearBottom()
          continue
        }

        if (event.type === "reasoning") {
          assistantMsg.streamPhase = "thinking"
          let newContent = `${assistantMsg.thinkingContent || ""}${event.content}`
          // 如果这是思考阶段的开头，剔除前面的所有空白和换行符
          if (!assistantMsg.thinkingContent) {
            newContent = newContent.trimStart()
          }
          if (!newContent) continue
          assistantMsg.thinkingContent = newContent
          await scrollToBottomIfNearBottom()
          continue
        }

        if (event.type === "delta") {
          assistantMsg.streamPhase = "answering"
          let newRawContent = `${assistantMsg.rawContent || ""}${event.content}`
          // 如果这是回答阶段的开头，剔除前面的所有空白和换行符
          if (!assistantMsg.rawContent) {
            newRawContent = newRawContent.trimStart()
          }
          if (!newRawContent) continue
          assistantMsg.rawContent = newRawContent
          assistantMsg.content = stripThinkBlocks(assistantMsg.rawContent || "")
          assistantMsg.status = "streaming"
          await scrollToBottomIfNearBottom()
          continue
        }

        if (event.type === "error") {
          assistantMsg.status = "error"
          assistantMsg.content = event.error
          await scrollToBottomIfNearBottom()
          return
        }

        if (event.type === "done") {
          if (!assistantMsg.content.trim() && (assistantMsg.thinkingContent || "").trim()) {
            assistantMsg.content = assistantMsg.thinkingContent?.trim() || ""
          }
          assistantMsg.streamPhase = "answering"
          assistantMsg.status = assistantMsg.status === "error" ? "error" : "success"
          await scrollToBottomIfNearBottom()
          return
        }
      }

      assistantMsg.status = assistantMsg.status === "error" ? "error" : "success"
      await scrollToBottomIfNearBottom()
    } catch (e: any) {
      if (e?.name === "AbortError") {
        assistantMsg.status = assistantMsg.content ? "success" : "error"
        assistantMsg.streamPhase = assistantMsg.content ? "answering" : "thinking"
        if (!assistantMsg.content) {
          assistantMsg.content = assistantMsg.thinkingContent?.trim() || "已停止生成"
        }
      } else {
        assistantMsg.status = "error"
        assistantMsg.content =
          assistantMsg.content ||
          assistantMsg.thinkingContent?.trim() ||
          e?.message ||
          "请求异常"
      }
      await scrollToBottomIfNearBottom()
    } finally {
      isSending.value = false
      activeController.value = null
      try {
        await saveChatHistory("history", chatHistory)
      } catch {
        /* no-op */
      }
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
