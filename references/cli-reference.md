# boss-agent-cli 命令速查

> 拿不准时以 `boss schema` 输出为准（能力真源，支持 `--format openai-tools` 导出工具定义）。
> 所有命令 stdout 只输出 JSON 信封：`{ok, data, pagination, error, hints}`；stderr 是日志。exit 0/1。

## JSON 信封解析约定

- `ok: true` → 业务数据在 `data`；列表结果看 `pagination`（翻页/总数）。
- `ok: false` → 看 `error.code` / `error.recoverable` / `error.recovery_action`：可恢复错误按 `recovery_action` 指定的命令重试或引导用户操作。
- `hints.operator_actions`：需要真人离开终端做的动作（扫码、浏览器里调整），转述给用户；`hints.next_actions` 是给 Agent 的后继命令。
- 风控/安全页错误：立即停止当前工作流，保存断点，告知用户，不得自动重试绕过。

## 常用命令（求职者链路）

### 认证

```bash
boss doctor            # 环境自检（CDP 可达性、browser_channel）
boss login             # 登录（按平台选择链路，会引导扫码）
boss status            # 验证登录态；status --live 低频只读探测
boss logout
```

### 职位发现

```bash
boss search "<关键词>" --city <城市> [--welfare "双休,五险一金"] [--salary "15-25K"] [--page N] [--sort score]
boss detail <security_id>     # 职位详情
boss show <编号>               # 按编号回看缓存结果
boss cities                    # 城市代码表
boss history                   # 搜索历史
```

- v3.0.0（PyPI 当前版）search 参数：--url/--preset/--city/--salary/--experience/--education/--industry/--scale/--stage/--job-type/--welfare/--page/--with-score/--sort。`--active` 活跃度筛选仅更新源码版有，以 `boss search --help` 为准。

- `--welfare`：自动翻页补抓后按 AND 逻辑真实匹配，可 `--sort score` 按本地匹配分排序。
- 排除项（公司名、职位名、JD 关键词）在 Agent 侧过滤：`search` 结果里逐项检查后决定是否 shortlist。

### 风控应对（实测）

- headless 内核（patchright headless）直接发请求，实测触发 ACCOUNT_RISK code 36「账户存在异常行为」。触发后**当天停止自动化**，引导用户回 BOSS 官方 App/网页完成安全验证。
- 低风险替代：复用用户真实 Chrome 会话（不新建页面、不注入 Cookie）——完全退出 Chrome 后以调试端口重启（macOS：`open -na "Google Chrome" --args --remote-debugging-port=9222`），正常登录 zhipin.com，然后 `boss --browser-source existing-browser --cdp-url http://localhost:9222 search ...`。

### 本地整理与统计

```bash
boss shortlist add <security_id> <job_id> --tags 标签1,标签2
boss shortlist list [--tag 标签]      # 查看候选池
boss shortlist compare --tag 标签     # 离线对比
boss stats                            # 漏斗统计
boss favorites                        # 网页收藏（仅同步有效项）
boss preset / boss watch              # 保存筛选预设 / 盯岗
```

### 候选动作（打招呼 / 投递）

```bash
boss greet <security_id> <job_id>                     # 单个打招呼
boss batch-greet --input-json '<json数组>'             # 批量（CLI 内置高斯延迟节流）
boss apply <security_id> <job_id>                      # 投递/发简历等进一步动作
boss pipeline <run_id>                                 # 恢复中断的流程
boss exchange / boss digest                            # 交换联系方式 / 会话摘要
```

### 可恢复采集（大批量时）

```bash
boss crawl configure --max-requests 20 --max-details 50 --max-seconds 600 --max-retries 1
boss crawl run "<关键词>" --city <城市> --pages 3 [--with-detail]
boss crawl status <run_id> / boss crawl resume <run_id> / boss crawl stop <run_id>
boss crawl results <run_id>                            # 导出 JSON/CSV/XLSX 增量产物
```

采集预算固定（请求数/详情数/墙钟时间/重试次数），SQLite 断点，stop 在下一个安全点生效。默认导出不含 security_id 等敏感字段。

### AI 能力（可选，需要用户在 boss config 里配 OpenAI 兼容接口或本地 Ollama/vLLM）

```bash
boss ai analyze-jd <security_id>     # JD 分析
boss ai fit                          # 简历与候选池匹配度
boss ai polish / ai optimize         # 简历润色 / 定向优化
boss ai interview-prep               # 模拟面试素材
boss ai chat-coach                   # 沟通指导
```

## 与追踪表的对照

- `search/detail` 输出里的公司名、职位名、薪资、职位页链接 → 写入追踪表对应列。
- 职位页 URL 形态通常为 `https://www.zhipin.com/job_detail/<id>.html`；若命令只给 `security_id`，用 `boss detail` 的返回字段补全链接，实在拿不到链接就把 security_id 记入备注。
