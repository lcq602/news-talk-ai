# 06 · 可运行 Python MVP（v0.1）

**目标**：只做本地阅读一篇原创文章 + 与 AI 英语教练聊天 + 全面纠错。不做新闻抓取、账号、数据库、语音、登录、真实 CEFR 测评。

## 1. 功能闭环
1. 用户打开 `http://127.0.0.1:8000`，阅读左侧原创虚构文章。
2. 点击开始对话，AI 根据文章先问一个问题。
3. 用户英文回答；AI 回复观点、逐条指出可证实的拼写/语法/用词/自然度/标点/表达清晰度问题，给完整润色版本、解释和追问。
4. 用户可继续练习；点击“新对话”清空当前练习。

## 2. 安装与运行
先安装 uv：https://docs.astral.sh/uv/getting-started/installation/

```powershell
git clone https://github.com/lcq602/news-talk-ai.git
cd news-talk-ai
Copy-Item .env.example .env
# 使用编辑器打开 .env，填写自己的 OPENAI_API_KEY、OPENAI_MODEL、OPENAI_BASE_URL
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

然后打开 http://127.0.0.1:8000

Linux/macOS：`cp .env.example .env`，其余命令相同。

### 环境变量
```dotenv
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-key
OPENAI_MODEL=your-chat-model
AI_TIMEOUT_SECONDS=45
```
**Base URL 末尾是 `/v1`，不是 `/chat/completions`。** 服务端自行拼接后者。仅支持兼容 `POST /chat/completions` 的服务。不同提供商对结构化输出等高级参数兼容不同，因此 MVP 只用基础 messages + model 请求。需选支持基础 JSON 指令遵循的模型。

运行测试：`uv run pytest -q`。

## 3. 如何更换文章
修改 `content/article.md`（UTF-8），重新启动服务（使用 --reload 会自动重载 Python 文件，但修改 .md 后建议手动重启）。目前只有一个文章，无动态切换、上传或抓取功能。仅使用自己原创或获得适当授权的正文。

## 4. 如何修改 AI 角色
编辑 `prompts/english_tutor.md`。这是独立、版本化的**system prompt / teaching skill**：
- 先理解用户意思再指出问题；
- 每条有 original、suggested、type、中文解释；
- 默认指出所有**明确且有学习价值**的问题，而非随机改写；
- 区分错误、自然表达建议和事实纠错；
- 产出完整的 polished_version；
- 每轮只追问一个和文章相关的问题。

期望 JSON 字段：reply_en, polished_version, corrections[], useful_phrases[], follow_up_en。字段解析与验证失败返回 502，可重试。**不承诺所有小模型都能稳定遵循格式或纠错准确**，需实际对照评估。

## 5. API
- `GET /`：极简网页
- `GET /api/article`：当前文章（原创虚构）
- `POST /api/session`：启动一个会话并获取开场问句
- `POST /api/chat`：传 `{"session_id":"...","message":"..."}`，返回结构化纠错回复
- `DELETE /api/session/{id}`：结束会话，移除内存记录

## 6. 技术设计与边界
- FastAPI + httpx + 原生 HTML/CSS/JS，无前端构建工具。
- 单工作进程、内存会话、最多 100 个会话、每会话 30 轮、每条 2000 字符。
- 每次最多传最近 12 条会话消息，但系统提示里始终保留文章全文（当前短篇）。
- 没有流式输出，等待模型返回完整 JSON；如需低延迟可在下一阶段扩展。
- 本地 `127.0.0.1` 运行，不要直接开放公网：**无登录、无访问控制、无持久化、无生产级成本限流**。
- 不在日志打印 API key、用户对话或模型全文；`.env` 被 gitignore。
- 当错误发生时不保存当前用户消息，可以重新发送；并发请求同一会话可能返回 409（建议 UI 禁止重复发送）。
- 无云端实际集成测试；需自己设置 key 测通，并注意提供商的数据保留策略。

## 7. 手工验收用例
| 用户输入 | 期待效果 |
|---|---|
| `I think AI can helps small stores.` | 指出 can 后动词原形 |
| `This story is very interesing.` | 指出 interesing → interesting |
| `I very like this idea.` | 改为 I really like this idea / I like this idea very much |
| `I think the assistant can help Maya, but it sometimes give wrong answer.` | 指出 gives / answers 等错误 |
| `I believe technology should support people.` | 不硬凑错误；可给可选表达 |
| `我不知道怎么说` | 提供简单英文句子开头，邀请尝试 |
| `Maya never checked the AI's answers.` | 基于文章纠正事实理解，而不是当作语法错误 |

## 8. 下一轮的改进方向
- 为纠错设计固定人工测试集与误报率评估。
- 长对话状态压缩、上下文 token 上限、模型费用统计。
- 明确欢迎问题/回合结束总结。
- 处理会话过期、并发安全、登录与数据库后再考虑多人部署。
- 合规新增真实新闻源，遵循 `docs/01-research-and-sources.md`。
