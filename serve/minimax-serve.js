/**
 * Minimax OpenAI 兼容接口对接服务
 * 核心：使用 OpenAI SDK + 读取 .env 配置 + 完全兼容 Vue 前端
 * 文档：https://platform.minimaxi.com/docs/api-reference/text-openai-api
 * 依赖：npm install openai cors dotenv express
 */
const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
// 引入 OpenAI 官方 SDK（核心依赖）
const { OpenAI } = require('openai');

// 1. 加载 .env 配置（优先读取环境变量，安全且易部署）
dotenv.config();
const app = express();
const PORT = process.env.PORT || 3000;

// 2. 从 .env 读取 Minimax 配置（所有参数通过环境变量注入）
const MINIMAX_CONFIG = {
  API_KEY: process.env.MINIMAX_API_KEY, // 必须从 .env 读取，不设默认值（强制配置）
  GROUP_ID: process.env.MINIMAX_GROUP_ID, // 可选，部分账号需要
  MODEL: process.env.MINIMAX_MODEL || 'minimax-3.5', // 兜底默认值
  BASE_URL: process.env.MINIMAX_BASE_URL || 'https://api.minimax.chat/v1' // Minimax OpenAI 兼容接口前缀
};

// 3. 校验核心配置（缺少 API Key 直接报错）
if (!MINIMAX_CONFIG.API_KEY) {
  console.error('[错误] 请在 .env 文件中配置 MINIMAX_API_KEY！');
  process.exit(1); // 终止服务启动，避免运行时错误
}

// 4. 初始化 OpenAI 客户端（指向 Minimax 兼容接口）
const openai = new OpenAI({
  apiKey: MINIMAX_CONFIG.API_KEY, // 用 Minimax 的 API Key
  baseURL: MINIMAX_CONFIG.BASE_URL, // 指向 Minimax 的 OpenAI 兼容接口地址
  timeout: 30000 // 超时时间，避免请求挂起
});

// 5. 全局中间件配置
app.use(cors()); // 解决前端跨域
app.use(express.json()); // 解析 JSON 请求体
app.use(express.urlencoded({ extended: true })); // 解析表单请求

// 6. 健康检查接口（验证配置和服务状态）
app.get('/api/health', (req, res) => {
  res.status(200).json({
    status: 'success',
    message: 'Minimax OpenAI 兼容服务运行正常',
    timestamp: new Date().toISOString(),
    config: {
      model: MINIMAX_CONFIG.MODEL,
      baseUrl: MINIMAX_CONFIG.BASE_URL,
      hasApiKey: !!MINIMAX_CONFIG.API_KEY, // 只返回是否配置，不泄露密钥
      hasGroupId: !!MINIMAX_CONFIG.GROUP_ID
    }
  });
});

// 7. 核心聊天接口（使用 OpenAI SDK + 读取 .env 配置）
app.post('/api/chat', async (req, res) => {
  try {
    const {
      message = '',
      history = [],
      temperature = 0.7
    } = req.body;

    // 参数校验
    if (!message.trim()) {
      return res.status(400).json({
        code: 400,
        error: '消息内容不能为空'
      });
    }

    // 构造 OpenAI 格式的消息（兼容前端传入的 history）
    const messages = [
      ...history, // 复用前端的历史消息格式 {role: 'user/bot', content: 'xxx'}
      { role: 'user', content: message.trim() }
    ];

    // 调用 Minimax 接口（通过 OpenAI SDK）
    const stream = await openai.chat.completions.create({
      model: MINIMAX_CONFIG.MODEL, // 从 .env 读取模型名
      messages: messages,
      stream: true, // 流式输出
      temperature: Number(temperature),
      max_tokens: 2048,
      // 可选：传入 Group ID（部分账号需要）
      ...(MINIMAX_CONFIG.GROUP_ID && { group_id: MINIMAX_CONFIG.GROUP_ID })
    });

    // 配置流式响应头（适配 Vue 前端）
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    // 逐行转发流式数据
    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content || '';
      if (content) {
        // 输出 OpenAI 标准格式的流式数据，前端无需修改
        res.write(`data: ${JSON.stringify({
          choices: [{ delta: { content: content } }],
          model: MINIMAX_CONFIG.MODEL
        })}\n\n`);
      }
    }

    // 流结束标记
    res.write('data: [DONE]\n\n');
    res.end();

  } catch (error) {
    console.error('[聊天接口异常]', error.message);
    res.status(500).json({
      code: 500,
      error: 'AI 服务调用失败',
      detail: error.message,
      tip: '请检查 .env 中的 MINIMAX_API_KEY/MODEL 是否正确'
    });
  }
});

// 8. 启动服务
app.listen(PORT, () => {
  console.log(`====================================`);
  console.log(`服务启动成功：http://localhost:${PORT}`);
  console.log(`使用模型：${MINIMAX_CONFIG.MODEL}`);
  console.log(`接口地址：${MINIMAX_CONFIG.BASE_URL}`);
  console.log(`健康检查：http://localhost:${PORT}/api/health`);
  console.log(`====================================`);
});

// 9. 全局异常捕获（增强稳定性）
process.on('uncaughtException', (err) => {
  console.error('[未捕获异常]', err);
});
process.on('unhandledRejection', (reason) => {
  console.error('[未处理Promise拒绝]', reason);
});