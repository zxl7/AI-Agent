import { defineStore } from "pinia"
import { ref, reactive, computed } from "vue"
import type { ChatMessage } from "../composables/useChatAssistant"

export const useChatStore = defineStore("chat", () => {
  const inputText = ref<string>("")
  const isSending = ref<boolean>(false)
  const chatHistory = reactive<ChatMessage[]>([])

  const isChatMode = computed(() => isSending.value || chatHistory.some((m) => m.role === "user"))

  const setSending = (v: boolean) => {
    isSending.value = v
  }

  const setInput = (v: string) => {
    inputText.value = v
  }

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
