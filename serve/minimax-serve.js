const fs = require("node:fs")
const http = require("node:http")
const path = require("node:path")
const { URL } = require("node:url")

const tryLoadDotEnv = (filePath) => {
  try {
    if (!fs.existsSync(filePath)) return
    const raw = fs.readFileSync(filePath, "utf8")
    const unquote = (value) => {
      if (value.length >= 2 && value.startsWith('"') && value.endsWith('"')) return value.slice(1, -1)
      if (value.length >= 2 && value.startsWith("'") && value.endsWith("'")) return value.slice(1, -1)
      return value
    }
    raw
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#"))
      .forEach((line) => {
        const idx = line.indexOf("=")
        if (idx <= 0) return
        const key = line.slice(0, idx).trim()
        const value = unquote(line.slice(idx + 1).trim())
        if (!key) return
        if (process.env[key] != null) return
        process.env[key] = value
      })
  } catch (_) {
    return
  }
}

tryLoadDotEnv(path.join(__dirname, ".env"))

const getRequiredEnv = (key) => {
  const value = process.env[key]
  if (value == null || String(value).trim() === "") throw new Error(`Missing required env: ${key}`)
  return String(value)
}

const getOptionalEnv = (key, fallback) => {
  const value = process.env[key]
  if (value == null || String(value).trim() === "") return fallback
  return String(value)
}

const isRecord = (value) => value != null && typeof value === "object" && !Array.isArray(value)
const isString = (value) => typeof value === "string"

const clampNumber = (value, min, max, fallback) => {
  const num = typeof value === "number" ? value : Number(value)
  if (Number.isNaN(num)) return fallback
  return Math.min(max, Math.max(min, num))
}

const normalizeRole = (role) => {
  if (!isString(role)) return null
  const r = role.trim()
  if (r === "bot") return "assistant"
  if (r === "user" || r === "assistant" || r === "system") return r
  return null
}

const normalizeHistory = (history) => {
  if (!Array.isArray(history)) return []
  return history
    .filter((m) => isRecord(m))
    .map((m) => {
      const role = normalizeRole(m.role)
      const content = isString(m.content) ? m.content : ""
      if (!role) return null
      return { role, content }
    })
    .filter(Boolean)
    .slice(-50)
}

const sseHeaders = () => ({
  "Content-Type": "text/event-stream; charset=utf-8",
  "Cache-Control": "no-cache, no-transform",
  Connection: "keep-alive",
  "X-Accel-Buffering": "no",
})

const jsonHeaders = () => ({
  "Content-Type": "application/json; charset=utf-8",
})

const corsHeaders = () => {
  const origin = getOptionalEnv("CORS_ORIGIN", "*")
  const credentials = getOptionalEnv("CORS_CREDENTIALS", "false") === "true"
  const allowOrigin = credentials && origin === "*" ? "http://localhost:5173" : origin
  return {
    "Access-Control-Allow-Origin": allowOrigin,
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    ...(credentials ? { "Access-Control-Allow-Credentials": "true" } : {}),
  }
}

const sendJson = (res, status, payload) => {
  res.writeHead(status, { ...jsonHeaders(), ...corsHeaders() })
  res.end(JSON.stringify(payload))
}

const readJsonBody = (req, limitBytes) =>
  new Promise((resolve, reject) => {
    const chunks = []
    let size = 0
    req.on("data", (chunk) => {
      size += chunk.length
      if (size > limitBytes) {
        reject(new Error("Payload too large"))
        req.destroy()
        return
      }
      chunks.push(chunk)
    })
    req.on("end", () => {
      if (chunks.length === 0) return resolve({})
      try {
        const raw = Buffer.concat(chunks).toString("utf8")
        resolve(JSON.parse(raw))
      } catch (e) {
        reject(e)
      }
    })
    req.on("error", reject)
  })

const pipeWebStreamToNodeResponse = async ({ readable, res, signal }) => {
  const reader = readable.getReader()
  try {
    while (true) {
      if (signal.aborted) break
      const { done, value } = await reader.read()
      if (done) break
      res.write(Buffer.from(value))
    }
  } finally {
    try {
      reader.releaseLock()
    } catch (_) {
      return
    }
  }
}

const buildMinimaxUrl = () => {
  const base = getOptionalEnv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1").replace(/\/+$/, "")
  return `${base}/chat/completions`
}

