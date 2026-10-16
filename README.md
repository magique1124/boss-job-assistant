# BOSS 求职助手（boss-job-assistant）

一个开源的 **Agent Skill**：让 AI Agent 帮你在 BOSS 直聘上自动找工作——对话式收集求职意向，自动搜索、筛选、（经你确认后）投递简历，维护投递追踪表，约面后还能预测面试题、查资料、陪你模拟面试。

基于 [boss-agent-cli](https://github.com/can4hou6joeng4/boss-agent-cli)（MIT）构建，符合开放 Agent Skills 规范（`SKILL.md` 目录格式），可被 Kimi、Claude Code、Cursor、OpenCode 等支持 Skills 的 Agent 加载。

## 功能

- **对话式意向收集**：目标岗位关键词、城市、薪资、福利要求（如双休/五险一金）、排除项、简历路径
- **搜索与筛选**：调用 `boss search --welfare --active` 做多维筛选，排除不匹配的岗位
- **人工确认闸**：真实投递前必须给你候选清单确认，不擅自投递
- **投递追踪表**：自动生成 Excel 追踪表（公司/岗位/薪资/JD 链接/是否投递/是否回复/是否约面/面试情况/备注），支持按 JD 链接去重更新
- **面试准备**：针对约面岗位的 JD 和你的简历，预测面试官问题、联网查公司与面经、逐题模拟面试并点评
- **风控内置**：遵守平台打招呼上限，命中风控立即停止并提示，不绕过

## 前置要求（使用者一次性准备）

```bash
# 1. 安装 uv（https://astral.sh/uv）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 安装底座 CLI 与浏览器内核（需要 Python >= 3.10，uv 会自动准备）
uv tool install boss-agent-cli
patchright install chromium || uvx patchright install chromium

# 3. 扫码登录 BOSS 直聘（登录态加密保存在本机）
boss login
```

追踪表脚本依赖 openpyxl：`pip install openpyxl`（或用 Agent 的运行时自带环境）。

## 安装方式（按你用的 Agent 选一个）

**Kimi Work**：在插件页「个人」页签安装，或把本仓库交给 Kimi 的插件转换工具转成插件；也可以直接安装 `.skill` 包。

**Claude Code / Cursor / OpenCode / Kimi Code CLI 等**：把本仓库（或 `SKILL.md` 所在目录）复制到你的 skills 目录，例如：

```bash
git clone https://github.com/magique1124/boss-job-assistant.git ~/.claude/skills/boss-job-assistant
```

**skills 生态**：`npx skills add magique1124/boss-job-assistant`

## 使用（对 Agent 说人话即可）

- "帮我找 Golang 后端的工作，base 广州，15K 以上，要求双休"
- "把今天投递的岗位更新到追踪表"
- "字节约我下周面试，帮我准备"

## 免责声明

自动化访问招聘平台可能违反其用户协议，存在账号限流/降权风险。请仅用于**个人求职**、控制投递频率、发送前自行审阅招呼语；因使用产生的后果由使用者自行承担。详见 SKILL.md 内的硬性规则。

## License

MIT © magique1124
