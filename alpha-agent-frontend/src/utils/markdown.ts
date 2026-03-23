import MarkdownIt from "markdown-it"
import hljs from "highlight.js"

/**
 * Markdown 渲染器：
 * - 禁止 HTML（避免 XSS）
 * - 内置代码高亮（highlight.js）
 */
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  highlight: (str, lang) => {
    try {
      if (lang && hljs.getLanguage(lang)) {
        return `<pre><code class="hljs language-${lang}">` + hljs.highlight(str, { language: lang }).value + "</code></pre>"
      }
      return `<pre><code class="hljs">` + md.utils.escapeHtml(str) + "</code></pre>"
    } catch {
      return `<pre><code class="hljs">` + md.utils.escapeHtml(str) + "</code></pre>"
    }
  },
})

/**
 * 将 Markdown 渲染为 HTML 字符串（纯函数）。
 */
export const renderMarkdown = (source: string): string => {
  if (!source) return ""
  return md.render(source)
}