const handleHealth = (req, res) => {
  const model = getOptionalEnv("MINIMAX_MODEL", "minimax-3.5")
  const baseUrl = getOptionalEnv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
  const hasApiKey = Boolean(process.env.MINIMAX_API_KEY)
  const hasGroupId = Boolean(process.env.MINIMAX_GROUP_ID)
  sendJson(res, 200, {
    status: "success",
    message: "Minimax HTTP 接入服务运行正常",
    timestamp: new Date().toISOString(),
    config: { model, baseUrl, hasApiKey, hasGroupId },
  })
}

const handleChat = async (req, res) => {
  const jsonLimit = Number(getOptionalEnv("JSON_LIMIT_BYTES", "1048576"))
  let body
  try {
    body = await readJsonBody(req, jsonLimit)
  } catch (e) {
    return sendJson(res, 400, { code: 400, error: "请求体不是合法 JSON", detail: e.message })
  }

  const message = isString(body.message) ? body.message.trim() : ""
  const temperature = clampNumber(body.temperature, 0, 1, 0.7)
  const history = normalizeHistory(body.history)

  if (!message) return sendJson(res, 400, { code: 400, error: "消息内容不能为空" })
  if (message.length > 20000) return sendJson(res, 400, { code: 400, error: "消息内容过长" })

  const apiKey = getRequiredEnv("MINIMAX_API_KEY")
  const groupId = getOptionalEnv("MINIMAX_GROUP_ID", "")
  const model = getOptionalEnv("MINIMAX_MODEL", "minimax-3.5")
  const upstreamUrl = buildMinimaxUrl()

  const payload = {
    model,
    messages: [...history, { role: "user", content: message }],
    stream: true,
    temperature,
    max_tokens: clampNumber(body.max_tokens, 1, 8192, 2048),
    ...(groupId ? { group_id: groupId } : {}),
  }

  const controller = new AbortController()
  req.on("close", () => controller.abort())

  let upstreamRes
  try {
    const url = new URL(upstreamUrl)
    if (groupId && getOptionalEnv("MINIMAX_GROUP_ID_IN_QUERY", "false") === "true") {
      url.searchParams.set("GroupId", groupId)
    }

    upstreamRes = await fetch(url.toString(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })
  } catch (e) {
    if (controller.signal.aborted) return
    return sendJson(res, 502, { code: 502, error: "上游请求失败", detail: e.message })
  }

  const contentType = upstreamRes.headers.get("content-type") || ""

  if (!upstreamRes.ok) {
    const text = await upstreamRes.text().catch(() => "")
    return sendJson(res, upstreamRes.status || 500, {
      code: upstreamRes.status || 500,
      error: "上游返回错误",
      detail: text.slice(0, 2000),
    })
  }

  res.writeHead(200, { ...sseHeaders(), ...corsHeaders() })
  if (typeof res.flushHeaders === "function") res.flushHeaders()

  if (upstreamRes.body && contentType.includes("text/event-stream")) {
    await pipeWebStreamToNodeResponse({ readable: upstreamRes.body, res, signal: controller.signal })
    if (!res.writableEnded) res.end()
    return
  }

  const text = await upstreamRes.text().catch(() => "")
  const json = (() => {
    try {
      return JSON.parse(text)
    } catch (_) {
      return null
    }
  })()

  if (json?.choices?.[0]?.message?.content) {
    res.write(
      `data: ${JSON.stringify({
        choices: [{ delta: { content: String(json.choices[0].message.content) } }],
        model,
      })}\n\n`
    )
    res.write("data: [DONE]\n\n")
    res.end()
    return
  }

  res.write(`data: ${JSON.stringify({ error: "Unsupported upstream response" })}\n\n`)
  res.write("data: [DONE]\n\n")
  res.end()
}

const server = http.createServer(async (req, res) => {
  if (!req.url) return sendJson(res, 400, { code: 400, error: "Invalid request" })

  const url = new URL(req.url, "http://localhost")
  if (req.method === "OPTIONS") {
    res.writeHead(204, { ...corsHeaders() })
    return res.end()
  }

  if (req.method === "GET" && url.pathname === "/api/health") return handleHealth(req, res)
  if (req.method === "POST" && url.pathname === "/api/chat") return handleChat(req, res)

  return sendJson(res, 404, { code: 404, error: "Not found" })
})

process.on("uncaughtException", (err) => {
  console.error("[uncaughtException]", err)
})
process.on("unhandledRejection", (reason) => {
  console.error("[unhandledRejection]", reason)
})

const PORT = Number(getOptionalEnv("PORT", "3000"))
server.listen(PORT, () => {
  console.log(`服务启动成功：http://localhost:${PORT}`)
})
