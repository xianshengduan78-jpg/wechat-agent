"""封面图生成模块。

用 Pillow 生成微信封面图（wide 900x383 + square 900x900）。
"""

import logging
from pathlib import Path

from config.settings import OUTPUT_DIR, ASSETS_DIR

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

logger = logging.getLogger(__name__)

WIDE_SIZE = (900, 383)
SQUARE_SIZE = (900, 900)


def generate_daily_cover(article_title: str, digest: str, events: list = None) -> dict:
    """生成日报封面图。

    返回: {"wide": str, "square": str} 文件路径
    """
    if not HAS_PILLOW:
        logger.warning("Pillow 未安装，使用纯色占位封面")
        return _generate_fallback(article_title)

    cover_title = article_title.replace("AI早报｜", "")[:30]
    cover_subtitle = digest[:60] if digest else "AI 科技日报"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    wide_path = OUTPUT_DIR / "cover-wide.png"
    square_path = OUTPUT_DIR / "cover-square.png"

    _draw_cover(wide_path, WIDE_SIZE, cover_title, cover_subtitle)
    _draw_cover(square_path, SQUARE_SIZE, cover_title, cover_subtitle)

    logger.info("封面图已生成: wide=%s, square=%s", wide_path, square_path)
    return {"wide": str(wide_path), "square": str(square_path)}


def generate_article_cover(topic: str, cover_title: str = "", cover_subtitle: str = "") -> dict:
    """生成深度文章封面图。"""
    if not HAS_PILLOW:
        return _generate_fallback(topic)

    title = cover_title or topic[:30]
    subtitle = cover_subtitle or ""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    wide_path = OUTPUT_DIR / "cover-wide.png"
    square_path = OUTPUT_DIR / "cover-square.png"

    _draw_cover(wide_path, WIDE_SIZE, title, subtitle)
    _draw_cover(square_path, SQUARE_SIZE, title, subtitle)

    return {"wide": str(wide_path), "square": str(square_path)}


def _draw_cover(path: Path, size: tuple, title: str, subtitle: str):
    """绘制封面图。"""
    img = Image.new("RGB", size, color=(18, 18, 18))
    draw = ImageDraw.Draw(img)

    # 尝试加载字体
    font_title = _load_font(36)
    font_sub = _load_font(20)

    # 主标题（居中）
    if font_title:
        bbox = draw.textbbox((0, 0), title, font=font_title)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (size[0] - tw) // 2
        ty = (size[1] - th) // 2 - 20
        draw.text((tx, ty), title, fill=(255, 255, 255), font=font_title)

    # 副标题
    if subtitle and font_sub:
        bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
        sw = bbox[2] - bbox[0]
        sx = (size[0] - sw) // 2
        sy = ty + th + 10 if font_title else size[1] // 2
        draw.text((sx, sy), subtitle, fill=(180, 180, 180), font=font_sub)

    img.save(path, "PNG")


def _load_font(size: int):
    """加载字体，fallback 到默认。"""
    try:
        return ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", size)
    except (IOError, OSError):
        try:
            return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except (IOError, OSError):
            return None


def _generate_fallback(label: str) -> dict:
    """Pillow 不可用时的占位封面。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in ["cover-wide.png", "cover-square.png"]:
        path = OUTPUT_DIR / name
        # 生成一个 1x1 像素占位图
        if not path.exists():
            with open(path, "wb") as f:
                f.write(b"")
    return {"wide": str(OUTPUT_DIR / "cover-wide.png"), "square": str(OUTPUT_DIR / "cover-square.png")}
