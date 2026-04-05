import { http } from "./index"

/**
 * 获取知识库所有数据
 */
export const getVectorData = async () => {
  const res = await http.get("/api/vector/data")
  return res.data
}

/**
 * 向向量库添加数据
 */
export const addVectorData = async (payload: { texts: string[]; metadatas?: Record<string, any>[] }) => {
  const res = await http.post("/api/vector/add", payload)
  return res.data
}

