# AGENTS.md — 微信公众号写作 Agent

## 项目目标

构建一个独立的 Python agent，自动完成：
- **内容线 A（AI 日报）**：自动抓取 AI 新闻 → 筛选评分 → 调 DeepSeek 写日报 → 生成封面和 HTML → 推送到微信公众号草稿箱
- **内容线 B（深度文章）**：推荐选题 → 用户确认 → 调 DeepSeek 写文章 → 生成封面和 HTML → 推送到草稿箱
- **数据闭环**：拉取公众号后台数据 → 分析表现 → 更新策略记忆 → 影响下次选题和写作

## 核心设计原则（Harness Engineering）

**流程控制在代码里，不在 LLM 里。** DeepSeek 只在"写文章"和"生成标题"时被调用。其他所有逻辑（抓取、筛选、去重、验证、发布）都是确定性的 Python 代码。

**三层架构：**
- **Information Layer**：每次调 DeepSeek 前，精确装配 context（不多不少）
- **Execution Layer**：代码驱动的 pipeline，每步有独立错误处理
- **Validation Layer**：DeepSeek 输出后必须过验证，失败则重试，不直接使用

**不可逆操作前必须有 human checkpoint：** 推送到微信草稿箱之前，打印预览，等用户确认。

---

## 技术栈

- Python 3.11+
- DeepSeek API（兼容 OpenAI SDK 格式）
- 微信公众号官方 API（access_token → 素材上传 → 草稿创建）
- Pillow（封面图生成）
- Playwright（官方页面截图）
- requests / httpx（HTTP 请求）
- python-dotenv（环境变量）
- SQLite（本地数据存储）

---

## 文件结构

```
wechat-agent/
│
├── AGENTS.md                ← 你正在读的这个文件
├── .env                     ← 环境变量（不入版本控制）
├── requirements.txt
├── main.py                  ← CLI 入口
│
├── config/
│   ├── __init__.py
│   └── settings.py          ← 所有常量、路径、阈值集中管理
│
├── llm/
│   ├── __init__.py
│   ├── client.py            ← DeepSeek API 封装（重试、超时、JSON 解析）
│   └── prompts.py           ← 所有 system prompt 模板集中管理
│
├── sources/
│   ├── __init__.py
│   ├── rss_fetcher.py       ← RSS 抓取（15 个官方 feed）
│   ├── aihot_fetcher.py     ← AIHOT API 聚合抓取
│   ├── search_fetcher.py    ← Tavily 搜索补充（官方域名限定）
│   └── pool_manager.py      ← 候选池管理（合并、去重、健康度检查、自动刷新）
│
├── selection/
│   ├── __init__.py
│   ├── scorer.py            ← 事件评分（综合分、眼球分、社区热度分）
│   ├── filter.py            ← 事件排除规则（时间窗口、来源、政策噪音）
│   ├── dedup.py             ← 去重逻辑（URL 去重、标题相似度、历史对比）
│   ├── diversifier.py       ← 来源多样性控制（单源上限、多源最低要求）
│   └── selector.py          ← 整合以上模块，输出最终事件列表
│
├── writing/
│   ├── __init__.py
│   ├── diagnosis.py         ← 选题诊断（类型判断、目标读者、结构推荐）
│   ├── daily_writer.py      ← 日报写作（调 DeepSeek → 验证 → 重试）
│   ├── article_writer.py    ← 深度文章写作（先大纲 → 确认 → 写全文）
│   └── title_generator.py   ← 标题生成（5 类标题 + 封面文案）
│
├── publishing/
│   ├── __init__.py
│   ├── html_builder.py      ← Markdown → 微信兼容 HTML
│   ├── cover_generator.py   ← 封面图生成（wide + square）
│   ├── screenshot.py        ← Playwright 截图
│   ├── wechat_api.py        ← 微信 API 封装（token、素材上传、草稿创建）
│   └── image_manager.py     ← 截图分配、图片和事件对齐
│
├── validation/
│   ├── __init__.py
│   ├── article_validator.py ← 文章验证（字数、禁词、时间词、模板腔、重复段落）
│   ├── title_validator.py   ← 标题验证（≤30 字、有主体+钩子、无冒号破折号）
│   ├── daily_validator.py   ← 日报专用验证（速览 ≤20 字、事件-图片对齐、来源记录完整）
│   └── sync_validator.py    ← 发布前总验证（合并以上检查，全通过才允许 sync）
│
├── memory/
│   ├── __init__.py
│   ├── strategy_memory.py   ← 策略记忆（选题偏好、标题策略、封面策略）
│   ├── event_history.py     ← 已发事件历史（去重用）
│   ├── content_memory.py    ← 公众号共同记忆（写作风格、平台规则）
│   └── stats_fetcher.py     ← 微信后台数据拉取（datacube 接口）
│
├── pipelines/
│   ├── __init__.py
│   ├── daily_pipeline.py    ← 日报完整流程（10 步 pipeline）
│   ├── article_pipeline.py  ← 深度文章完整流程（含人工确认节点）
│   └── loop_pipeline.py     ← 数据闭环（拉数据 → 分析 → 更新策略）
│
├── data/                    ← 运行时数据（git ignore）
│   ├── topic-pool.json
│   ├── daily-event-history.json
│   ├── strategy-memory.json
│   ├── performance-history.json
│   └── content-db.sqlite
│
├── output/                  ← 每次运行的输出（git ignore）
│   ├── article.md
│   ├── article-wechat.html
│   ├── cover.png / cover-wide.png / cover-square.png
│   ├── images/
│   ├── sources.json
│   ├── topic-selection-report.md
│   ├── structure-plan.md
│   ├── title-plan.md
│   └── publish-checklist.md
│
├── templates/
│   ├── wechat-html-template.html
│   └── checklist-template.md
│
└── assets/
    └── daily-24h-header.png
```

