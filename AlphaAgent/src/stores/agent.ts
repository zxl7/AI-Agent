import { defineStore } from "pinia"
import { ref } from "vue"

export type AgentMode = "chat" | "rag" | "workflow"

export const useAgentStore = defineStore("agent", () => {
  /** 当前工作台模式（用于跨页面共享状态） */
  const mode = ref<AgentMode>("chat")

  /**
   * 设置工作台模式（副作用：写入 store）。
   */
  const setMode = (v: AgentMode) => {
    mode.value = v
  }

  return { mode, setMode }
})
