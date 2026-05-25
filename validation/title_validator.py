"""标题验证器。

硬性规则：
- 标题 ≤ 30 字
- 无冒号（：）、无破折号（——）
- 必须有主体（公司/产品名）
- 禁止相对时间词
"""

import re

# 常见公司/产品名（用于检查是否有主体）
KNOWN_ENTITIES = [
    "OpenAI", "Google", "Anthropic", "Meta", "Microsoft", "Apple",
    "NVIDIA", "AWS", "GitHub", "DeepSeek", "Mistral", "Hugging Face",
    "Claude", "GPT", "Gemini", "Llama", "Copilot", "ChatGPT",
    "Product Hunt", "Cloudflare", "Together AI", "Perplexity",
    "Notion", "Cursor", "Windsurf", "Bolt", "Claude Code",
    "iPhone", "iPad", "Mac", "Vision Pro",
]

BANNED_TIME = ["今天", "昨天", "今日"]


def validate_title(title: str) -> list:
    """验证单条标题，返回错误列表。空列表 = 通过。"""
    errors = []

    # 1. 长度 ≤ 30 字
    if len(title) > 30:
        errors.append(f"标题超长: {len(title)} > 30 字")

    # 2. 无冒号
    if "：" in title:
        errors.append("包含中文冒号（：）")

    # 3. 无破折号
    if "——" in title or "──" in title:
        errors.append("包含破折号（——）")

    # 4. 必须有主体
    has_entity = any(entity.lower() in title.lower() for entity in KNOWN_ENTITIES)
    if not has_entity:
        errors.append("缺少主体（公司/产品名）")

    # 5. 禁止时间词
    for tw in BANNED_TIME:
        if tw in title:
            errors.append(f"包含时间词: {tw}")

    return errors


def validate_all_titles(title_candidates: list) -> list:
    """验证所有候选标题，返回所有错误。"""
    all_errors = []
    for t in title_candidates:
        errors = validate_title(t)
        if errors:
            all_errors.append({"title": t, "errors": errors})
    return all_errors
