<script setup lang="ts">
import { onMounted, reactive, resolveComponent } from "vue"
import { useChatAssistant, type ChatHistoryItem } from "../../composables/useChatAssistant"
import { renderMarkdown } from "../../utils/markdown"

// 快捷指令
const quickTags = reactive([
  { label: "定时任务", icon: "Timer", color: "#ff9800", isFill: false },
  { label: "制作网页", icon: "Monitor", color: "#00c853", isFill: true },
  { label: "调研报告", icon: "Document", color: "#7c4dff", isFill: false },
  { label: "AI PPT", icon: "DataLine", color: "#2196f3", isFill: false },
  { label: "更多", icon: "", color: "#333", isFill: false },
])

// 专家套组
const expertList = reactive([
  {
    name: "办公",
    bg: "linear-gradient(135deg, #e8f5e9, #fbe9e7)",
    textColor: "#333",
    imgClass: "bg-office",
  },
  {
    name: "金融",
    bg: "linear-gradient(135deg, #e3f2fd, #bbdefb)",
    textColor: "#333",
    imgClass: "bg-finance",
  },
  {
    name: "编程",
    bg: "linear-gradient(135deg, #2b2b2b, #1a1a1a)",
    textColor: "#fff",
    imgClass: "bg-code",
  },
])

// 输入文本
const apiBase = import.meta.env.VITE_API_BASE || "http://localhost:3001"

const systemPrompt: ChatHistoryItem = {
  role: "system",
  content:
    "你是一个中文 AI 个人助手。目标：高效、可靠、可执行。风格：简洁清晰、先结论后细节；必要时给出步骤与可复制的示例；不确定时先澄清关键前提并给出默认方案。对代码相关问题：优先给出可运行的实现与边界条件。",
}

const { inputText, chatHistory, chatContainer, isSending, isChatMode, send, stopGenerating, applyQuickTag, resetConversation, scrollToBottom } =
  useChatAssistant({ apiBase, systemPrompt })

onMounted(() => scrollToBottom())
</script>

<template>
  <el-main class="main-content" :class="{ 'is-chat-mode': isChatMode }">
    <div class="center-container" :class="{ 'is-chat-mode': isChatMode }">
      <template v-if="!isChatMode">
        <h1 class="main-title">AI Agent, 让你的工作更轻松</h1>

        <div class="search-panel">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="4"
            resize="none"
            placeholder="请输入任务，然后交给 AI Agent（Enter 发送）"
            class="custom-textarea"
            @keydown.enter.exact.prevent="send"
          />
          <div class="composer-actions">
            <el-button type="info" round class="send-btn" :disabled="!inputText || isSending" @click="send">
              发送
            </el-button>
          </div>
        </div>

        <div class="quick-tags">
          <div
            v-for="tag in quickTags"
            :key="tag.label"
            class="tag-item"
            :class="{ 'is-fill': tag.isFill }"
            @click="applyQuickTag(tag.label)"
          >
            <el-icon v-if="tag.icon" :style="{ color: tag.color, width: '18px', height: '18px' }">
              <component :is="resolveComponent(tag.icon)" />
            </el-icon>
            <span class="tag-text">{{ tag.label }}</span>
          </div>
        </div>

        <div class="expert-suites">
          <div class="section-header">
            <h3>专家套组</h3>
          </div>

          <el-row :gutter="20" class="expert-cards">
            <el-col :span="8" v-for="expert in expertList" :key="expert.name">
              <div class="expert-card" :style="{ background: expert.bg, color: expert.textColor || '#333' }">
                <div class="card-content" :class="expert.imgClass"></div>
                <div class="card-title">{{ expert.name }}</div>
              </div>
            </el-col>
          </el-row>
        </div>
      </template>

      <template v-else>
        <div class="chat-mode-header">
          <div class="chat-mode-title">AI个人助手</div>
          <el-button text class="chat-mode-sub" @click="resetConversation">
            新对话
          </el-button>
        </div>

        <div class="chat-shell">
          <div ref="chatContainer" class="chat-scroll">
            <div class="message-list">
              <div v-for="msg in chatHistory" :key="msg.id" class="message-item" :class="`msg-${msg.role}`">
                <template v-if="msg.role === 'user'">
                  <div class="msg-bubble user-bubble">{{ msg.content }}</div>
                </template>
                <template v-else>
                  <div v-if="msg.status === 'streaming'" class="msg-status">
                    <span class="status-text">正在生成中…</span>
                    <el-button text size="small" class="status-stop" @click="stopGenerating">停止</el-button>
                  </div>
                  <div v-else-if="msg.status === 'error'" class="msg-status is-error">
                    <span class="status-text">生成失败</span>
                  </div>
                  <div class="msg-bubble ai-bubble markdown-body" v-html="renderMarkdown(msg.content)"></div>
                </template>
              </div>
            </div>
          </div>

          <div class="composer">
            <div class="search-panel">
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="3"
                resize="none"
                placeholder="请输入你的需求，按「Enter」发送"
                class="custom-textarea"
                @keydown.enter.exact.prevent="send"
              />
              <div class="composer-actions">
                <el-button
                  :type="isSending ? 'danger' : 'info'"
                  round
                  class="send-btn"
                  :disabled="isSending ? false : !inputText"
                  @click="isSending ? stopGenerating() : send()"
                >
                  <span v-if="isSending">停止</span>
                  <span v-else>发送</span>
                </el-button>
              </div>
            </div>
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

