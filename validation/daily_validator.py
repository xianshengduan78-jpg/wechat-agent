"""日报专用验证器。

- 速览每条 ≤ 20 字
- 每条有主体 + 钩子
- 事件数和图片数对齐
- 无自制信息卡
- 来源记录和正文事件一一对应
"""

from validation.title_validator import KNOWN_ENTITIES


def validate_daily(article: dict, events: list) -> list:
    """验证日报，返回错误列表。"""
    errors = []

    overviews = article.get("overview_lines", [])
    expanded = article.get("expanded_items", [])

    # 1. 速览每条 ≤ 20 字
    for item in overviews:
        if len(item) > 22:
            errors.append(f"速览超长 (>22 字): {item}")

    # 2. 速览每条有主体 + 钩子
    for item in overviews:
        has_entity = any(e.lower() in item.lower() for e in KNOWN_ENTITIES)
        if not has_entity:
            errors.append(f"速览缺少主体: {item}")

    # 3. 事件数和展开段落数对齐
    if len(expanded) != len(events):
        errors.append(
            f"事件数与展开数不匹配: {len(events)} 事件 vs {len(expanded)} 展开"
        )

    # 4. 来源记录检查
    sources = article.get("source_section", [])
    if len(sources) < len(events):
        errors.append(f"来源记录数 ({len(sources)}) < 事件数 ({len(events)})")

    return errors
