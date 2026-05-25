"""深度文章完整 pipeline。

8 步流程：选题诊断 → 参考资料 → 大纲 → 确认 → 全文 → 验证 → 封面/HTML → 确认 → 发布。
"""

import json
import logging
from pathlib import Path

from config.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)


def run_article(topic: str, dry_run=False):
    """运行深度文章 pipeline。"""
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: 选题诊断
    from writing.diagnosis import diagnose_topic
    logger.info("Step 1/8: 选题诊断")
    diagnosis = diagnose_topic(topic)
    logger.info("类型: %s, 读者: %s", diagnosis["event_type"], diagnosis["target_audience"])

    if dry_run:
        logger.info("Dry-run 模式，停在 Step 1")
        return {"diagnosis": diagnosis}

    # Step 2: 搜索参考资料
    from sources.search_fetcher import fetch as search_refs
    logger.info("Step 2/8: 搜索参考资料")
    references = search_refs()
    logger.info("获取到 %d 条参考资料", len(references))

    ref_path = output_dir / "references.json"
    with open(ref_path, "w", encoding="utf-8") as f:
        json.dump(references, f, ensure_ascii=False, indent=2)

    # Step 3: 调 DeepSeek 出大纲
    from writing.article_writer import write_outline
    logger.info("Step 3/8: 生成大纲")
    outline = write_outline(topic, references)

    outline_path = output_dir / "structure-plan.md"
    with open(outline_path, "w", encoding="utf-8") as f:
        f.write(f"# 大纲: {topic}\n\n")
        f.write(f"主线: {outline.get('main_line', '')}\n\n")
        f.write("## 小标题\n")
        for h in outline.get("headings", []):
            f.write(f"- {h}\n")
        f.write(f"\n## 不要写\n{outline.get('not_write', '')}\n")
        f.write(f"\n## 写法\n{outline.get('writing_mode', '')}\n")
    logger.info("大纲已保存: %s", outline_path)

    # Step 4: 人工确认
    logger.info("Step 4/8: 等待用户确认大纲")
    _print_outline(topic, outline)
    confirmed = _human_checkpoint()
    if not confirmed:
        logger.info("用户取消，终止 pipeline")
        return {"outline": outline}

    # Step 5: 调 DeepSeek 写全文
    from writing.article_writer import write_full_article
    logger.info("Step 5/8: 写全文")
    article = write_full_article(topic, outline, references)

    article_path = output_dir / "article.md"
    with open(article_path, "w", encoding="utf-8") as f:
        f.write(article.get("body_markdown", ""))
    logger.info("文章已保存: %s", article_path)

    # Step 6: 验证
    from validation.article_validator import validate_article
    logger.info("Step 6/8: 验证文章")
    errors = validate_article(article)
    if errors:
        logger.warning("验证发现 %d 个问题", len(errors))
        for e in errors:
            logger.warning("  %s", e)
    else:
        logger.info("验证通过")

    # Step 7: 截图 + 封面 + HTML
    from publishing.cover_generator import generate_article_cover
    from publishing.html_builder import build_html
    logger.info("Step 7/8: 生成封面和 HTML")

    cover_title = article.get("cover_title", topic[:8])
    cover_subtitle = article.get("cover_subtitle", "")
    cover_paths = generate_article_cover(topic, cover_title, cover_subtitle)

    html_content = build_html(
        article.get("body_markdown", ""),
        article.get("article_title", ""),
    )
    html_path = output_dir / "article-wechat.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 标题方案
    from writing.title_generator import generate_titles
    logger.info("生成标题方案")
    try:
        titles = generate_titles(article.get("body_markdown", ""), article.get("article_title", ""))
        title_path = output_dir / "title-plan.md"
        with open(title_path, "w", encoding="utf-8") as f:
            f.write("# 标题方案\n\n")
            for i, t in enumerate(titles.get("title_candidates", []), 1):
                f.write(f"{i}. {t}\n")
        logger.info("标题方案已保存: %s", title_path)
    except Exception as e:
        logger.warning("标题生成失败: %s", e)

    # Step 8: 人工确认 + 发布
    logger.info("Step 8/8: 人工确认")
    _print_preview(article, cover_paths, html_path)
    confirmed = _human_checkpoint()
    if not confirmed:
        logger.info("用户取消发布")
        return {"article": article, "cover": cover_paths, "html": str(html_path)}

    # 上传 + 创建草稿
    from publishing.wechat_api import WeChatClient
    wechat = WeChatClient()

    thumb_id = wechat.upload_thumb_material(cover_paths.get("wide", ""))
    if not thumb_id:
        logger.error("封面上传失败")
        return None

    draft_articles = [{
        "title": article.get("wechat_api_title", article.get("article_title", "")),
        "author": "LumenAI",
        "digest": article.get("digest", ""),
        "content": html_content,
        "thumb_media_id": thumb_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }]
    media_id = wechat.create_draft(draft_articles)
    if media_id:
        logger.info("草稿创建成功: %s", media_id)
    else:
        logger.error("草稿创建失败")

    return {
        "article": article,
        "outline": outline,
        "cover": cover_paths,
        "html": str(html_path),
        "media_id": media_id,
    }


def _print_outline(topic: str, outline: dict):
    """打印大纲预览。"""
    print("\n" + "=" * 50)
    print(f"📝 大纲: {topic}")
    print("=" * 50)
    print(f"主线: {outline.get('main_line', '')}")
    print(f"\n小标题:")
    for h in outline.get("headings", []):
        print(f"  - {h}")
    print(f"\n写法: {outline.get('writing_mode', '')}")
    print(f"不要写: {outline.get('not_write', '')}")
    print("=" * 50)


def _print_preview(article: dict, cover_paths: dict, html_path: Path):
    """打印发布预览。"""
    print("\n" + "=" * 50)
    print("📋 发布预览")
    print("=" * 50)
    print(f"标题: {article.get('article_title', '')}")
    print(f"字数: {len(article.get('body_markdown', ''))}")
    print(f"封面: {cover_paths.get('wide', '')}, {cover_paths.get('square', '')}")
    print(f"HTML: {html_path}")
    print("=" * 50)


def _human_checkpoint() -> bool:
    """等待用户确认。"""
    try:
        response = input("\n确认发布到微信公众号草稿箱？(y/n): ")
        return response.lower().strip() == "y"
    except (EOFError, KeyboardInterrupt):
        return False
