import { computed, nextTick, ref } from "vue"
import { streamChat, stripThinkBlocks } from "../api/chat"
import { useChatStore } from "../stores/chat"
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
  status,
})

/**
 * 组合式对话助手：集中管理消息状态、SSE 流式接收、终止生成与滚动。
 * - 业务副作用仅集中在 send/stop/reset 中，便于测试与复用
 * - 其余为纯函数或计算属性，符合函数式与单一职责的拆分思路
 */
export const useChatAssistant = (options: Options) => {
  const store = useChatStore()
  /** 输入框内容（接入 Pinia） */
  const inputText = store.inputText
  /** 是否正在请求/流式生成中（接入 Pinia） */
  const isSending = store.isSending
  /** 用于中止当前请求 */
  const activeController = ref<AbortController | null>(null)
  /** 消息滚动容器引用 */
  const chatContainer = ref<HTMLElement | null>(null)

  /** 初始欢迎语 */
  const initialText = options.initialAssistantMessage || "你好，我是你的 AI 个人助手。你现在想做什么？"
  /** 初始消息列表（纯函数） */
  const initialHistory = (): ChatMessage[] => [{ id: nowId(), role: "assistant", content: initialText, status: "success" }]

  /** 消息列表：由 Pinia 统一管理 */
  const chatHistory = store.chatHistory
  ;(async () => {
    try {
      const saved = await loadChatHistory<ChatMessage[]>("history")
      if (saved && saved.length > 0) {
        store.resetHistory(saved)
      } else if (chatHistory.length === 0) {
        store.resetHistory(initialHistory())
      }
    } catch {
      if (chatHistory.length === 0) {
        store.resetHistory(initialHistory())
      }
    }
  })()

  /** 可作为上下文发送的历史（排除 streaming 占位消息） */
  const visibleHistory = computed(() => chatHistory.filter((m) => m.status !== "streaming"))
  /** 是否进入对话模式（用于布局切换） */
  const isChatMode = store.isChatMode

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
    const assistantMsg = createAssistantMessage("streaming")
    chatHistory.push(assistantMsg)

    inputText.value = ""
    store.setSending(true)
    await scrollToBottomNextTick()

    try {
      const controller = new AbortController()
      activeController.value = controller
      for await (const event of streamChat({ apiBase: options.apiBase, payload, signal: controller.signal })) {
        if (event.type === "delta") {
          assistantMsg.rawContent = (assistantMsg.rawContent || "") + event.content
          assistantMsg.content = stripThinkBlocks(assistantMsg.rawContent || "")
          await scrollToBottomNextTick()
          continue
        }

        if (event.type === "error") {
          assistantMsg.status = "error"
          assistantMsg.content = event.error
          await scrollToBottomNextTick()
          return
        }

        if (event.type === "done") {
          assistantMsg.status = assistantMsg.status === "error" ? "error" : "success"
          await scrollToBottomNextTick()
          return
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
      store.setSending(false)
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
