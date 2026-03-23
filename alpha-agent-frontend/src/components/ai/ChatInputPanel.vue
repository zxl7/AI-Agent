<script setup lang="ts">
type Props = {
  modelValue: string
  rows: number
  placeholder: string
  isSending: boolean
  canStop?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: "update:modelValue", v: string): void
  (e: "send"): void
  (e: "stop"): void
}>()

/**
 * 同步输入框值到父组件（副作用：emit）。
 */
const onUpdateModelValue = (v: string) => {
  emit("update:modelValue", v)
}

/**
 * 按下 Enter 触发发送（副作用：emit）。
 */
const onEnterSend = () => {
  emit("send")
}

/**
 * 点击主按钮：根据状态决定 send/stop（副作用：emit）。
 */
const onPrimaryClick = () => {
  if (props.canStop && props.isSending) {
    emit("stop")
    return
  }
  emit("send")
}
</script>

<template>
  <div class="search-panel">
    <el-input
      :model-value="props.modelValue"
      type="textarea"
      :rows="props.rows"
      resize="none"
      :placeholder="props.placeholder"
      class="custom-textarea"
      @update:modelValue="onUpdateModelValue"
      @keydown.enter.exact.prevent="onEnterSend"
    />

    <div class="composer-actions">
      <el-button
        :type="props.canStop && props.isSending ? 'danger' : 'primary'"
        round
        class="send-btn"
        :class="{ 'is-stop': props.canStop && props.isSending }"
        :disabled="props.canStop && props.isSending ? false : !props.modelValue.trim()"
        @click="onPrimaryClick"
      >
        <span v-if="props.canStop && props.isSending">停止</span>
        <span v-else>发送</span>
      </el-button>
    </div>
  </div>
</template>

<style scoped>
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
  width: 100%;
  resize: none;
  outline: none !important;
}

:deep(.custom-textarea.ep-textarea) {
  --ep-input-focus-border-color: transparent;
  --ep-input-border-color: transparent;
  --ep-input-hover-border-color: transparent;
}

.composer-actions {
  display: flex;
  justify-content: flex-end;
  padding: 0 16px 14px;
}

:deep(.send-btn) {
  height: 38px;
  min-width: 104px;
  padding: 0 14px;
  border-radius: 999px;
  font-weight: 600;
  letter-spacing: 0.2px;
  border: none;
  background: #2563eb;
  color: #fff;
  box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease,
    background-color 0.12s ease;
}

:deep(.send-btn:hover) {
  background: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.28);
}

:deep(.send-btn:active) {
  background: #1e40af;
  transform: translateY(0);
  box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
}

:deep(.send-btn:focus-visible) {
  outline: none;
  box-shadow:
    0 0 0 3px rgba(37, 99, 235, 0.28),
    0 10px 22px rgba(37, 99, 235, 0.22);
}

:deep(.send-btn.is-disabled) {
  background: #e5e7eb;
  color: #9ca3af;
  box-shadow: none;
}

:deep(.send-btn.is-stop) {
  background: #fff;
  color: #d03050;
  border: 1px solid rgba(208, 48, 80, 0.25);
  box-shadow: 0 10px 24px rgba(208, 48, 80, 0.12);
}

:deep(.send-btn.is-stop:hover) {
  filter: none;
  box-shadow: 0 14px 30px rgba(208, 48, 80, 0.16);
}
</style>
