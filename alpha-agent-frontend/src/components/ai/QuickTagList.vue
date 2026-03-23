<script setup lang="ts">
import { resolveComponent } from "vue"

export type QuickTag = {
  label: string
  icon?: string
  color?: string
  isFill?: boolean
}

const props = defineProps<{
  tags: QuickTag[]
}>()

const emit = defineEmits<{
  (e: "select", label: string): void
}>()

/**
 * 点击某个快捷标签后触发选择事件（副作用：emit）。
 */
const selectTag = (tag: QuickTag) => {
  emit("select", tag.label)
}
</script>

<template>
  <div class="quick-tags">
    <div
      v-for="tag in props.tags"
      :key="tag.label"
      class="tag-item"
      :class="{ 'is-fill': tag.isFill }"
      @click="selectTag(tag)"
    >
      <el-icon v-if="tag.icon" :style="{ color: tag.color, width: '18px', height: '18px' }">
        <component :is="resolveComponent(tag.icon)" />
      </el-icon>
      <span class="tag-text">{{ tag.label }}</span>
    </div>
  </div>
</template>

<style scoped>
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
</style>

