# 本地使用说明（复盘日记生成器）

本项目推荐用 **两个脚本** 完成日常工作：

1) `fetch_report.sh`：**拉取数据 + 生成最新报告**（会请求接口，有成本）  
2) `review.sh`：**只用缓存离线渲染报告**（不取数，适合反复调模板）

输出 HTML 都在 `html/` 目录。

---

## 环境要求

- Python 3.10+（建议）

---

## 1) 拉取数据并生成最新报告（在线，有成本）

```bash
chmod +x fetch_report.sh
./fetch_report.sh              # 自动回退到最近交易日
./fetch_report.sh 2026-04-17   # 指定日期
```

输出：
- `cache/market_data-YYYYMMDD.json`（更新缓存）
- `html/复盘日记-YYYYMMDD-tab-v1.html`（用最新模板渲染）

说明：
- `gen_report_v4.py` 本身会生成一个带时分秒的历史版本 HTML（用于留档）。
- `fetch_report.sh` 会**自动清理**该历史版本，只保留你常用的 `复盘日记-YYYYMMDD-tab-v1.html`，避免目录里出现两个 HTML。

---

## 2) 只用缓存渲染报告（离线，无成本）

```bash
chmod +x review.sh
./review.sh                    # 使用 cache 里最新的 market_data-*.json
./review.sh 2026-04-17         # 指定日期（需已有对应 cache/market_data-YYYYMMDD.json）
```

输出：
- `html/复盘日记-YYYYMMDD-tab-v1.html`

---

## 常见问题

### 1) 为什么日期会自动变化？
当输入日期是周末/非交易日，取数脚本会自动回退到最近交易日，并在日志里提示。

### 2) 离线渲染提示找不到 `market_data-YYYYMMDD.json`
说明本地还没有这一天的缓存。先跑一次：
```bash
./fetch_report.sh 2026-04-17
```

---

## 关键文件（知道这些就够了）

- `templates/report_template.html`：主模板
- `cache/market_data-YYYYMMDD.json`：渲染输入数据
- `html/`：输出目录
