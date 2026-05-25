"""标题生成模块。

5 类标题生成（信息型/反差型/用户型/选择型/趋势型）+ 封面文案。
"""

import logging

from llm.client import DeepSeekClient
from llm.prompts import TITLE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def generate_titles(article_body: str, article_title: str = None) -> dict:
    """生成 5 类标题和封面文案。

    返回: {title_candidates: [...], cover_title, cover_subtitle}
    """
    client = DeepSeekClient()

    content = f"文章标题：{article_title or ''}\n\n文章正文：\n{article_body}"

    messages = [
        {"role": "system", "content": TITLE_SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]

    logger.info("调 DeepSeek 生成标题...")
    result = client.chat_json(messages)

    if "title_candidates" not in result:
        raise ValueError("标题生成返回缺少 title_candidates")

    logger.info("标题生成完成: %d 个候选", len(result.get("title_candidates", [])))
    return result
