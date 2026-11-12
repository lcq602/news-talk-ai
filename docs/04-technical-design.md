# 04 · 技术架构与数据设计

状态：建议方案，非已实现系统。

## 1. 推荐技术栈
- Web 前端：Vue 3 + TypeScript + Vite + Pinia + Vue Router；响应式布局。
- API：Java 21 + Spring Boot 3 + Spring Web；SSE 流式输出；Spring AI **可选**，先保留可切换模型适配层。
- 内容抓取：先 Java RSS 适配器即可；Python 定时任务以后再考虑，避免 MVP 多服务负担。
- 数据库：PostgreSQL（用户、文章索引、许可状态、会话、词汇、复习）。
- Redis：可选，用于限流/缓存；早期本地开发可用数据库完成基本流程。
- AI：OpenAI-compatible 接口或提供商 SDK；服务端代理，不向浏览器泄露 Key。
- 部署：Docker Compose（web + api + postgres），反向代理 Caddy/Nginx 可选。

## 2. 分层
```text
Vue UI
  ├─ Discover / Reader / Chat / Vocabulary / Progress
  ↓ HTTPS + SSE
Spring Boot API
  ├─ Auth & User Preferences
  ├─ ContentCatalog (license-aware)
  ├─ Conversation / Tutor
  ├─ Vocabulary & Review
  ├─ AI Provider Gateway + Budget + Observability
  └─ Admin / Source Policies
  ↓
PostgreSQL + (optional Redis)
RSS/approved content provider ← ingestion job
```

## 3. 建议数据表（逻辑字段）
- users(id, email, password_hash, created_at, deleted_at)
- learner_profiles(user_id, practice_level, topics_json, correction_mode, zh_help_enabled)
- content_sources(id, name, home_url, feed_url, terms_url, terms_reviewed_at)
- content_rights(source_id, display_level, llm_allowed, caching_allowed, retention_days, review_status)
- articles(id, source_id, canonical_url, title, published_at, language, excerpt, body, body_origin, rights_snapshot_id, content_hash)
- conversations(id, user_id, article_id, article_version, level, state, created_at, finished_at)
- messages(id, conversation_id, sender, text, seq, token_input, token_output, created_at)
- vocab_items(id, user_id, expression, meaning_zh, sentence, source_message_id, next_review_at, review_stage)
- review_events(id, vocab_item_id, result, reviewed_at)
- model_usage(id, user_id, conversation_id, provider, model, input_tokens, output_tokens, estimated_cost_usd, occurred_at)

注：文章 body 可以为空；只有权利配置允许，才写入 body 并发往 LLM。

## 4. API 草案
```http
GET    /api/v1/articles?topic=technology&cursor=...
GET    /api/v1/articles/{id}
POST   /api/v1/conversations
GET    /api/v1/conversations/{id}
POST   /api/v1/conversations/{id}/messages/stream
POST   /api/v1/conversations/{id}/finish
GET    /api/v1/vocabulary
POST   /api/v1/vocabulary
POST   /api/v1/vocabulary/{id}/reviews
GET    /api/v1/progress?days=7
DELETE /api/v1/me/learning-data
```

SSE 类型建议：`message.started`, `message.delta`, `feedback.ready`, `message.completed`, `usage.ready`, `error`。后端以服务器权威计数和幂等键保护重复调用。

## 5. 新闻接入合法性“闸门”
```text
content rights unknown → catalog metadata only
display_allowed=true → reader eligible
llm_allowed=true → tutor may receive passage
cache_allowed=true → persistent storage with retention
rights expired/revoked → disable future LLM use; evaluate removal
```
不得因 feed 含有 `content:encoded` 就默认具备再发布、模型处理权；按照来源、具体授权和审查日期判断。

## 6. 模型成本管理
单次对话费用模型（不含其他平台收费）：
```text
cost = input_tokens / 1_000_000 * input_price
     + output_tokens / 1_000_000 * output_price
```
变量价格按当前供应商实时配置，不在文档中硬编码所谓“永久免费”。
- 每轮只发送文章摘要/必要段落 + 最近 4–8 轮对话 + 用户偏好；摘要只能从允许 AI 处理的文本产生。
- 对合规段落的教学提示做缓存；模型返回 JSON schema 校验失败重试次数受限。
- 每日用户 token 上限、单次最大输出、速率限制、成本仪表盘。
- 生产数据禁止不经许可用于模型训练；核对供应商的数据使用和保留条款。

## 7. 隐私、安全、风险
- Auth：密码哈希推荐 Argon2id/bcrypt，安全 Cookie/JWT 策略统一，不存明文密码。
- 服务端存储/调用 API key；输入长度限制、用户资源权限校验、日志脱敏。
- 提示注入防御：新闻文字和用户文本作为低信任数据；不得执行内部指令或调用危险操作。
- 第三方新闻授权记录可审计；允许内容下架与删除。
- SSE 断线重连时避免重复生成；OpenTelemetry/结构化日志记录请求链路。
- 明确隐私政策、保存期限与数据删除流程，尤其对话中可能包含用户隐私。

## 8. 推荐项目目录（待创建）
```text
news-talk-ai/
├─ README.md
├─ docs/
├─ frontend/    # Vue 3
├─ backend/     # Spring Boot
├─ deploy/      # compose / config templates
└─ .github/     # CI and issue templates
```
