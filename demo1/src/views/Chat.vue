<script setup lang="ts">
import { reactive, resolveComponent, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 左侧菜单数据
const mainMenus = reactive([
  { label: '新建任务', icon: 'Plus' },
  { label: '搜索', icon: 'Search' },
  { label: '资产', icon: 'Folder' },
  { label: '画廊', icon: 'Picture' },
])

// 会话数据模拟
const chatHistory = reactive([
  {
    id: 1,
    role: 'user',
    content: '测试'
  },
  {
    id: 2,
    role: 'assistant',
    status: 'success',
    thinking: 'The user said "测试" which is Chinese for "test". This seems like they\'re just testing if I\'m working or responding. I should respond politely and let them know I\'m ready to help.',
    thinkTime: '1.59s',
    content: `你好！我是 MiniMax Agent，已准备就绪。

有什么我可以帮助你的吗？你可以：

- 提问或咨询问题
- 请求代码开发或网页制作
- 进行文件操作和分析
- 生成图片、视频或音频
- 研究和信息收集
- 创建文档和报告

请告诉我你的需求，我会尽力帮你完成。`
  }
])

const inputContent = ref('')
const chatContainer = ref<HTMLElement | null>(null)

// 自动滚动到底部
const scrollToBottom = () => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

onMounted(() => {
  scrollToBottom()
})

const handleNewTask = () => {
  router.push('/')
}
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
          <div v-for="item in mainMenus" :key="item.label" class="menu-item" @click="item.label === '新建任务' && handleNewTask()">
            <el-icon :size="18">
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
            任务记录 <el-icon :size="14">
              <ArrowRight />
            </el-icon>
          </div>
          <div class="menu-item sub-item is-active">
            <span>测试</span>
          </div>
          <div class="menu-item sub-item">
            <span>协鑫集成股票分析</span>
          </div>
        </div>
      </div>

      <div class="nav-bottom">
        <div class="user-info">
          <el-avatar :size="32" class="user-avatar">
            <img src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" />
          </el-avatar>
          <div class="user-detail">
            <div class="user-name">三人行 <span class="badge-pro">👑</span></div>
            <div class="user-desc">免费</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <el-container class="main-shell">
      <el-header class="chat-header">
        <div class="header-title">测试</div>
        <div class="header-actions">
          <el-button text circle><el-icon :size="20"><Plus /></el-icon></el-button>
          <el-button text class="share-btn">
            <el-icon class="el-icon--left"><Share /></el-icon> 分享
          </el-button>
        </div>
      </el-header>

      <el-main class="chat-content" ref="chatContainer">
        <div class="chat-flow-container">
          
          <!-- 快捷操作栏 (固定在最上方) -->
          <div class="chat-tools-bar">
            <el-button round size="small" class="tool-chip"><el-icon><Search /></el-icon> 深度调研</el-button>
            <el-button round size="small" class="tool-chip"><el-icon><Edit /></el-icon> 报告撰写</el-button>
            <el-button round size="small" class="tool-chip"><el-icon><DataBoard /></el-icon> PPT</el-button>
            <el-button round size="small" class="tool-chip"><el-icon><Document /></el-icon> docx 文档专家</el-button>
            <el-button round size="small" class="tool-chip"><el-icon><Files /></el-icon> pdf&docx文档专家</el-button>
          </div>

          <!-- 聊天记录区 -->
          <div class="message-list">
            <div v-for="msg in chatHistory" :key="msg.id" class="message-item" :class="`msg-${msg.role}`">
              <!-- 用户消息 -->
              <template v-if="msg.role === 'user'">
                <div class="msg-bubble user-bubble">
                  {{ msg.content }}
                </div>
                <div class="msg-actions user-actions">
                  <el-button text circle size="small"><el-icon><DocumentCopy /></el-icon></el-button>
                </div>
              </template>

              <!-- AI 消息 -->
              <template v-else>
                <div class="msg-status">
                  <span class="status-text">收到您的请求，我正在处理中。</span>
                </div>
                
                <div v-if="msg.thinking" class="msg-thinking">
                  <div class="thinking-header">
                    <span class="thinking-title">已思考 {{ msg.thinkTime }}</span>
                    <el-icon><ArrowDown /></el-icon>
                  </div>
                  <div class="thinking-content">
                    {{ msg.thinking }}
                  </div>
                </div>

                <div class="msg-bubble ai-bubble markdown-body">
                  <div style="white-space: pre-wrap;">{{ msg.content }}</div>
                </div>
              </template>
            </div>
          </div>

          <!-- 底部留白，防止输入框遮挡 -->
          <div class="bottom-spacer"></div>
        </div>
      </el-main>

      <!-- 底部固定输入区 -->
      <div class="chat-footer">
        <div class="footer-inner">
          <div class="context-files-bar">
            <el-button text size="small" class="files-btn">
              <el-icon><Document /></el-icon> 查看此任务中的所有文件
            </el-button>
          </div>
          <div class="chat-input-wrapper">
            <el-input 
              v-model="inputContent"
              type="textarea" 
              :rows="3" 
              resize="none" 
              placeholder="请输入你的需求，按「Enter」发送"
              class="chat-textarea" 
            />
            <div class="input-actions">
              <div class="actions-left">
                <el-button text circle><el-icon :size="20"><Paperclip /></el-icon></el-button>
                <el-button text circle><el-icon :size="20"><Switch /></el-icon></el-button>
                <el-button text circle><el-icon :size="20"><FullScreen /></el-icon></el-button>
              </div>
              <div class="actions-right">
                <el-button text class="model-select-btn">
                  <el-icon class="el-icon--left"><Setting /></el-icon>
                  全能
                </el-button>
                <el-button type="info" circle class="send-btn" :disabled="!inputContent">
                  <el-icon :size="20"><Top /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
          <div class="footer-disclaimer">
            内容由AI生成，重要信息请务必核查
          </div>
        </div>
      </div>
    </el-container>
  </el-container>
</template>

<style scoped>
.home-shell {
  height: 100vh;
  display: flex;
  width: 100%;
}

/* 左侧边栏复用样式 */
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
  background: #f0f0f0;
  font-weight: 500;
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

/* 主区域 - 聊天特有样式 */
.main-shell {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  position: relative;
}

.chat-header {
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background: #fff;
  z-index: 10;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.share-btn {
  font-size: 14px;
  color: #333;
}

.chat-content {
  flex: 1;
  padding: 0;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.chat-flow-container {
  width: 100%;
  max-width: 860px;
  margin: 0 auto;
  padding: 24px 40px;
  display: flex;
  flex-direction: column;
}

.chat-tools-bar {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 40px;
}

.tool-chip {
  color: #999;
  border-color: #eee;
  background: transparent;
}

/* 消息列表区 */
.message-list {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.message-item {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.msg-user {
  align-items: flex-end;
}

.msg-assistant {
  align-items: flex-start;
}

.msg-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.6;
  max-width: 85%;
  word-break: break-word;
}

.user-bubble {
  background: #f4f4f4;
  color: #333;
  border-bottom-right-radius: 4px;
}

.ai-bubble {
  background: transparent;
  color: #333;
  padding: 0;
}

.user-actions {
  margin-top: 4px;
  color: #999;
}

.msg-status {
  font-size: 15px;
  font-weight: 500;
  color: #333;
  margin-bottom: 16px;
}

.msg-thinking {
  border-left: 2px solid #e5e5e5;
  padding-left: 16px;
  margin-bottom: 24px;
  color: #999;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  cursor: pointer;
  margin-bottom: 8px;
}

.thinking-content {
  font-size: 14px;
  line-height: 1.6;
}

/* 底部固定输入区 */
.bottom-spacer {
  height: 180px; /* 为底部悬浮区留白 */
}

.chat-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(255,255,255,1) 80%, rgba(255,255,255,0));
  padding-top: 30px;
  padding-bottom: 16px;
  display: flex;
  justify-content: center;
  z-index: 20;
}

.footer-inner {
  width: 100%;
  max-width: 860px;
  padding: 0 40px;
  display: flex;
  flex-direction: column;
}

.context-files-bar {
  margin-bottom: 8px;
}

.files-btn {
  background: #f9f9f9;
  border-radius: 6px;
  color: #666;
  padding: 6px 12px;
}

.chat-input-wrapper {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  border: 1px solid #eaeaea;
  display: flex;
  flex-direction: column;
}

:deep(.chat-textarea .el-textarea__inner) {
  border: none !important;
  box-shadow: none !important;
  padding: 16px 20px !important;
  font-size: 15px !important;
  line-height: 1.5;
  background: transparent !important;
  min-height: 80px !important;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px 12px;
}

.actions-left,
.actions-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-select-btn {
  font-size: 13px;
  color: #666;
  background-color: transparent !important;
}

.send-btn {
  background: #1a1a1a !important;
  border-color: #1a1a1a !important;
  color: #fff !important;
}

.send-btn.is-disabled {
  background: #e5e5e5 !important;
  border-color: #e5e5e5 !important;
  color: #fff !important;
}

.footer-disclaimer {
  text-align: center;
  font-size: 12px;
  color: #bbb;
  margin-top: 12px;
}
</style>