/* 搜索框 */
.search-panel {
  width: 100%;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #eaeaea;
  display: flex;
  flex-direction: column;
  margin-bottom: 24px;
}

:deep(.custom-textarea .ep-textarea__inner) {
  border: none !important;
  box-shadow: none !important;
  padding: 20px 24px !important;
  font-size: 16px !important;
  line-height: 1.6;
  background: transparent !important;
  min-height: 96px !important;
  width: 100%;
  resize: none;
  outline: none !important;
}

:deep(.custom-textarea.ep-textarea) {
  --ep-input-focus-border-color: transparent;
  --ep-input-border-color: transparent;
  --ep-input-hover-border-color: transparent;
}

/* 快捷标签 */
.quick-tags {
  display: flex;
  gap: 12px;
  margin: 12px 0 24px;
  flex-wrap: wrap;
  justify-content: center;
}

.tag-item {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tag-item:hover {
  background: #fcfcfc;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transform: translateY(-1px);
}

.tag-item.is-fill {
  background: #f6f8fa;
  border-color: #f0f2f5;
}

.tag-item.is-fill:hover {
  background: #f0f2f5;
}

.tag-text {
  font-size: 16px;
  color: #333;
  font-weight: 500;
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

.message-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 0 2px;
}

.message-item {
  display: flex;
  flex-direction: column;
}

.message-item.msg-user {
  align-items: flex-end;
}

.message-item.msg-assistant {
  align-items: flex-start;
}

.msg-bubble {
  max-width: 80%;
  border-radius: 14px;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.user-bubble {
  background: #2b2b2b;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.ai-bubble {
  background: #f6f8fa;
  color: #111;
  border-bottom-left-radius: 4px;
}

.markdown-body {
  white-space: normal;
}

.markdown-body :deep(p) {
  margin: 8px 0;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  margin: 12px 0 8px;
  line-height: 1.25;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.markdown-body :deep(li) {
  margin: 4px 0;
}

.markdown-body :deep(blockquote) {
  margin: 10px 0;
  padding: 8px 12px;
  border-left: 3px solid #d7dde8;
  background: rgba(0, 0, 0, 0.02);
  color: #334155;
}

.markdown-body :deep(pre) {
  margin: 10px 0;
  padding: 12px 14px;
  background: #0b1220;
  color: #e5e7eb;
  border-radius: 12px;
  overflow: auto;
}

.markdown-body :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.95em;
}

.markdown-body :deep(p > code),
.markdown-body :deep(li > code),
.markdown-body :deep(blockquote > code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 8px;
}

.markdown-body :deep(a) {
  color: #2563eb;
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.msg-status {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #666;
  margin: 2px 0 8px;
}

.msg-status.is-error {
  color: #d03050;
}

.status-stop {
  padding: 0;
}

.composer {
  width: 100%;
}

.composer-actions {
  display: flex;
  justify-content: flex-end;
  padding: 0 16px 14px;
}

.send-btn {
  min-width: 88px;
}

/* 专家套组 */
.expert-suites {
  width: 100%;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.expert-cards {
  display: flex;
  margin: 0 -10px;
}

.expert-card {
  border-radius: 16px;
  padding: 24px;
  height: 180px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.expert-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  position: relative;
  z-index: 2;
}

.card-content {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-size: cover;
  background-position: center;
  opacity: 0.8;
  z-index: 1;
}

@media (max-width: 960px) {
  .center-container {
    padding: 0 20px;
  }
}
</style>
