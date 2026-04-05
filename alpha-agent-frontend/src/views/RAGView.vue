<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getVectorData, addVectorData } from '../api/vector'

const loading = ref(false)
const vectorData = ref<{ ids: string[], documents: string[], metadatas: any[] }>({
  ids: [],
  documents: [],
  metadatas: []
})

// 添加知识表单
const addDialogVisible = ref(false)
const newTexts = ref('')
const adding = ref(false)

/**
 * 获取知识库列表（纯函数分离副作用，在 mounted 触发）
 */
const fetchVectorData = async () => {
  loading.value = true
  try {
    const res = await getVectorData()
    if (res.success && res.data) {
      vectorData.value = res.data
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取知识库数据失败')
  } finally {
    loading.value = false
  }
}

/**
 * 提交新增知识
 */
const submitAdd = async () => {
  if (!newTexts.value.trim()) {
    ElMessage.warning('请输入要添加的文本知识')
    return
  }
  
  // 按行分割文本，过滤空行
  const textsArray = newTexts.value
    .split('\n')
    .map(t => t.trim())
    .filter(t => t.length > 0)
    
  if (textsArray.length === 0) return

  adding.value = true
  try {
    const res = await addVectorData({ texts: textsArray })
    if (res.success) {
      ElMessage.success('添加成功！')
      addDialogVisible.value = false
      newTexts.value = ''
      // 重新拉取数据
      await fetchVectorData()
    } else {
      ElMessage.error(res.message || '添加失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '添加失败')
  } finally {
    adding.value = false
  }
}

onMounted(() => {
  fetchVectorData()
})
</script>

<template>
  <el-main class="rag-container">
    <div class="rag-header">
      <h2>知识库管理</h2>
      <el-button type="primary" @click="addDialogVisible = true">新增知识片段</el-button>
    </div>

    <el-card class="rag-card" v-loading="loading">
      <el-empty v-if="vectorData.documents.length === 0" description="知识库目前为空" />
      <el-table v-else :data="vectorData.documents.map((doc, idx) => ({ id: vectorData.ids[idx], text: doc, meta: vectorData.metadatas[idx] }))" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="300" show-overflow-tooltip />
        <el-table-column prop="text" label="文本内容" min-width="400" />
        <el-table-column prop="meta" label="元数据" width="200">
          <template #default="{ row }">
            <el-tag size="small" type="info" v-if="row.meta && row.meta.source">
              {{ row.meta.source }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="addDialogVisible" title="新增知识片段" width="600px">
      <div style="margin-bottom: 8px; color: #666; font-size: 13px;">
        输入文本段落，每行将被视为一个独立的知识片段（Document）进行向量化存储。
      </div>
      <el-input
        v-model="newTexts"
        type="textarea"
        :rows="10"
        placeholder="例如：\nAlpha Agent 是一个智能体。\n每周五下午是团队下午茶时间。"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="adding" @click="submitAdd">
            确认添加
          </el-button>
        </span>
      </template>
    </el-dialog>
  </el-main>
</template>

<style scoped>
.rag-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.rag-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.rag-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.rag-card {
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
</style>

