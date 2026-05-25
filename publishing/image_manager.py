"""图片管理模块。

给每个事件分配截图，检查截图和事件一一对应。
"""

import logging
from pathlib import Path

from config.settings import SCREENSHOT_URL_MAP, OUTPUT_DIR

logger = logging.getLogger(__name__)


def assign_screenshots(events: list) -> dict:
    """为事件分配截图，返回 {event_index: screenshot_path}。

    截图规则（按优先级）：
    1. 事件公司名匹配 SCREENSHOT_URL_MAP
    2. 同公司事件共享截图
    3. 不匹配的跳过
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    screenshots_dir = OUTPUT_DIR / "images"
    screenshots_dir.mkdir(exist_ok=True)

    assignments = {}
    used_companies = set()

    for i, event in enumerate(events):
        source = event.get("source_name", "")
        company = _find_company(source)

        if not company:
            logger.debug("事件 %d 无匹配公司: %s", i, source)
            continue

        if company in used_companies:
            # 同公司用已截过的图
            continue

        # 标记需要截图
        screenshot_path = str(screenshots_dir / f"event-{i}.png")
        assignments[i] = {
            "company": company,
            "path": screenshot_path,
            "domain": SCREENSHOT_URL_MAP.get(company, ""),
        }
        used_companies.add(company)

    logger.info("截图分配: %d 个事件需截图", len(assignments))
    return assignments


def check_alignment(events: list, assignments: dict) -> list:
    """检查截图和事件是否对齐，返回问题列表。"""
    issues = []
    for i, event in enumerate(events):
        has_screenshot = i in assignments
        needs_image = bool(event.get("title", ""))

        if needs_image and not has_screenshot:
            issues.append(f"事件 {i} ({event.get('title', '')[:30]}) 缺少截图")

    if not issues:
        logger.info("截图-事件对齐检查通过")
    else:
        logger.warning("截图-事件对齐问题: %d 个", len(issues))

    return issues


def _find_company(source_name: str) -> str:
    """根据 source_name 找到匹配的公司名。"""
    source_lower = source_name.lower()
    for company in SCREENSHOT_URL_MAP:
        if company.lower() in source_lower:
            return company
        # 反向匹配
        if source_lower in company.lower():
            return company
    return ""
