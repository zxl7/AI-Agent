<script setup lang="ts">
import { ref, reactive, resolveComponent } from "vue"

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
const inputText = ref("")
</script>

<template>
  <el-main class="main-content">
    <div class="center-container">
      <h1 class="main-title">MiniMax Agent, 让你的工作更轻松</h1>

      <!-- 核心输入区 -->
      <div class="search-panel">
        <el-input v-model="inputText" type="textarea" :rows="4" resize="none" placeholder="请输入任务，然后交给 MiniMax Agent" class="custom-textarea" />
      </div>

      <!-- 快捷标签 -->
      <div class="quick-tags">
        <div v-for="tag in quickTags" :key="tag.label" class="tag-item" :class="{ 'is-fill': tag.isFill }">
          <el-icon v-if="tag.icon" :style="{ color: tag.color, width: '18px', height: '18px' }">
            <component :is="resolveComponent(tag.icon)" />
          </el-icon>
          <span class="tag-text">{{ tag.label }}</span>
        </div>
      </div>

      <!-- 专家套组 -->
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
    </div>
  </el-main>
</template>

<style scoped>
/* 中间内容 */
.main-content {
  flex: 1;
  display: flex;
  justify-content: center;
  padding-top: 60px;
  overflow-y: auto;
}

.center-container {
  width: 100%;
  max-width: 860px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 40px;
}

.main-title {
  font-size: 32px;
  font-weight: 600;
  margin-bottom: 40px;
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
  min-height: 120px !important;
  padding: 4px;
  resize: none;
  outline: none !important;
}

:deep(.custom-textarea.el-textarea) {
  --el-input-focus-border-color: transparent;
  --el-input-border-color: transparent;
  --el-input-hover-border-color: transparent;
}

/* 快捷标签 */
.quick-tags {
  display: flex;
  gap: 12px;
  margin-bottom: 60px;
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

.more-btn {
  font-size: 14px;
  color: #999;
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
