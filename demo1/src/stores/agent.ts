import { defineStore } from "pinia"
import { ref } from "vue"

export type AgentMode = "chat" | "rag" | "workflow"

export const useAgentStore = defineStore("agent", () => {
  const mode = ref<AgentMode>("chat")

  const setMode = (v: AgentMode) => {
    mode.value = v
  }

  return { mode, setMode }
})
