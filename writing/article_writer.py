"""深度文章写作模块。

两步调用：先出大纲 → 用户确认 → 写全文。
"""

import json
import logging

from llm.client import DeepSeekClient
from llm.prompts import ARTICLE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def write_outline(topic: str, references: list = None) -> dict:
    """第一步：出大纲。"""
    client = DeepSeekClient()

    user_content = f"选题：{topic}\n"
    if references:
        user_content += f"\n参考资料:\n{json.dumps(references, ensure_ascii=False, indent=2)}"

    messages = [
        {"role": "system", "content": ARTICLE_SYSTEM_PROMPT + "\n\n请输出大纲 JSON。"},
        {"role": "user", "content": user_content},
    ]

    logger.info("调 DeepSeek 生成大纲...")
    result = client.chat_json(messages)

    required = ["main_line", "headings", "not_write", "writing_mode"]
    for field in required:
        if field not in result:
            raise ValueError(f"大纲缺少必需字段: {field}")

    logger.info("大纲生成完成")
    return result


def write_full_article(topic: str, outline: dict, references: list = None) -> dict:
    """第二步：根据大纲写全文。"""
    client = DeepSeekClient()

    user_content = f"选题：{topic}\n\n大纲:\n{json.dumps(outline, ensure_ascii=False, indent=2)}\n"
    if references:
        user_content += f"\n参考资料:\n{json.dumps(references, ensure_ascii=False, indent=2)}"
    user_content += "\n\n请根据以上大纲写完整文章，输出 JSON。"

    messages = [
        {"role": "system", "content": ARTICLE_SYSTEM_PROMPT + "\n\n请输出全文 JSON。"},
        {"role": "user", "content": user_content},
    ]

    logger.info("调 DeepSeek 写全文...")
    result = client.chat_json(messages)

    required = ["article_title", "body_markdown", "title_candidates"]
    for field in required:
        if field not in result:
            raise ValueError(f"全文缺少必需字段: {field}")

    result["topic"] = topic
    result["outline"] = outline

    logger.info("全文生成完成: %s", result.get("article_title", ""))
    return result