---

## 分步实施计划

严格按以下顺序实施。每完成一步，测试通过后再进入下一步。

### Phase 1：骨架 + DeepSeek 调通

**目标：能调 DeepSeek 写一段文字并拿到结构化 JSON 返回。**

1. 创建 `config/settings.py`：
   - 定义所有路径常量（DATA_DIR, OUTPUT_DIR, ASSETS_DIR 等）
   - 定义所有阈值常量（MIN_EVENTS=8, MAX_EVENTS=16, PRIMARY_WINDOW_HOURS=24 等）
   - 定义大厂域名列表（BIG_TECH_DOMAINS）
   - 从 .env 读取 DEEPSEEK_API_KEY, WECHAT_APPID, WECHAT_APPSECRET, TAVILY_API_KEY

2. 创建 `llm/client.py`：
   - 封装 DeepSeek API 调用（兼容 OpenAI SDK 格式）
   - base_url = "https://api.deepseek.com/v1"
   - model = "deepseek-chat"
   - 支持：普通调用 + JSON mode（response_format={"type": "json_object"}）
   - 内置重试逻辑（最多 3 次，指数退避）
   - 内置超时处理（默认 120 秒）
   - 返回值自动解析 JSON，解析失败则重试

3. 创建 `llm/prompts.py`：
   - DAILY_SYSTEM_PROMPT：日报写作的 system prompt
   - ARTICLE_SYSTEM_PROMPT：深度文章写作的 system prompt
   - TITLE_SYSTEM_PROMPT：标题生成的 system prompt
   - 每个 prompt 都从下方「写作规则」章节提炼

4. 创建 `main.py`：
   - CLI 入口，支持 `--daily`, `--article "选题"`, `--loop`, `--dry-run`
   - 先只实现一个 `--test` 命令：调 DeepSeek 写一句话，验证能跑通

5. 创建 `.env` 和 `requirements.txt`

**测试方法：** `python main.py --test` 能输出 DeepSeek 返回的文字。

### Phase 2：数据抓取 + 事件筛选

**目标：能从 RSS/AIHOT/搜索抓取 AI 新闻，筛选出 12-16 条高质量事件。**

6. 创建 `sources/rss_fetcher.py`：
   - 抓取 15 个官方 RSS feed（列表见下方「RSS 源列表」）
   - 解析 XML，提取 title/link/pubDate/summary
   - 过滤非 AI 相关条目
   - 返回标准化事件列表

