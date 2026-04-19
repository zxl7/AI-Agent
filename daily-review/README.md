# 本地使用说明（复盘日记生成器）

这套工具分两步：
1) **取数/计算**：`gen_report_v4.py`（会请求接口，有成本）
2) **渲染 HTML**：`daily_review/render/render_html.py`（只读本地 JSON，不取数）

> 推荐日常工作流：先用缓存反复调模板（不取数）→ 需要更新数据时再跑一次取数脚本。

---

## 1. 环境要求

- Linux / macOS / Windows（WSL 也可）
- Python 3.10+（建议）

---

## 2. 目录结构（关键文件）

- `gen_report_v4.py`：取数与生成 `cache/market_data-YYYYMMDD.json`
- `run_report.sh`：一键取数并生成一份 HTML（脚本默认输出）
- `templates/report_template.html`：主模板（你正在迭代的页面）
- `daily_review/render/render_html.py`：将模板 + `market_data-*.json` 渲染成 HTML（离线）
- `cache/`：缓存目录  
  - `market_data-YYYYMMDD.json`：当天汇总数据（渲染输入）
  - `pools_cache.json`：涨停池等明细（渲染时可注入到 HTML）
  - `theme_cache.json`：代码→题材映射（渲染时可注入到 HTML）
- `html/`：输出 HTML 目录

---

## 3. 一键生成（在线取数 + 输出 HTML）

### 3.1 生成最近交易日（自动回退）

```bash
chmod +x run_report.sh
./run_report.sh
```

### 3.2 指定日期（YYYY-MM-DD）

```bash
./run_report.sh 2026-04-17
```

**输出：**
- `cache/market_data-YYYYMMDD.json`（会更新）
- `html/复盘日记-YYYYMMDD-HHMMSS.html`（脚本默认生成的一份 HTML）

---

## 4. 离线渲染（不取数：模板调试/反复迭代用）

当你只想调整模板、样式、布局、算法展示，而不想再次请求接口时，使用离线渲染：

```bash
PYTHONPATH=. python3 daily_review/render/render_html.py \
  --template templates/report_template.html \
  --market-data-json cache/market_data-20260417.json \
  --out html/复盘日记-20260417-tab-v1.html \
  --date 2026-04-17
```

**说明：**
- 该渲染器会离线读取 `cache/pools_cache.json` 与 `cache/theme_cache.json`，把当日涨停池/题材映射注入到 HTML，用于“明日计划/涨停个股分析”等模块。
- 只要 `cache/market_data-YYYYMMDD.json` 存在，就可以反复渲染，不会产生接口消耗。

---

## 5. 常见问题排查

### 5.1 我跑了 `./review.sh` 报错

仓库里默认入口脚本叫 `run_report.sh`，没有 `review.sh`。

你可以：
- 改用 `./run_report.sh`；或
- 自己创建一个 `review.sh`，内容写成：

```bash
#!/usr/bin/env bash
set -euo pipefail
./run_report.sh "$@"
```

并执行：

```bash
chmod +x review.sh
```

### 5.2 生成日期不对

如果你用“今天日期”但今天是周末/假期，脚本会自动回退到最近交易日；可在输出里看到提示。

### 5.3 “明日计划/涨停个股分析”为空

通常是因为渲染时没有注入 `ztgc`（涨停池明细）。请确认：
- `cache/pools_cache.json` 存在且包含对应日期；并且
- 使用的是 `daily_review/render/render_html.py` 离线渲染（它会自动注入）

---

## 6. 推荐工作流（省成本）

1) 每天收盘后跑一次：
   ```bash
   ./run_report.sh
   ```
2) 之后所有 UI/文案/规则迭代都用离线渲染反复调：
   ```bash
   PYTHONPATH=. python3 daily_review/render/render_html.py ...
   ```

