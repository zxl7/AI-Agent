import MarkdownIt from "markdown-it"
import hljs from "highlight.js"

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

export const renderMarkdown = (source: string): string => {
  if (!source) return ""
  return md.render(source)
}
