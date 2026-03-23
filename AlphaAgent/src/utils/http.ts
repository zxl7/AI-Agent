import axios from "axios"

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://localhost:3001",
  timeout: 30000,
})

http.interceptors.response.use(
  (res: any) => res,
  (err: any) => {
    return Promise.reject(err)
  }
)