7. 创建 `sources/aihot_fetcher.py`：
   - 从 AIHOT API (https://aihot.virxact.com/api/public/items) 抓取过去 24h 精选
   - 转为标准化事件格式

8. 创建 `sources/search_fetcher.py`：
   - 用 Tavily API 搜索 10 个大厂官方域名
   - 每个域名限定 site: 搜索
   - 提取时间证据（snippet 日期、页面 meta、URL 日期）

9. 创建 `sources/pool_manager.py`：
   - 合并三个来源的事件
   - URL 去重
   - 健康度检查（合格事件数 >= 阈值 && 来源数 >= 3）
   - 不够时自动触发搜索补充
   - 写入 data/topic-pool.json

10. 创建 `selection/scorer.py`：
    - 综合评分 = 眼球分×2 + 用户相关性×2 + 时效性 + 官方分 + 产品价值 + 账号匹配 + 社区热度
    - 眼球分：关键词匹配（免费、降价、开放、Agent、图片等）
    - 高表现类型 +5，低表现类型 -8

11. 创建 `selection/filter.py`：
    - 排除规则：无可靠时间 → 排除；超过 48h 窗口 → 排除；非大厂来源 → 排除；政策/军方噪音 → 排除；用户关注度 < 12 → 排除；社区热度 < 8 → 排除

12. 创建 `selection/dedup.py`：
    - URL 标准化去重
    - 标题相似度计算（字符 bigram Jaccard，阈值 0.72）
    - 对比 data/daily-event-history.json 和历史文章标题

13. 创建 `selection/diversifier.py`：
    - 单源上限（默认 4 条/源）
    - 来源多样性最低要求（至少 3 个不同来源）

14. 创建 `selection/selector.py`：
    - 整合以上模块
    - 输出：selected_events（入选）+ excluded_events（排除+原因）
    - 写入 topic-selection-report.md

**测试方法：** `python main.py --daily --dry-run` 能输出筛选后的事件列表和排除报告。

### Phase 3：写作 + 验证

**目标：能用 DeepSeek 写出完整日报，通过所有验证。**

15. 创建 `writing/diagnosis.py`：
    - diagnose_topic()：根据关键词判断选题类型、目标读者、推荐结构
    - 结构库映射（A-H 八种结构）
    - 返回 structure-plan

16. 创建 `writing/daily_writer.py`：
    - 输入：筛选后的事件列表 + 策略记忆 + 写作风格
    - 装配 context → 调 DeepSeek（JSON mode）→ 解析返回
    - DeepSeek 返回格式：{article_title, wechat_api_title, digest, body_markdown, title_candidates}
    - 失败重试（最多 2 次）

17. 创建 `writing/article_writer.py`：
    - 两步调用：先出大纲 JSON → 打印给用户确认 → 确认后写全文
    - 装配 context 包含：选题诊断 + 参考资料 + 写作风格 + 策略记忆

18. 创建 `writing/title_generator.py`：
    - 5 类标题生成（信息型、反差型、用户型、选择型、趋势型）
    - 封面文案生成（cover_title 4-8 字 + cover_subtitle 10-20 字）

19. 创建 `validation/article_validator.py`：
    - 字数检查（日报无硬性上限，深度文章 800-1400 字）
    - 禁止时间词（"今天""昨天""今日"，"今日速览"板块名除外）
    - 禁止模板腔（"值得关注的是""这意味着""颠覆""革命""未来已来"）
    - 重复段落检测
    - 输出格式检查（必须是合法 JSON，必须包含所有必需字段）

20. 创建 `validation/title_validator.py`：
    - 标题 ≤ 30 字
    - 无冒号（：）、无破折号（——）
    - 必须有主体（公司/产品名）
    - 必须有钩子（不能只是"XX 发布""XX 更新"）

21. 创建 `validation/daily_validator.py`：
    - 速览每条 ≤ 20 字
    - 每条有主体 + 钩子
    - 事件数和图片数对齐
    - 无自制信息卡
    - 来源记录和正文事件一一对应

22. 创建 `validation/sync_validator.py`：
    - 合并所有验证器
    - 全部通过返回 True
    - 任何失败返回具体错误信息
    - 不通过 → 不允许调微信 API

**测试方法：** `python main.py --daily --dry-run` 能生成完整日报 article.md，通过所有验证。

### Phase 4：发布流程

**目标：能生成封面、HTML，推送到微信草稿箱。**

23. 创建 `publishing/html_builder.py`：
    - 读取 article.md → 转为微信兼容 HTML
    - 使用 templates/wechat-html-template.html 作为模板
    - 替换本地图片路径为微信图片 URL（在上传后）

24. 创建 `publishing/cover_generator.py`：
    - 用 Pillow 生成封面图
    - 日报封面：用入选事件中最有代表性的截图 + 短钩子主标题 + 副标题
    - 深度文章封面：根据选题类型自动选模板
    - 输出：cover.png (900x383) + cover-wide.png (900x383) + cover-square.png (900x900)

25. 创建 `publishing/screenshot.py`：
    - Playwright 截图封装
    - 支持 scroll-y、click-selector、clip-selector、wait-ms
    - 截图失败处理（换同公司 URL 重试一次）

26. 创建 `publishing/image_manager.py`：
    - 给每个事件分配截图
    - 按截图规则表匹配 URL（Google→google.com, Anthropic→anthropic.com 等）
    - 检查截图和事件一一对应

27. 创建 `publishing/wechat_api.py`：
    - get_access_token(appid, appsecret)
    - upload_thumb_material(token, image_path) → thumb_media_id
    - upload_article_image(token, image_path) → wechat_url
    - create_draft(token, articles) → media_id
    - 错误处理：40164(IP白名单)、40013(AppID错)、40125(AppSecret错)、48001(无权限)

28. 创建 `pipelines/daily_pipeline.py`：
    ```
    def run_daily(dry_run=False):
        # Step 1: 加载策略记忆
        # Step 2: 刷新候选池（RSS + AIHOT + 搜索）
        # Step 3: 筛选事件（评分 + 过滤 + 去重 + 多样性）
        # Step 4: 写选题报告
        # Step 5: 调 DeepSeek 写日报
        # Step 6: 验证文章（字数、禁词、格式）
        # Step 7: 截图 + 分配图片
        # Step 8: 生成封面 + HTML
        # Step 9: Human checkpoint（打印预览，等 y）
        # Step 10: 上传素材 + 创建草稿
        # Step 11: 记录历史
    ```

29. 创建 `pipelines/article_pipeline.py`：
    ```
    def run_article(topic, dry_run=False):
        # Step 1: 选题诊断
        # Step 2: 搜索参考资料
        # Step 3: 调 DeepSeek 出大纲 → 打印 → 等用户确认
        # Step 4: 调 DeepSeek 写全文
        # Step 5: 验证
        # Step 6: 截图 + 封面 + HTML
        # Step 7: Human checkpoint
        # Step 8: 上传 + 创建草稿
    ```

**测试方法：** `python main.py --daily` 完整跑通，微信草稿箱能看到日报。

### Phase 5：数据闭环

**目标：能拉后台数据，分析表现，更新策略记忆。**

30. 创建 `memory/strategy_memory.py`：
    - load() / save()
    - 包含：高/低表现事件类型、推荐事件数、标题策略、封面策略、写作备注

31. 创建 `memory/event_history.py`：
    - load() / append() / deduplicate()
    - 每次成功发布后追加入选事件

32. 创建 `memory/stats_fetcher.py`：
    - 调微信 datacube 接口拉取文章数据
    - GET https://api.weixin.qq.com/datacube/getarticletotal
    - 拉取：阅读数、分享数、收藏数、新增关注、取消关注
    - 写入 data/performance-history.json

33. 创建 `pipelines/loop_pipeline.py`：
    ```
    def run_loop():
        # Step 1: 拉后台数据（最近 7 天）
        # Step 2: 分析表现（按事件类型、标题类型、封面类型分组）
        # Step 3: 更新 strategy-memory.json
        # Step 4: 生成分析报告
    ```

**测试方法：** `python main.py --loop` 能拉到数据并更新策略记忆。

---

## .env 格式

```env
# 必需
DEEPSEEK_API_KEY=sk-xxx
WECHAT_APPID=wx-xxx
WECHAT_APPSECRET=xxx

# 可选（用于搜索补充候选池）
TAVILY_API_KEY=tvly-xxx

# 可选
WECHAT_COVER_LABEL=
```

---

## requirements.txt

```
requests>=2.31.0
httpx>=0.28.0
python-dotenv>=1.0.0
Pillow>=10.0.0
playwright>=1.40.0
beautifulsoup4>=4.12.0
```

注意：不用 openai SDK。DeepSeek API 兼容 OpenAI 格式，直接用 httpx 调。

---

## RSS 源列表

在 `sources/rss_fetcher.py` 中硬编码以下 15 个官方 feed：

```python
FEEDS = [
    ("OpenAI", "OpenAI News", "https://openai.com/news/rss.xml"),
    ("Google", "Google Blog", "https://blog.google/rss/"),
    ("Google DeepMind", "DeepMind Blog", "https://deepmind.google/blog/rss.xml"),
    ("GitHub", "GitHub Changelog", "https://github.blog/changelog/feed/"),
    ("AWS", "AWS ML Blog", "https://aws.amazon.com/blogs/machine-learning/feed/"),
    ("NVIDIA", "NVIDIA GenAI Blog", "https://developer.nvidia.com/blog/category/generative-ai/feed/"),
    ("Hugging Face", "HF Blog", "https://huggingface.co/blog/feed.xml"),
    ("Together AI", "Together Blog", "https://together.ai/blog/rss.xml"),
    ("Product Hunt", "PH AI", "https://www.producthunt.com/feed?category=ai"),
    ("Simon Willison", "Simon Blog", "https://simonwillison.net/atom/everything/"),
    ("Andrej Karpathy", "Karpathy Blog", "https://karpathy.bearblog.dev/feed/"),
    ("Chip Huyen", "Chip Blog", "https://huyenchip.com/feed.xml"),
    ("Ethan Mollick", "One Useful Thing", "https://www.oneusefulthing.org/feed"),
    ("Import AI", "Jack Clark", "https://jack-clark.net/feed/"),
]
```

---

## 大厂域名列表

在 `config/settings.py` 中定义：

```python
BIG_TECH_DOMAINS = [
    "openai.com", "anthropic.com", "google.com", "deepmind.google",
    "blog.google", "developers.googleblog.com", "meta.com", "ai.meta.com",
    "apple.com", "nvidia.com", "x.ai", "microsoft.com", "github.com",
    "amazon.com", "aws.amazon.com", "huggingface.co", "together.ai",
    "producthunt.com", "simonwillison.net", "karpathy.bearblog.dev",
    "huyenchip.com", "oneusefulthing.org", "jack-clark.net", "arxiv.org",
]
```

---

## 截图 URL 规则表

在 `publishing/image_manager.py` 中使用：

```python
SCREENSHOT_URL_MAP = {
    "Google": "google.com",
    "Anthropic": "anthropic.com",
    "AWS": "aws.amazon.com",
    "NVIDIA": "nvidia.com",
    "GitHub": "github.com",
    "Cloudflare": "cloudflare.com",
    "DeepSeek": "deepseek.com",
    "Meta": "meta.com",
    "Microsoft": "microsoft.com",
    "OpenAI": "openai.com",
}
```

规则：截公司首页，不截具体文章页。截不到 → 换同公司另一个 URL → 再失败才用已有截图。禁止截 HN/Reddit（反爬）、禁止自制文字卡片。

---

## 微信 API 端点

```python
# access_token
TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"

# 永久素材上传（封面图）
MATERIAL_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"

# 正文图片上传
UPLOAD_IMG_URL = "https://api.weixin.qq.com/cgi-bin/media/uploadimg"

# 草稿创建
DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"

# 草稿获取
DRAFT_GET_URL = "https://api.weixin.qq.com/cgi-bin/draft/get"

# 草稿更新
DRAFT_UPDATE_URL = "https://api.weixin.qq.com/cgi-bin/draft/update"

# 数据统计（阅读量等）
DATACUBE_URL = "https://api.weixin.qq.com/datacube/getarticletotal"
```

---

## 写作规则（塞进 DeepSeek prompt）

以下规则是从 3 万字 SKILL.md + writing-style.md + daily-24h-rules.md 中提炼的核心，必须写进 `llm/prompts.py` 的 system prompt 里。

### 通用写作风格

```
你是微信公众号 AI 科技内容编辑。

写作原则：
- 写中文，用人话，短句，先事实后判断
- 必须有判断。没有判断的文章是新闻通稿
- 判断必须有态度且具体。好判断："说白了，卖 API 的增长到头了"。坏判断："这标志着 AI 行业进入了新阶段"
- 结尾不要总结，可以是一个观察、一个问题、或者直接停
- 每篇文章有自己的主线，小标题贴合选题
- 先从读者能感知的变化切入

禁止：
- 新闻通稿腔、论文腔、营销腔
- "颠覆""革命""重塑一切""未来已来"
- "值得关注的是""这意味着""核心变化""底层逻辑""赋能"
- "作为 AI 产品经理""从我的视角"
- 每条展开都用同一种结构开头
- 连续两段以"据XX报道"开头

数字规范：
- 美元金额：用"亿美元/万美元"，不用 $
- 百分比：用 10%，不写 ten percent
- 下载量：2200 万，不写 22M
```

### 日报专用规则

```
你正在写一篇 AI 日报（AI早报）。

输入：我会给你一个 JSON 数组，每个元素是一条 AI 事件，包含 title, summary, source_name, user_hook 等字段。

输出：严格返回 JSON，字段为：
- article_title: 标题，格式为 "AI早报｜信号1，信号2，信号3"
- wechat_api_title: 同 article_title
- digest: 摘要，≤120 字，无时间词
- overview_lines: 速览列表，每条 ≤20 字，格式为 "主体 + 钩子"
- expanded_items: 每条事件的展开段落，每条 100-220 字
- source_section: 来源列表，短链接格式

写作要求：
- 速览每条必须有主体（公司/产品名）AND 钩子（为什么值得看）
- 展开段落不要每条都用同一种开头
- 有的事件只需 40-60 字 + 配图（数字本身就够说明力的）
- 有的事件需要 200-300 字（结构性变化、反直觉数据）
- 全文禁止"今天""昨天""今日"（"今日速览"板块名除外）
- 不要写"这类变化值得关注，不是因为它热闹"之类套话
```

### 深度文章专用规则

```
你正在写一篇微信公众号深度文章。

输入：选题、结构计划、参考资料。

第一步：输出大纲 JSON：
- main_line: 文章主线（一句话）
- headings: 小标题列表（3-5 个，贴合选题，不用固定模板）
- not_write: 这篇文章不应该写什么
- writing_mode: 写法模式（观察笔记/问题拆解/使用场景/避坑提醒/对比选择/观点短评）

第二步（用户确认后）：输出全文 JSON：
- article_title, wechat_api_title, digest, body_markdown
- title_candidates: 5 类标题（信息型/反差型/用户型/选择型/趋势型）
- cover_title: 4-8 字，有反差/变化/停顿感
- cover_subtitle: 10-20 字

正文要求：
- 800-1400 字
- 不要把标题备选、创作判断、结构标签写进正文
- 不要按角色分栏（"对普通用户来说""对产品经理来说"）
- 小标题不要用"发生了什么/为什么重要/对用户有什么影响"
```

---

## 标题规则（影视飓风方法论）

标题验证器 `validation/title_validator.py` 需要检查这些硬性规则：

1. 大标题一口气读完，≤ 30 字
2. 用逗号自然断句，不用冒号（：）和破折号（——）
3. 每条标题必须有主体（公司/产品名）
4. 速览每条 ≤ 20 字，上限绝对不超过 22 字
5. 小标题也是一句话，不用冒号断开
6. 禁止相对时间词："今天""昨天""今日"（"今日速览"板块名除外）

标题公式参考（写进 prompt）：
- 数字 + 付出 + 结果
- 反常识
- 痛点 + 利益承诺
- 恐惧/焦虑诉求
- 结果前置 + 悬念
- 对比实测 + 意外
- 否定问题本身

---

## 事件标准化格式

所有来源（RSS/AIHOT/搜索）都必须输出统一的事件格式：

```python
{
    "title": str,           # 事件标题
    "summary": str,         # 摘要（≤260 字）
    "source_name": str,     # 来源名称（OpenAI/Google 等）
    "source_url": str,      # 来源 URL
    "event_type": str,      # 事件类型
    "published_at": str,    # ISO 时间戳
    "time_reason": str,     # 时间证据来源
    "freshness": int,       # 时效性分（0-20）
    "official_score": int,  # 官方分（0-20）
    "user_relevance": int,  # 用户相关性（0-20）
    "product_value": int,   # 产品价值（0-20）
    "account_fit": int,     # 账号匹配（0-20）
    "community_signal_score": int,  # 社区热度（0-20）
    "user_hook": str,       # 用户钩子
    "overview": str,        # 速览短标题（≤20 字）
}
```

---

## 关键设计决策说明

### 为什么不用 OpenAI SDK？
DeepSeek API 兼容 OpenAI 格式，但直接用 httpx 调更轻量、更可控。避免 SDK 版本升级带来的兼容性问题。

### 为什么筛选逻辑不用 LLM？
筛选是确定性规则（时间窗口、域名匹配、分数阈值）。用代码做永远不会忘记规则、永远不会跳步骤。这是 Harness Engineering 的核心：能用代码做的不用 LLM。

### 为什么发布前要 human checkpoint？
微信草稿创建是不可逆操作（会占用素材额度）。LLM 偶尔会写错事实、立场偏激、或格式异常。人工确认是最后一道防线。

### 为什么 DeepSeek prompt 要用 JSON mode？
自然语言输出格式不稳定——有时多废话、有时少字段。JSON mode 强制结构化输出，验证层可以直接 json.loads() 检查。

### 为什么要分 pipeline 和 tool？
Pipeline 是完整流程（10 步）。Tool 是单个功能（截图、上传）。Pipeline 调 tool，但 tool 不知道 pipeline。这样每个 tool 可以独立测试。
