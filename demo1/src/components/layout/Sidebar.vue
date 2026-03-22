<script setup lang="ts">
import { reactive, resolveComponent } from "vue"

// 左侧菜单数据
const mainMenus = reactive([
  { label: "新建任务", icon: "Plus", active: true },
  { label: "搜索", icon: "Search" },
  { label: "资产", icon: "Folder" },
  { label: "画廊", icon: "Picture" },
])
</script>

<template>
  <aside class="left-nav">
    <div class="nav-top">
      <div class="brand">
        <div class="brand-logo">
          <img src="/vite.svg" alt="logo" />
        </div>
        <div class="brand-title">个人助手</div>
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

    <div class="nav-bottom">
      <div class="user-info">
        <el-avatar :size="32" class="user-avatar">
          <img src="@/assets/avatar.png" alt="avatar" class="info-avatar" />
        </el-avatar>
        <div class="user-detail">
          <div class="user-name">
            三人行
            <span class="badge-pro">🛴</span>
          </div>
          <div class="user-desc">免费</div>
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
/* 左侧边栏 */
.left-nav {
  width: 260px;
  background: #fcfcfc;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.info-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
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

.brand-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
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

@media (max-width: 960px) {
  .left-nav {
    display: none;
  }
}
</style>
