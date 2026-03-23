const DB_NAME = "ai-agent"
const DB_VERSION = 1
const STORE_CHAT = "chat"

const openDB = (): Promise<IDBDatabase> =>
  new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains(STORE_CHAT)) {
        db.createObjectStore(STORE_CHAT)
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })

export const saveChatHistory = async (key: string, value: unknown) => {
  const db = await openDB()
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE_CHAT, "readwrite")
    const store = tx.objectStore(STORE_CHAT)
    store.put(value, key)
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
  db.close()
}

export const loadChatHistory = async <T = unknown>(key: string): Promise<T | null> => {
  const db = await openDB()
  const data = await new Promise<T | null>((resolve, reject) => {
    const tx = db.transaction(STORE_CHAT, "readonly")
    const store = tx.objectStore(STORE_CHAT)
    const req = store.get(key)
    req.onsuccess = () => resolve((req.result as T) ?? null)
    req.onerror = () => reject(req.error)
  })
  db.close()
  return data
}
