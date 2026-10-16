---
name: boss-job-assistant
description: BOSS 直聘自动求职助手：交互式收集目标岗位（关键词/薪资/城市/福利要求），自动搜索、筛选、投递简历并生成投递追踪表（公司/岗位/薪资/JD 链接/投递/回复/约面/面试情况），约面后提供面试题预测、资料调研和模拟面试。使用场景：用户说"帮我找工作/投简历/自动投递/BOSS 直聘求职/生成投递追踪表/准备面试/模拟面试"，或明确要针对目标岗位批量打招呼、投递简历并跟踪求职进度时。
---

# BOSS 直聘自动求职助手

以开源工具 `boss-agent-cli` 为底座（它是面向 AI Agent 的 BOSS 直聘 CLI，stdout 输出结构化 JSON 信封），本 skill 在其上封装完整求职工作流：**信息收集 → 环境检查 → 搜索筛选 → 人工确认 → 投递 → 追踪表 → 面试准备**。

## 前置依赖（首次使用时引导用户完成）

```bash
uv tool install boss-agent-cli
patchright install chromium
boss doctor        # 环境自检，必须 ok
boss login         # 用户扫码登录
boss status        # 确认登录态有效
```

若 `boss` 命令不存在，先装 uv：`curl -LsSf https://astral.sh/uv/install.sh | sh`。
命令输出全部是 JSON 信封 `{ok, data, pagination, error, hints}`：用 `ok` 判断成败，用 `hints.operator_actions` 获取需要转述给用户的真人操作（如扫码）。错误信封带 `code` / `recoverable` / `recovery_action`，按恢复动作重试或引导用户处理。

## 工作流

### 第 1 步：交互式收集求职意向（每次开始必做）

用**一轮对话**问清以下信息（用户可能一次性给全，缺什么问什么，不要反复追问）：

1. **目标岗位关键词**（如"Golang 后端"，可多个）
2. **工作城市**（如"广州"，可多选）
3. **期望薪资**（区间，如 15-25K）
4. **硬性福利/要求**（如"双休,五险一金"，对应 CLI 的 `--welfare`，是本项目核心筛选能力）
5. **排除项**（如排除外包、销售岗、某些公司名）
6. **简历文件路径**（本地 PDF；可选，用于投递和后续面试准备）
7. **本次投递数量**（默认 20 个以内，遵守平台每日打招呼上限约 100-150 次）

把结果整理成一段配置复述给用户确认，例如：

> 目标：Golang 后端｜广州｜15-25K｜要求双休+五险一金｜排除外包｜简历：/path/resume.pdf｜本次投 20 个。确认后我开始搜索。

### 第 2 步：搜索与筛选

```bash
boss search "<关键词>" --city <城市> --welfare "<福利>" --page 1
boss detail <security_id>   # 对候选岗位逐个看详情
```

- 可用的筛选参数以 `boss search --help` 为准（PyPI 当前 v3.0.0 支持 --city/--salary/--experience/--education/--industry/--scale/--stage/--job-type/--welfare/--sort；`--active` 活跃度筛选仅在更新源码版可用）。
- 结合 `pagination` 翻页拿够候选；用第 1 步的排除项过滤（公司名、职位名、JD 内容）。
- 把通过筛选的岗位存入本地候选池并打标签，便于离线对比：

```bash
boss shortlist add <security_id> <job_id> --tags 自动投递,<日期>
boss shortlist compare        # 候选多的话离线对比给用户看
```

### 第 3 步：人工确认（必做，不可跳过）

投递前把候选清单（公司、岗位、薪资、匹配理由）呈现给用户，明确说：

> 以上 N 个岗位将执行打招呼/投递，确认吗？也可以删掉个别岗位。

未经用户确认不得执行真实投递动作。若用户想先看招呼语质量，用 dry-run 思路：生成招呼语给用户过目后再发。

### 第 4 步：执行投递

```bash
boss greet <security_id> <job_id>          # 单个打招呼
boss batch-greet --input-json '<json>'     # 批量（间隔由 CLI 节流控制）
boss apply <security_id> <job_id>          # 需要发简历/进一步动作时
```

- CLI 自带高斯延迟节流，不要自行加速或并发调用。
- **风控应对（重要，实测经验）**：headless 内核直接请求容易触发平台风控（ACCOUNT_RISK code 36 账户异常）。更稳的方式是复用用户真实 Chrome 会话：先完全退出 Chrome，再以 `open -na "Google Chrome" --args --remote-debugging-port=9222` 启动，在浏览器里正常登录 zhipin.com 后，用 `boss --browser-source existing-browser --cdp-url http://localhost:9222 search ...`（该模式不新建页面、不注入 Cookie）。触发风控后立即停手，引导用户回 BOSS 官方 App/网页完成安全验证，当天不再重试。
- 单次会话投递量遵守用户设定的数量。

### 第 5 步：更新投递追踪表

每次投递结束，用脚本维护工作目录下的 `投递追踪表.xlsx`（团队/个人复用同一文件，跨会话追加）：

```bash
# 新建（已存在则跳过）
python3 <skill目录>/scripts/create_tracker.py ./投递追踪表.xlsx

# 每投一个岗位追加一行
python3 <skill目录>/scripts/update_tracker.py ./投递追踪表.xlsx add \
  --company "公司名" --position "岗位名" --salary "15-25K" \
  --jd "https://..." --status 已投递

# 后续更新进度（按 JD 链接定位行）
python3 <skill_dir>/scripts/update_tracker.py ./投递追踪表.xlsx update \
  --jd "https://..." --set 是否回复=是 --set 备注="HR 要了作品集"
```

列结构：序号 / 公司 / 岗位 / 薪资 / JD 链接 / 是否投递 / 是否回复 / 是否约面 / 面试情况 / 备注 / 更新时间。状态列带下拉选项（是/否/已投递/待投递/未通过/通过/待定）。

投递结束后向用户汇报：本次投递数、失败数、追踪表路径，并主动问是否要查看/补充表格。

### 第 6 步：面试准备（用户反馈"约面了"时触发）

读 [references/interview-prep.md](references/interview-prep.md) 执行：JD + 简历 → 预测面试官问题（含联网查公司/行业/技术资料）→ 模拟面试逐题演练并点评。完成后把面试情况回写追踪表 `--set 面试情况="..."`。

## 详细命令参考

所有 `boss` 命令的参数、JSON 信封字段、错误码与恢复动作见 [references/cli-reference.md](references/cli-reference.md)。拿不准命令时先跑 `boss schema`（能力真源）。

## 硬性规则

1. 真实投递前必须经用户清单确认（第 3 步）。
2. 遵守平台每日上限与 CLI 节流，不绕过风控；风控触发即停。
3. 追踪表是本 skill 的核心交付物之一，每次投递后必须更新，进度信息（回复/约面/面试结果）随时可回写。
4. 用户凭证、简历等本地数据不离开本机，不写入追踪表以外的地方。
5. 首次使用必须向用户说明：自动化访问招聘平台可能违反平台用户协议，有账号限流/降权风险，请控制频率、仅用于个人求职。
