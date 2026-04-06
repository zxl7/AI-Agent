<script setup lang="ts">
import { computed, ref, watch } from "vue"
import type { ChatMessage } from "../../types"

const props = defineProps<{
  message: ChatMessage
  renderMarkdown: (source: string) => string
}>()

const emit = defineEmits<{
  (e: "stop"): void
}>()

/**
 * 触发停止生成（副作用：emit）。
 */
const requestStop = () => {
  emit("stop")
}

const isThinkingExpanded = ref(true)

watch(
  () => props.message.streamPhase,
  (phase) => {
    if (phase === "answering" && (props.message.content || "").trim().length > 0) {
      isThinkingExpanded.value = false
    }
  },
  { immediate: true }
)

/**
 * 切换思考面板展开状态（副作用：更新局部 UI 状态）。
 */
const toggleThinkingPanel = () => {
  isThinkingExpanded.value = !isThinkingExpanded.value
}

/**
 * 是否展示答案气泡（纯函数派生）。
 */
const shouldShowAnswerBubble = computed(() => props.message.content.trim().length > 0)

/**
 * 是否展示答案承载区域（纯函数派生）。
 */
const shouldShowAnswerShell = computed(() => {
  if (shouldShowAnswerBubble.value) return true
  return props.message.status === "streaming" && props.message.streamPhase === "answering"
})

/**
 * 流式阶段优先以纯文本渲染，避免不完整 markdown 反复解析导致闪烁。
 */
const shouldRenderStreamingPlainText = computed(() => {
  return props.message.status === "streaming" && shouldShowAnswerBubble.value
})

/**
 * 是否展示思考过程面板（纯函数派生）。
 */
const shouldShowThinkingPanel = computed(() => {
  if (props.message.role !== "assistant") return false
  if ((props.message.thinkingContent || "").trim().length > 0) return true
  return props.message.status === "streaming" && !shouldShowAnswerBubble.value
})

/**
 * 当前流式阶段对应的状态文案（纯函数派生）。
 */
const streamingStatusText = computed(() => {
  if (props.message.streamPhase === "answering") return "正在输出答案…"
  return "思考中…"
})

/**
 * 思考内容摘要（纯函数派生）。
 */
const thinkingSummary = computed(() => {
  const content = (props.message.thinkingContent || "").trim()
  if (!content) return "正在结合知识库检索并思考中…"
  if (content.length <= 120) return content
  return `${content.slice(0, 120)}…`
})
</script>

<template>
  <div class="message-item" :class="`msg-${props.message.role}`">
    <template v-if="props.message.role === 'user'">
      <div class="msg-bubble user-bubble">{{ props.message.content }}</div>
    </template>
    <template v-else>
      <div v-if="props.message.status === 'streaming'" class="msg-status">
        <span class="status-text">{{ streamingStatusText }}</span>
        <el-button text size="small" class="status-stop" @click="requestStop">停止</el-button>
      </div>
      <div v-else-if="props.message.status === 'error'" class="msg-status is-error">
        <span class="status-text">生成失败</span>
      </div>

      <div v-if="shouldShowThinkingPanel" class="thinking-panel">
        <button type="button" class="thinking-header" @click="toggleThinkingPanel">
          <div class="thinking-title-wrap">
            <span class="thinking-dot"></span>
            <span class="thinking-title">思考过程</span>
          </div>
          <span class="thinking-toggle">{{ isThinkingExpanded ? "收起" : "展开" }}</span>
        </button>
        <div v-if="isThinkingExpanded" class="thinking-content">
          {{ props.message.thinkingContent?.trim() || "正在结合知识库检索并思考中…" }}
        </div>
        <div v-else class="thinking-summary">
          {{ thinkingSummary }}
        </div>
      </div>

      <div
        v-if="shouldShowAnswerShell"
        class="msg-bubble ai-bubble markdown-body"
        :class="{ 'is-streaming': props.message.status === 'streaming', 'is-placeholder': !shouldShowAnswerBubble }"
      >
        <template v-if="!shouldShowAnswerBubble">
          <p>正在整理答案…</p>
        </template>
        <template v-else-if="shouldRenderStreamingPlainText">
          <div class="streaming-plain-text">{{ props.message.content }}</div>
        </template>
        <template v-else>
          <div v-html="props.renderMarkdown(props.message.content)"></div>
        </template>
      </div>

      <div v-if="props.message.retrievedContext && props.message.retrievedContext.length > 0" class="retrieved-context-box">
        <div class="context-title">
          <el-icon><Document /></el-icon>
          <span>命中本地知识库 ({{ props.message.retrievedContext.length }}条)</span>
        </div>
        <div class="context-list">
          <div v-for="(ctx, idx) in props.message.retrievedContext" :key="idx" class="context-item">
            <div class="context-text">{{ ctx.pageContent }}</div>
            <div class="context-meta" v-if="ctx.metadata && Object.keys(ctx.metadata).length > 0">
              <el-tag size="small" type="info">{{ ctx.metadata.source || '未知来源' }}</el-tag>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
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

.ai-bubble.is-placeholder {
  color: #6b7280;
}

.markdown-body {
  white-space: normal;
}

.streaming-plain-text {
  white-space: pre-wrap;
  word-break: break-word;
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

.thinking-panel {
  width: 100%;
  max-width: 80%;
  margin-bottom: 10px;
  border-radius: 12px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  box-sizing: border-box;
  overflow: hidden;
}

.thinking-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
}

.thinking-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.thinking-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #f97316;
  box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.14);
}

.thinking-title {
  color: #c2410c;
  font-size: 12px;
  font-weight: 600;
}

.thinking-toggle {
  color: #9a3412;
  font-size: 12px;
}

.thinking-content {
  padding: 0 12px 12px;
  color: #9a3412;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.thinking-summary {
  padding: 0 12px 12px;
  color: #9a3412;
  font-size: 12px;
  line-height: 1.6;
}

:deep(.status-stop) {
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid rgba(208, 48, 80, 0.25);
  color: #d03050;
  background: #fff;
}

:deep(.status-stop:hover) {
  background: rgba(208, 48, 80, 0.06);
}

.retrieved-context-box {
  margin-top: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  width: 100%;
  max-width: 80%;
  box-sizing: border-box;
}

.ai-bubble.is-streaming :deep(*:last-child)::after,
.ai-bubble.is-streaming::after {
  content: "▍";
  display: inline-block;
  margin-left: 2px;
  color: #2563eb;
  animation: blink-cursor 1s steps(1) infinite;
}

@keyframes blink-cursor {
  0%,
  50% {
    opacity: 1;
  }
  50.01%,
  100% {
    opacity: 0;
  }
}

.context-title {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 8px;
}

.context-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.context-item {
  background: #ffffff;
  border: 1px solid #f1f5f9;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 13px;
  color: #475569;
  line-height: 1.5;
}

.context-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.context-meta {
  margin-top: 6px;
  display: flex;
  justify-content: flex-end;
}
</style>
