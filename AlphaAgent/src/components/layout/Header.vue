<script setup lang="ts"></script>

<template>
  <el-header class="top-toolbar">
    <div class="toolbar-actions">
      <el-icon :size="20" style="width: 18px">
        <Document />
      </el-icon>
      <el-icon :size="20" style="width: 18px">
        <Present />
      </el-icon>
      <el-icon :size="20" style="width: 18px">
        <Bell />
      </el-icon>
      <el-icon :size="20" style="width: 18px">
        <Download />
      </el-icon>
      <el-icon :size="20" style="width: 18px">
        <Coin />
      </el-icon>
    </div>
  </el-header>
</template>

<style scoped>
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
</style>
