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
      @update:model-value="(v) => emit('update:modelValue', String(v))"
      @keydown.enter.exact.prevent="onEnterSend"
    />

    <div class="composer-actions">
      <el-button
        :type="props.canStop && props.isSending ? 'danger' : 'primary'"
        round
        class="send-btn"
        :disabled="props.canStop && props.isSending ? false : !props.modelValue"
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

.send-btn {
  min-width: 88px;
}
</style>

