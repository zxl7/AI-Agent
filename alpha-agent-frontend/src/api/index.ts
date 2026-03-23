import axios from "axios"

/**
 * Axios 实例（非流式接口使用）：
 * - 适合常规 JSON 请求/响应
 * - 流式输出（ReadableStream）仍建议用 fetch（更可控）
 */
export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://localhost:3001",
  timeout: 30000,
})

http.interceptors.response.use(
  (res) => res,
  (err) => Promise.reject(err)
)

