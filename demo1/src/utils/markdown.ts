const replaceAllText = (value: string, search: string, replacement: string) => value.split(search).join(replacement)

const escapeHtml = (value: string) =>
  replaceAllText(
    replaceAllText(
      replaceAllText(replaceAllText(replaceAllText(value, "&", "&amp;"), "<", "&lt;"), ">", "&gt;"),
      '"',
      "&quot;"
    ),
    "'",
    "&#39;"
  )

const sanitizeHref = (href: string) => {
  const raw = href.trim()
  if (!raw) return "#"
  try {
    const url = new URL(raw, "http://localhost")
    if (url.protocol === "http:" || url.protocol === "https:" || url.protocol === "mailto:") return url.toString()
    return "#"
  } catch (_) {
    return "#"
  }
}

const renderInlineMarkdown = (input: string) => {
  const segments = input.split("`")
  return segments
    .map((segment, idx) => {
      const escaped = escapeHtml(segment)
      if (idx % 2 === 1) return `<code>${escaped}</code>`

      const withLinks = escaped.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_: string, text: string, href: string) => {
        const safeHref = sanitizeHref(String(href))
        const safeText = String(text)
        return `<a href="${safeHref}" target="_blank" rel="noreferrer noopener">${safeText}</a>`
      })

      const withBold = withLinks
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/__([^_]+)__/g, "<strong>$1</strong>")

      const withItalic = withBold
        .replace(/(^|[^*])\*([^*\n]+)\*([^*]|$)/g, "$1<em>$2</em>$3")
        .replace(/(^|[^_])_([^_\n]+)_([^_]|$)/g, "$1<em>$2</em>$3")

      return withItalic
    })
    .join("")
}

export const renderMarkdown = (source: string) => {
  const lines = source.replace(/\r\n/g, "\n").split("\n")
  const out: string[] = []

  let inFence = false
  let fenceLang = ""
  let fenceLines: string[] = []

  const flushFence = () => {
    if (!inFence) return
    const code = escapeHtml(fenceLines.join("\n"))
    const langClass = fenceLang ? ` class="language-${escapeHtml(fenceLang)}"` : ""
    out.push(`<pre><code${langClass}>${code}</code></pre>`)
    inFence = false
    fenceLang = ""
    fenceLines = []
  }

  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    const fenceMatch = line.match(/^```(\w+)?\s*$/)
    if (fenceMatch) {
      if (inFence) {
        flushFence()
        i += 1
        continue
      }
      inFence = true
      fenceLang = fenceMatch[1] || ""
      fenceLines = []
      i += 1
      continue
    }

    if (inFence) {
      fenceLines.push(line)
      i += 1
      continue
    }

    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/)
    if (headingMatch) {
      const level = headingMatch[1].length
      out.push(`<h${level}>${renderInlineMarkdown(headingMatch[2])}</h${level}>`)
      i += 1
      continue
    }

    if (line.trim() === "") {
      out.push("")
      i += 1
      continue
    }

    const blockquoteMatch = line.match(/^>\s?(.*)$/)
    if (blockquoteMatch) {
      const quoteLines: string[] = []
      while (i < lines.length) {
        const m = lines[i].match(/^>\s?(.*)$/)
        if (!m) break
        quoteLines.push(renderInlineMarkdown(m[1] || ""))
        i += 1
      }
      out.push(`<blockquote>${quoteLines.join("<br/>")}</blockquote>`)
      continue
    }

    const ulMatch = line.match(/^\s*[-*+]\s+(.+)$/)
    const olMatch = line.match(/^\s*\d+\.\s+(.+)$/)
    if (ulMatch || olMatch) {
      const isOrdered = Boolean(olMatch)
      const tag = isOrdered ? "ol" : "ul"
      const items: string[] = []
      while (i < lines.length) {
        const cur = lines[i]
        const m = isOrdered ? cur.match(/^\s*\d+\.\s+(.+)$/) : cur.match(/^\s*[-*+]\s+(.+)$/)
        if (!m) break
        items.push(`<li>${renderInlineMarkdown(m[1])}</li>`)
        i += 1
      }
      out.push(`<${tag}>${items.join("")}</${tag}>`)
      continue
    }

    const paraLines: string[] = []
    while (i < lines.length) {
      const cur = lines[i]
      if (cur.trim() === "") break
      if (/^```/.test(cur)) break
      if (/^(#{1,6})\s+/.test(cur)) break
      if (/^>\s?/.test(cur)) break
      if (/^\s*[-*+]\s+/.test(cur)) break
      if (/^\s*\d+\.\s+/.test(cur)) break
      paraLines.push(renderInlineMarkdown(cur))
      i += 1
    }
    out.push(`<p>${paraLines.join("<br/>")}</p>`)
  }

  flushFence()
  return out
    .filter((b) => b !== "")
    .join("\n")
    .trim()
}

