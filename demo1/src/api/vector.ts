/**
 * 向量库相关接口占位（对接 NestJS）。
 * - 当前 demo 未接入实际 API，仅预留模块边界，便于后续扩展
 */

export type VectorUpsertPayload = {
  namespace: string
  documents: Array<{ id: string; text: string; metadata?: Record<string, unknown> }>
}

export type VectorSearchPayload = {
  namespace: string
  query: string
  topK?: number
}
