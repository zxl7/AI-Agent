<script setup lang="ts">
import { reactive, resolveComponent } from "vue"

// 左侧菜单数据
const mainMenus = reactive([
  { label: "新建任务", icon: "Plus", active: true },
  { label: "搜索", icon: "Search" },
  { label: "资产", icon: "Folder" },
  { label: "画廊", icon: "Picture" },
])

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
</script>

<template>
  <el-container class="home-shell">
    <!-- 左侧边栏 -->
    <aside class="left-nav">
      <div class="nav-top">
        <div class="brand">
          <div class="brand-logo">
            <img src="/vite.svg" alt="logo" />
          </div>
          <el-button text circle size="small" class="collapse-btn">
            <el-icon>
              <Switch />
            </el-icon>
          </el-button>
        </div>

        <div class="menu-list">
          <div v-for="item in mainMenus" :key="item.label" class="menu-item" :class="{ 'is-active': item.active }">
            <el-icon :size="18" style="width: 12px">
              <component :is="resolveComponent(item.icon)" />
            </el-icon>
            <span>{{ item.label }}</span>
          </div>
        </div>

        <div class="menu-group">
          <div class="group-title">MiniMax实验室</div>
          <div class="menu-item">
            <el-icon :size="18">
              <Lightning />
            </el-icon>
            <span>MaxClaw</span>
            <span class="tag-new">New</span>
          </div>
        </div>

        <div class="menu-group">
          <div class="group-title">专家</div>
          <div class="menu-item">
            <el-icon :size="18">
              <User />
            </el-icon>
            <span>探索专家</span>
            <span class="tag-new">New</span>
          </div>
        </div>

        <div class="menu-group">
          <div class="group-title">
            任务记录
            <el-icon :size="14">
              <ArrowRight />
            </el-icon>
          </div>
          <div class="menu-item sub-item" @click="$router.push('/chat')">
            <span>测试</span>
          </div>
          <div class="menu-item sub-item"></div>
        </div>
      </div>
    </aside>

    <el-container class="main-shell">
      <el-main class="main-content">
        <div class="center-container">
          <h1 class="main-title">MiniMax Agent, 让你的工作更轻松</h1>

          <!-- 核心输入区 -->
          <div class="search-panel">
            <el-input type="textarea" :rows="4" resize="none" placeholder="请输入任务，然后交给 MiniMax Agent" class="custom-textarea" />
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
    </el-container>
  </el-container>
</template>

<style scoped>
.home-shell {
  height: 100vh;
  display: flex;
  width: 100%;
}

/* 左侧边栏 */
.left-nav {
  width: 260px;
  background: #fcfcfc;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.nav-top {
  padding: 16px;
}

.brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.brand-logo img {
  width: 32px;
  height: 32px;
  border-radius: 8px;
}

.collapse-btn {
  color: #666;
}

.menu-list {
  margin-bottom: 24px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  color: #333;
  cursor: pointer;
  font-size: 14px;
  margin-bottom: 4px;
}

.menu-item:hover {
  background: #f0f0f0;
}

.menu-item.is-active {
  background: #fff;
  font-weight: 500;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.menu-group {
  margin-bottom: 16px;
}

.group-title {
  font-size: 12px;
  color: #999;
  padding: 0 12px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.tag-new {
  font-size: 10px;
  background: #f0f0f0;
  color: #666;
  padding: 2px 6px;
  border-radius: 10px;
  margin-left: auto;
}

.sub-item {
  padding-left: 36px;
}

.nav-bottom {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-detail {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.badge-pro {
  font-size: 12px;
}

.user-desc {
  font-size: 12px;
  color: #999;
}

/* 主区域 */
.main-shell {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

.top-toolbar {
  height: 60px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 0 24px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  font-size: 13px !important;
}

.coin-btn {
  background: #f9f9f9 !important;
  border-color: #eee !important;
}

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

:deep(.custom-textarea .el-textarea__inner) {
  border: none !important;
  box-shadow: none !important;
  padding: 20px 24px !important;
  font-size: 16px !important;
  line-height: 1.6;
  background: transparent !important;
  min-height: 120px !important;
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
  /* 抵消 el-row 的 padding 影响，保证和上方对齐 */
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

/* 响应式 */
@media (max-width: 960px) {
  .left-nav {
    display: none;
  }

  .center-container {
    padding: 0 20px;
  }
}
</style>
