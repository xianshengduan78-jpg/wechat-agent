"""发布前总验证器。

合并所有验证器，全通过才允许 sync。
"""

import logging

from validation.article_validator import validate_article
from validation.title_validator import validate_title
from validation.daily_validator import validate_daily

logger = logging.getLogger(__name__)


def validate_before_sync(article: dict, events: list = None) -> dict:
    """发布前总验证。

    返回: {
        "passed": bool,
        "errors": {"article": [...], "title": [...], "daily": [...]},
    }
    """
    result = {"passed": True, "errors": {"article": [], "title": [], "daily": []}}

    # 1. 文章验证
    article_errors = validate_article(article)
    result["errors"]["article"] = article_errors

    # 2. 标题验证
    title = article.get("wechat_api_title") or article.get("article_title", "")
    title_errors = validate_title(title)
    result["errors"]["title"] = title_errors

    # 3. 日报专用验证
    if events:
        daily_errors = validate_daily(article, events)
        result["errors"]["daily"] = daily_errors

    # 汇总
    all_errors = []
    for category, errs in result["errors"].items():
        all_errors.extend(errs)

    if all_errors:
        result["passed"] = False
        logger.warning("发布前验证失败: %d 个问题", len(all_errors))
        for cat, errs in result["errors"].items():
            for e in errs:
                logger.warning("  [%s] %s", cat, e)
    else:
        logger.info("发布前验证通过")

    return result
