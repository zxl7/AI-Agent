<script setup lang="ts">
import type { ChatMessage } from "../../types"
import ChatMessageItem from "./ChatMessageItem.vue"

const props = defineProps<{
  messages: ChatMessage[]
}>()

const emit = defineEmits<{
  (e: "stop"): void
}>()
</script>

<template>
  <div class="message-list">
    <ChatMessageItem
      v-for="msg in props.messages"
      :key="msg.id"
      :message="msg"
      @stop="emit('stop')"
    />
  </div>
</template>

<style scoped>
.message-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 0 2px;
}
</style>

