/**
 * 通用类型定义入口：
 * - 只放「领域模型/协议模型」等纯类型
 * - 不依赖 Vue/Pinia，避免类型层反向依赖业务实现
 */

/** 对话消息角色 */
export type ChatRole = "user" | "assistant"

/** UI 消息状态：streaming 为占位/流式拼接中 */
export type ChatMessageStatus = "success" | "streaming" | "error"

/** UI 层消息模型（用于渲染与流式拼接） */
export type ChatMessage = {
  id: number
  role: ChatRole
  content: string
  rawContent?: string
  status?: ChatMessageStatus
}

/** 发送给后端的历史消息模型（system/user/assistant） */
export type ChatHistoryItem = { role: "user" | "assistant" | "system"; content: string }

/** Chat 接口请求体 */
export type ChatRequestPayload = {
  message: string
  history: ChatHistoryItem[]
  temperature?: number
}

