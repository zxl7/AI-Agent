import { defineStore } from "pinia"
import { ref, reactive, computed } from "vue"
import type { ChatMessage } from "../types"

export const useChatStore = defineStore("chat", () => {
  /** 输入框内容（与 UI 双向绑定） */
  const inputText = ref<string>("")
  /** 当前是否处于流式生成中 */
  const isSending = ref<boolean>(false)
  /** 消息列表（对话上下文 + 渲染源数据） */
  const chatHistory = reactive<ChatMessage[]>([])

  /** 是否进入对话模式（用于页面布局切换） */
  const isChatMode = computed(() => isSending.value || chatHistory.some((m) => m.role === "user"))

  /**
   * 设置发送/生成状态（副作用：写入 store）。
   */
  const setSending = (v: boolean) => {
    isSending.value = v
  }

  /**
   * 设置输入框内容（副作用：写入 store）。
   */
  const setInput = (v: string) => {
    inputText.value = v
  }

  /**
   * 重置消息列表为指定初始值（副作用：修改 reactive 数组）。
   */
  const resetHistory = (initial: ChatMessage[]) => {
    chatHistory.splice(0, chatHistory.length, ...initial)
  }

  return {
    inputText,
    isSending,
    chatHistory,
    isChatMode,
    setSending,
    setInput,
    resetHistory,
  }
})
