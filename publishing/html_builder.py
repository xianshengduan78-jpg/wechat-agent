"""Markdown → 微信兼容 HTML 转换。"""

import re
import logging
from pathlib import Path

from config.settings import TEMPLATES_DIR

logger = logging.getLogger(__name__)


def build_html(markdown_text: str, title: str = "", image_map: dict = None) -> str:
    """将 Markdown 正文转为微信兼容 HTML。

    Args:
        markdown_text: Markdown 正文
        title: 文章标题
        image_map: 本地路径 → 微信 URL 的映射

    Returns:
        完整的微信兼容 HTML 字符串
    """
    # 1. Markdown → HTML 块转换
    html_body = _md_to_html(markdown_text, image_map or {})

    # 2. 套模板
    template_path = TEMPLATES_DIR / "wechat-html-template.html"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    else:
        template = "<!DOCTYPE html><html><body>{% body %}</body></html>"

    html = template.replace("{% title %}", _escape_html(title))
    html = html.replace("{% body %}", html_body)

    html = _wechat_format(html)

    return html


def _md_to_html(md: str, image_map: dict) -> str:
    """简单的 Markdown → HTML 转换。"""
    lines = md.split("\n")
    html_parts = []
    in_list = False

    for line in lines:
        # 标题
        if line.startswith("### "):
            _close_list(html_parts, in_list)
            in_list = False
            html_parts.append(f'<h3>{_escape_html(line[4:])}</h3>')
        elif line.startswith("## "):
            _close_list(html_parts, in_list)
            in_list = False
            html_parts.append(f'<h2>{_escape_html(line[3:])}</h2>')
        elif line.startswith("# "):
            _close_list(html_parts, in_list)
            in_list = False
            html_parts.append(f'<h1>{_escape_html(line[2:])}</h1>')
        # 列表项
        elif line.startswith("- ") or line.startswith("* "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f'<li>{_escape_html(line[2:])}</li>')
        # 空行
        elif not line.strip():
            _close_list(html_parts, in_list)
            in_list = False
        # 图片
        elif line.startswith("!["):
            img_html = _convert_img(line, image_map)
            html_parts.append(f'<p>{img_html}</p>')
        # 段落
        else:
            _close_list(html_parts, in_list)
            in_list = False
            processed = _escape_html(line)
            processed = _process_inline(processed)
            html_parts.append(f'<p>{processed}</p>')

    _close_list(html_parts, in_list)
    return "\n".join(html_parts)


def _close_list(parts: list, in_list: bool):
    if in_list:
        parts.append("</ul>")


def _convert_img(line: str, image_map: dict) -> str:
    """转换图片标记，替换本地路径为微信 URL。"""
    match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
    if not match:
        return line
    alt, src = match.groups()
    # 替换本地路径
    if src in image_map:
        src = image_map[src]
    return f'<img src="{src}" alt="{_escape_html(alt)}" style="max-width:100%;height:auto;">'


def _process_inline(text: str) -> str:
    """处理行内格式（粗体、链接）。"""
    # 粗体 **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 链接 [text](url)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    return text


def _escape_html(text: str) -> str:
    """HTML 转义。"""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def _wechat_format(html: str) -> str:
    """微信特殊格式化处理。"""
    # 微信不支持 section 标签，替换为 div
    html = html.replace("<section>", "<div>").replace("</section>", "</div>")
    # 图片居中
    html = html.replace('<img ', '<img style="max-width:100%;height:auto;display:block;margin:10px auto;" ')
    return html
