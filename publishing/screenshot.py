"""Playwright 截图模块。

支持 scroll-y、click-selector、clip-selector、wait-ms。
"""

import logging
from typing import Optional, Callable

from config.settings import SCREENSHOT_URL_MAP

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

logger = logging.getLogger(__name__)


def take_screenshot(url: str, output_path: str, **kwargs) -> bool:
    """对指定 URL 截图，保存到 output_path。

    Args:
        url: 目标 URL
        output_path: 截图保存路径
        kwargs:
            wait_ms: 等待毫秒数（默认 3000）
            scroll_y: 滚动像素
            click_selector: 点击选择器
            clip: 裁剪区域 {"x": int, "y": int, "width": int, "height": int}

    Returns:
        是否成功
    """
    if not HAS_PLAYWRIGHT:
        logger.warning("Playwright 未安装，跳过截图: %s", url)
        return False

    wait_ms = kwargs.get("wait_ms", 3000)
    scroll_y = kwargs.get("scroll_y")
    click_selector = kwargs.get("click_selector")
    clip = kwargs.get("clip")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(url, wait_until="networkidle", timeout=30000)

            if click_selector:
                page.click(click_selector)
                page.wait_for_timeout(1000)

            if scroll_y:
                page.evaluate(f"window.scrollBy(0, {scroll_y})")
                page.wait_for_timeout(500)

            page.wait_for_timeout(wait_ms)

            clip_obj = None
            if clip:
                clip_obj = {
                    "x": clip["x"],
                    "y": clip["y"],
                    "width": clip["width"],
                    "height": clip["height"],
                }

            page.screenshot(path=output_path, clip=clip_obj, full_page=not clip)
            browser.close()
            logger.info("截图成功: %s → %s", url, output_path)
            return True
    except Exception as e:
        logger.warning("截图失败 [%s]: %s", url, e)
        return False


def retry_screenshot(company: str, output_path: str) -> bool:
    """对指定公司截图，失败则尝试备用 URL。"""
    domain = SCREENSHOT_URL_MAP.get(company)
    if not domain:
        logger.warning("未知公司: %s", company)
        return False

    urls = [f"https://www.{domain}", f"https://{domain}"]

    for url in urls:
        if take_screenshot(url, output_path, wait_ms=3000):
            return True
        logger.info("重试截图: %s", url)

    return False
