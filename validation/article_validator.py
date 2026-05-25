"""文章验证器。

字数检查、禁词检查、重复段落检测、格式检查。
"""

import re

# 禁止模板词
BANNED_PHRASES = [
    "值得关注的是", "这意味着", "核心变化", "底层逻辑", "赋能",
    "颠覆", "革命", "重塑一切", "未来已来",
    "从我的视角", "作为 AI 产品经理",
]

# 禁止时间词（"今日速览" 板块名除外）
BANNED_TIME_WORDS = ["今天", "昨天", "今日"]


def validate_article(article: dict) -> list:
    """验证文章，返回错误信息列表。空列表 = 通过。"""
    errors = []

    body = article.get("body_markdown", "")
    title = article.get("article_title", "")
    digest = article.get("digest", "")
    overviews = article.get("overview_lines", [])

    # 1. 字数检查（日报无上限，深度文章 800-1400）
    char_count = len(body)
    # 深度文章字数检查
    if "deep" in str(article.get("writing_mode", "")).lower() or len(body) > 800:
        if char_count < 800:
            errors.append(f"字数不足: {char_count} < 800")
        if char_count > 1400 and "daily" not in str(article.get("article_title", "")):
            errors.append(f"字数超限: {char_count} > 1400")

    # 2. 禁词检查
    for phrase in BANNED_PHRASES:
        if phrase in body:
            errors.append(f"包含禁词: {phrase}")

    # 3. 时间词检查（排除 "今日速览"）
    for tw in BANNED_TIME_WORDS:
        if tw in body and "今日速览" not in body:
            errors.append(f"包含时间词: {tw}")

    # 4. 重复段落检测
    paragraphs = [p.strip() for p in body.split("\n") if p.strip()]
    seen = set()
    for p in paragraphs:
        if p in seen:
            errors.append(f"重复段落: {p[:50]}")
        seen.add(p)

    # 5. digest 长度检查
    if len(digest) > 120:
        errors.append(f"摘要超长: {len(digest)} > 120 字")

    # 6. overview 检查
    for item in overviews:
        if len(item) > 22:
            errors.append(f"速览超长 (>22 字): {item}")

    return errors
