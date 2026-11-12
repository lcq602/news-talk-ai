# 01 · 调研：教学依据、新闻来源与版权

状态：2026-11-12 调研快照。**所有第三方条款、价格、速率限制都可能变化，上线前必须重新检查原站文档并记录验证日期。**

## 1. 英语教学设计依据

### CEFR
欧盟理事会/欧洲委员会发布的 *Common European Framework of Reference for Languages: Companion Volume* 包括接受、产出、互动以及在线互动等描述。使用 A1–C2 作为用户自选程度和内容适配参考，但**不要仅凭一次 AI 对话宣称获得 CEFR 官方等级**。

产品映射（项目设计建议，非官方测试量表）：
- A1–A2：简短新闻简述、中文辅助词义、事实问题和 1–2 句回答。
- B1：简要复述、观点与原因、少量自我纠错。
- B2：比较立场、联系现实、反对意见与举例。
- C1：隐含假设、措辞偏见、证据和不确定性评价。

参考：https://www.coe.int/en/web/common-european-framework-reference-languages

### 检索练习、间隔复习与输出
学习目标不是只“看懂”，而是过一段时间依然能提取、使用表达。安排隔日/数日再次回忆和造句；学习词条以**本人对话出现过的短语**优先。
- 间隔练习在第二语言习得研究中有积极证据，但效果受间隔时间、练习形式影响，不保证所有用户收益相同。
- 讨论中通过复述和发表意见促进输出练习；AI 的纠错用建议而非绝对评分。

学术研究检索起点：https://scholar.google.com/scholar?q=spaced+practice+second+language+learning+meta+analysis

## 2. 新闻接入方式比较

| 来源类型 | 可做什么 | 风险与建议 |
|---|---|---|
| 官方 RSS（例如 BBC / NPR 的公开 feed） | 发现标题、来源、URL、feed 中提供的内容字段 | RSS 可读 ≠ 获得转载全文或 AI 处理授权；逐站核验 |
| 有明确协议的新闻 API | 按协议索引新闻、取允许的元数据/摘要 | 免费套餐可能仅限开发、不可商用、禁止持久化/AI 训练或处理 |
| 新闻链接 + 官方原站阅读 | 展示允许的标题和来源信息，点击打开原站 | 原站内容不能因为用户点开就自动抓取/转发模型 |
| 用户有权提供的文本、开放许可内容 | 正文内划词与正文级 AI 讨论 | 需核验原始版权和用户的处理权，不以“用户粘贴”自动推断许可 |
| 自写学习新闻简讯 | 将已核实的事实组织成原创教学文本 | 核对信息来源、来源署名、避免近似改写受保护原文 |

### 候选来源，待授权确认
- NPR RSS 说明及新闻来源：https://www.npr.org/rss/
- BBC News feeds：https://www.bbc.co.uk/news/10628494
- The Guardian Open Platform：https://open-platform.theguardian.com/
- NewsAPI：https://newsapi.org/pricing
- GDELT：https://www.gdeltproject.org/

**重要**：Guardian 的 Open Platform 条款和具体用途/计划可能对 AI/机器学习处理有限制；不应假定免费 Key 可以让模型读取文章正文。NewsAPI 免费开发套餐的生产/商业使用限制也需核验。GDELT 是新闻发现与研究数据来源，不代表授予原新闻版权。

## 3. 建议的来源策略

**Phase 0（优先）**：项目内置少量自主撰写、引用事实并附原文链接的英文学习短文；以及权利明确的开放许可样例。保证用户能体验完整“文章 → AI”。
**Phase 1**：接入 RSS 只用于标题、日期、来源链接与获准展示字段；不默认抓全文，不将未获授权正文发给模型。
**Phase 2**：联系来源/核验可用协议，再启用合法正文采集、缓存和正文级问答。
**用户提供内容**：设置用户确认其有权使用内容的提示和投诉/删除流程；仍需服务端限制长度、处理隐私和权利投诉。

## 4. 来源适配器的合规字段
source_id, provider, canonical_url, title, published_at, language,
license_type, terms_url, reviewed_at, excerpt_allowed, fulltext_display_allowed,
llm_processing_allowed, cache_allowed, retention_days, attribution_rule.

任何字段未知时采取最小权限：不抓取全文、不送入模型；只用获准的索引信息完成新闻发现。

## 5. 需验证的外部资料
- CEFR Companion Volume：https://www.coe.int/en/web/common-european-framework-reference-languages
- BBC RSS：https://www.bbc.co.uk/news/10628494
- NPR RSS：https://www.npr.org/rss/
- The Guardian Open Platform 及条款：https://open-platform.theguardian.com/
- NewsAPI 价格及使用限制：https://newsapi.org/pricing
- GDELT 数据概览：https://www.gdeltproject.org/
- 模型提供商计费、数据保留、安全文档：待选择具体供应商后核验。

## 6. 尚未完成的实证研究
未做真实用户访谈、竞品可用性测评、RSS API 连通性与正式版权法律审查；这些都是上线前待办，不应把以上候选视为已经通过。
