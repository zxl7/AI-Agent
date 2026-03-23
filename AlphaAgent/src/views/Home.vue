<script setup lang="ts">
import Sidebar from "../components/layout/Sidebar.vue"
import Header from "../components/layout/Header.vue"
import MainContent from "../components/layout/MainContent.vue"
</script>

<template>
  <el-container class="home-shell">
    <!-- 左侧边栏 -->
    <Sidebar />
    <el-container class="main-shell">
      <Header />
      <MainContent />
    </el-container>
  </el-container>
</template>

<style scoped>
.home-shell {
  height: 100vh;
  display: flex;
  width: 100%;
}

/* 主区域 */
.main-shell {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}
</style>
