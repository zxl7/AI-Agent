<script setup lang="ts">
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
</script>

<template>
  <div class="message-item" :class="`msg-${props.message.role}`">
    <template v-if="props.message.role === 'user'">
      <div class="msg-bubble user-bubble">{{ props.message.content }}</div>
    </template>
    <template v-else>
      <div v-if="props.message.status === 'streaming'" class="msg-status">
        <span class="status-text">正在生成中…</span>
        <el-button text size="small" class="status-stop" @click="requestStop">停止</el-button>
      </div>
      <div v-else-if="props.message.status === 'error'" class="msg-status is-error">
        <span class="status-text">生成失败</span>
      </div>
      <div class="msg-bubble ai-bubble markdown-body" v-html="props.renderMarkdown(props.message.content)"></div>
      
      <!-- 知识库命中结果展示 -->
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
