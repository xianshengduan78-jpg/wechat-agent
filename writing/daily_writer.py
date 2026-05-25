"""日报写作模块。

调 DeepSeek（JSON mode）写日报，验证后返回。
"""

import json
import logging

from llm.client import DeepSeekClient
from llm.prompts import DAILY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def write_daily(events: list, strategy_memory: dict = None) -> dict:
    """调 DeepSeek 写 AI 日报。

    输入：筛选后的事件列表 + 策略记忆
    输出：{article_title, wechat_api_title, digest, body_markdown, title_candidates}
    """
    if not events:
        raise ValueError("事件列表为空，无法生成日报")

    client = DeepSeekClient()

    # 装配 context：事件列表 + 策略记忆
    user_content = "请根据以下 AI 事件列表，写一篇 AI 日报。\n\n"
    user_content += f"事件列表（共 {len(events)} 条）:\n"
    user_content += json.dumps(events, ensure_ascii=False, indent=2)

    if strategy_memory:
        user_content += "\n\n策略记忆:\n"
        user_content += json.dumps(strategy_memory, ensure_ascii=False, indent=2)

    messages = [
        {"role": "system", "content": DAILY_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    logger.info("调 DeepSeek 写日报...")
    result = client.chat_json(messages)

    # 验证基本字段
    required_fields = ["article_title", "wechat_api_title", "digest", "overview_lines", "expanded_items"]
    for field in required_fields:
        if field not in result:
            raise ValueError(f"DeepSeek 返回缺少必需字段: {field}")

    result["body_markdown"] = _build_body(result)

    logger.info("日报生成完成: %s", result.get("article_title", ""))
    return result


def _build_body(result: dict) -> str:
    """从 overview_lines + expanded_items 构建 markdown 正文。"""
    lines = []

    # header
    lines.append(f"# {result.get('article_title', 'AI 早报')}\n")

    # 今日速览
    lines.append("## 今日速览\n")
    overviews = result.get("overview_lines", [])
    if isinstance(overviews, list):
        for item in overviews:
            lines.append(f"- {item}")
    lines.append("")

    # 展开
    lines.append("## 正文\n")
    items = result.get("expanded_items", [])
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                lines.append(item.get("text", str(item)))
            else:
                lines.append(str(item))
            lines.append("")

    # 来源
    sources = result.get("source_section", [])
    if isinstance(sources, list) and sources:
        lines.append("## 来源\n")
        for src in sources:
            lines.append(f"- {src}")

    return "\n".join(lines)
