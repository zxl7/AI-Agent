<script setup lang="ts">
import { onMounted } from "vue"
import { useChatAssistant, type ChatHistoryItem } from "../../composables/useChatAssistant"
import ChatInputPanel from "../ai/ChatInputPanel.vue"
import ChatMessageList from "../ai/ChatMessageList.vue"
import ExpertSuiteList from "../ai/ExpertSuiteList.vue"
import QuickTagList from "../ai/QuickTagList.vue"

const quickTags = [
  { label: "定时任务", icon: "Timer", color: "#ff9800", isFill: false },
  { label: "调研报告", icon: "Document", color: "#7c4dff", isFill: false },
  { label: "AI PPT", icon: "DataLine", color: "#2196f3", isFill: false },
  { label: "更多", icon: "", color: "#333", isFill: false },
] as const

const expertList = [
  {
    name: "办公",
    bg: "#f8fafc",
    textColor: "#333",
    imgClass: "bg-office",
  },
  {
    name: "金融",
    bg: "#eff6ff",
    textColor: "#333",
    imgClass: "bg-finance",
  },
  {
    name: "编程",
    bg: "#111827",
    textColor: "#fff",
    imgClass: "bg-code",
  },
] as const

// 输入文本
const apiBase = import.meta.env.VITE_API_BASE || "http://localhost:3000"

const systemPrompt: ChatHistoryItem = {
  role: "system",
  content:
    "你是一个中文 AI 个人助手。目标：高效、可靠、可执行。风格：简洁清晰、先结论后细节；必要时给出步骤与可复制的示例；不确定时先澄清关键前提并给出默认方案。对代码相关问题：优先给出可运行的实现与边界条件。",
}

const { inputText, chatHistory, chatContainer, isSending, isChatMode, send, stopGenerating, applyQuickTag, resetConversation, scrollToBottom } =
  useChatAssistant({ apiBase, systemPrompt })

/**
 * 更新输入框内容（副作用：写入 ref）。
 */
const updateInputText = (v: string) => {
  inputText.value = v
}

onMounted(() => scrollToBottom())
</script>

<template>
  <el-main class="main-content" :class="{ 'is-chat-mode': isChatMode }">
    <div class="center-container" :class="{ 'is-chat-mode': isChatMode }">
      <template v-if="!isChatMode">
        <h1 class="main-title">Alpha Agent 专业的投资助手</h1>

        <ChatInputPanel
          :model-value="inputText"
          :rows="4"
          placeholder="请输入任务，然后交给 Alpha Agent（Enter 发送）"
          :is-sending="isSending"
          @update:modelValue="updateInputText"
          @send="send"
        />

        <QuickTagList :tags="[...quickTags]" @select="applyQuickTag" />

        <ExpertSuiteList title="专业组件" :list="[...expertList]" />
      </template>

      <template v-else>
        <div class="chat-mode-header">
          <div class="chat-mode-title">Alpha Agent 专业的投资助手</div>
          <el-button text class="chat-mode-sub" @click="resetConversation">新对话</el-button>
        </div>

        <div class="chat-shell">
          <div ref="chatContainer" class="chat-scroll">
            <ChatMessageList :messages="chatHistory" @stop="stopGenerating" />
          </div>

          <div class="composer">
            <ChatInputPanel
              :model-value="inputText"
              :rows="3"
              placeholder="请输入你的需求，按「Enter」发送"
              :is-sending="isSending"
              :can-stop="true"
              @update:modelValue="updateInputText"
              @send="send"
              @stop="stopGenerating"
            />
          </div>
        </div>
      </template>
    </div>
  </el-main>
</template>

<style scoped>
/* 中间内容 */
.main-content {
  flex: 1;
  display: flex;
  justify-content: center;
  padding-top: 24px;
  overflow: hidden;
}

.main-content.is-chat-mode {
  padding-top: 0;
}

.center-container {
  width: 100%;
  max-width: 860px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 40px;
  height: 100%;
}

.center-container.is-chat-mode {
  align-items: stretch;
  padding: 0 24px 16px;
}

.main-title {
  font-size: 32px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1a1a1a;
}

.chat-mode-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 44px;
  padding: 8px 0;
}

.chat-mode-title {
  font-size: 16px;
  font-weight: 600;
  color: #111;
}

.chat-mode-sub {
  color: #666;
}

:deep(.chat-mode-sub) {
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #374151;
}

:deep(.chat-mode-sub:hover) {
  background: #e5e7eb;
}

.chat-shell {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.chat-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  width: 100%;
  padding: 8px 0;
}

.composer {
  width: 100%;
}

@media (max-width: 960px) {
  .center-container {
    padding: 0 20px;
  }
}
</style>
