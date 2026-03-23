<script setup lang="ts">
export type ExpertSuite = {
  name: string
  bg: string
  textColor?: string
  imgClass?: string
}

const props = defineProps<{
  title?: string
  list: ExpertSuite[]
}>()
</script>

<template>
  <div class="expert-suites">
    <div class="section-header">
      <h3>{{ props.title || "专业组件" }}</h3>
    </div>

    <el-row :gutter="20" class="expert-cards">
      <el-col :span="8" v-for="expert in props.list" :key="expert.name">
        <div class="expert-card" :style="{ background: expert.bg, color: expert.textColor || '#333' }">
          <div class="card-content" :class="expert.imgClass"></div>
          <div class="card-title">{{ expert.name }}</div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
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

.expert-cards {
  display: flex;
  justify-content: center;
  margin: 0 -10px;
}

.expert-card {
  border-radius: 16px;
  padding: 24px;
  height: 80px;
  width: 240px;
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
</style>

