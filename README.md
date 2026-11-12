# NewsTalk AI

> Read the news. Talk with AI. Improve your English.

NewsTalk AI 帮助用户通过阅读英文文章，与 AI 讨论文章主题，同时得到详细、准确、可理解的英语表达纠错。

## ✅ Python MVP（已提交代码，待配置自己的模型 API 实测）

第一版只提供：**一篇自定义英文文章 + 简单网页 + OpenAI 兼容接口 + AI 英语教练全面纠错**。

- **后端**：Python 3.11 + FastAPI + httpx，使用 uv 管理依赖
- **前端**：纯 HTML/CSS/JS，无需 Node.js
- **文章**：[content/article.md](content/article.md)（原创虚构练习材料，不是真实新闻）
- **AI 角色提示词**：[prompts/english_tutor.md](prompts/english_tutor.md)
- **详细运行与验收说明**：[docs/06-python-mvp.md](docs/06-python-mvp.md)

### Windows 运行

```powershell
git clone https://github.com/lcq602/news-talk-ai.git
cd news-talk-ai
Copy-Item .env.example .env
# 在 .env 中填写 OPENAI_BASE_URL、OPENAI_API_KEY、OPENAI_MODEL
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

浏览器访问 **http://127.0.0.1:8000**。在另一个终端执行 `uv run pytest -q` 测试（测试使用模拟模型，不需要真实 API key）。

`.env` 不可提交到 GitHub。模型服务要求兼容 `POST /chat/completions`。这版为**单机内存会话**，无登录与生产级限流，请勿公开部署到互联网。无流式输出、无数据库、无新闻抓取。尚未在真实第三方模型上进行端到端测试。

### 英语纠错策略

每轮会针对**拼写、语法、用词、自然度、标点与表达清晰度**检查所有明确且有学习价值的问题，输出逐条中文解释、完整英文润色句、话题回应和下一问。真正没有明显错误时不为了填满列表而虚构纠错；自然度建议也不能混同为语法错误。具体行为见 [Tutor Prompt](prompts/english_tutor.md)。

## 远期规划（不是本次 MVP 功能）

新闻发现 → 授权文章阅读 → AI 讨论 → 纠错 → 单词收藏 → 间隔复习。新闻正文用于转载或交给 AI 处理前必须确认相应许可。

## 文档导航

| 文档 | 内容 |
|---|---|
| [00-产品愿景与范围](docs/00-product-vision.md) | 定位与目标 |
| [01-调研与来源合规](docs/01-research-and-sources.md) | 教学研究与新闻版权 |
| [02-产品需求 PRD](docs/02-prd.md) | 产品需求及验收 |
| [03-用户流程与 AI 教学](docs/03-user-flows-and-ai-tutor.md) | 学习流程和对话策略 |
| [04-技术架构](docs/04-technical-design.md) | 未来架构参考 |
| [05-里程碑与验证](docs/05-roadmap-and-validation.md) | 迭代计划 |
| [06-Python MVP](docs/06-python-mvp.md) | **当前可运行版本的说明和限制** |

最后更新：2026-11-12
