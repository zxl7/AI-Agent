<script setup lang="ts">
</script>

<template>
  <el-header class="top-toolbar">
    <div class="toolbar-actions">
      <el-button text circle>
        <el-icon :size="20">
          <Document />
        </el-icon>
      </el-button>
      <el-button text circle>
        <el-icon :size="20">
          <Present />
        </el-icon>
      </el-button>
      <el-button text circle>
        <el-icon :size="20">
          <Bell />
        </el-icon>
      </el-button>
      <el-button round class="action-btn">
        <el-icon :size="16">
          <Download />
        </el-icon> 下载
      </el-button>
      <el-button round class="action-btn coin-btn">
        <el-icon :size="16">
          <Coin />
        </el-icon> 987
      </el-button>
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