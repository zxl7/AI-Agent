## 本地 Vendor 资源说明（替代 CDN）

目标：让生成的 HTML 在**离线**或**不稳定网络**环境下也能直接打开（file:// 或本地静态服务器均可）。

### 需要放哪些文件？

把以下 2 个文件下载到本目录（文件名保持一致）：

1. `echarts.min.js`
   - 来源（任选其一）：
     - https://fastly.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js
     - https://unpkg.com/echarts@5.4.3/dist/echarts.min.js

2. `vue.global.prod.js`
   - 来源（任选其一）：
     - https://fastly.jsdelivr.net/npm/vue@3/dist/vue.global.prod.js
     - https://unpkg.com/vue@3/dist/vue.global.prod.js

### 为什么不用 NPM / build？
- 你的报告是“Python 输出静态 HTML”的模式；
- 这里选择 **CDN 文件本地化**，不引入任何构建流程，保持简单可控。

