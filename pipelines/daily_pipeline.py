"""日报完整 pipeline。

10 步流程：记忆 → 抓取 → 筛选 → 写报告 → 写文章 → 验证 → 截图 → 封面/HTML → 确认 → 发布。
"""

import json
import logging
from pathlib import Path

from config.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)


def run_daily(dry_run=False):
    """运行日报完整 pipeline。"""
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: 加载策略记忆
    logger.info("Step 1/11: 加载策略记忆")
    strategy_memory = _load_strategy_memory()

    # Step 2: 刷新候选池
    from sources.pool_manager import refresh_pool
    logger.info("Step 2/11: 刷新候选池")
    pool = refresh_pool()

    # Step 3: 筛选事件
    from selection.selector import select, write_selection_report
    logger.info("Step 3/11: 筛选事件")
    result = select(pool)
    write_selection_report(result)

    selected_events = result["selected_events"]
    if not selected_events:
        logger.error("没有入选事件，终止 pipeline")
        return None

    # Step 4: 写选题报告（已在 step 3 中完成）

    if dry_run:
        logger.info("Dry-run 模式，停在第 4 步")
        return {"result": result, "phase": "selection"}

    # Step 5: 调 DeepSeek 写日报
    from writing.daily_writer import write_daily
    logger.info("Step 5/11: 调 DeepSeek 写日报")
    article = write_daily(selected_events, strategy_memory)

    # 保存文章
    article_path = output_dir / "article.md"
    with open(article_path, "w", encoding="utf-8") as f:
        f.write(article.get("body_markdown", ""))
    logger.info("文章已保存: %s", article_path)

    # Step 6: 验证文章
    from validation.sync_validator import validate_before_sync
    logger.info("Step 6/11: 验证文章")
    validation = validate_before_sync(article, selected_events)
    if not validation["passed"]:
        logger.warning("验证未通过，但继续处理")
    else:
        logger.info("验证通过")

    # Step 7: 截图
    from publishing.image_manager import assign_screenshots, check_alignment
    from publishing.screenshot import retry_screenshot
    logger.info("Step 7/11: 分配截图")
    screenshot_assignments = assign_screenshots(selected_events)
    for idx, info in screenshot_assignments.items():
        success = retry_screenshot(info["company"], info["path"])
        if not success:
            logger.warning("截图失败 [%s]", info["company"])
    alignment_issues = check_alignment(selected_events, screenshot_assignments)

    # Step 8: 生成封面 + HTML
    from publishing.cover_generator import generate_daily_cover
    from publishing.html_builder import build_html
    logger.info("Step 8/11: 生成封面和 HTML")
    cover_paths = generate_daily_cover(
        article.get("article_title", ""),
        article.get("digest", ""),
        selected_events,
    )

    html_content = build_html(article.get("body_markdown", ""), article.get("article_title", ""))
    html_path = output_dir / "article-wechat.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("HTML 已保存: %s", html_path)

    # Step 9: Human checkpoint
    logger.info("Step 9/11: 人工确认（等待用户确认）")
    _print_preview(article, cover_paths, html_path)
    confirmed = _human_checkpoint()
    if not confirmed:
        logger.info("用户取消发布")
        return {"article": article, "cover": cover_paths, "html": str(html_path)}

    # Step 10: 上传素材 + 创建草稿
    from publishing.wechat_api import WeChatClient
    logger.info("Step 10/11: 上传素材并创建草稿")
    wechat = WeChatClient()

    # 上传封面
    thumb_id = wechat.upload_thumb_material(cover_paths.get("wide", ""))
    if not thumb_id:
        logger.error("封面上传失败，终止发布")
        return None

    # 上传正文图片
    image_map = {}
    for idx, info in screenshot_assignments.items():
        wechat_url = wechat.upload_article_image(info["path"])
        if wechat_url:
            image_map[info["path"]] = wechat_url

    # 重新生成 HTML（替换图片路径）
    html_content = build_html(
        article.get("body_markdown", ""),
        article.get("article_title", ""),
        image_map,
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 创建草稿
    draft_articles = [{
        "title": article.get("wechat_api_title", article.get("article_title", "")),
        "author": "AI 早报",
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

    # Step 11: 记录历史
    from selection.dedup import append_history
    logger.info("Step 11/11: 记录历史")
    append_history(selected_events)
    logger.info("历史已更新")

    return {
        "article": article,
        "cover": cover_paths,
        "html": str(html_path),
        "media_id": media_id,
    }


def _load_strategy_memory() -> dict:
    """加载策略记忆。"""
    path = Path(__file__).parent.parent / "data" / "strategy-memory.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _print_preview(article: dict, cover_paths: dict, html_path: Path):
    """打印发布预览。"""
    print("\n" + "=" * 50)
    print("📋 发布预览")
    print("=" * 50)
    print(f"标题: {article.get('article_title', '')}")
    print(f"摘要: {article.get('digest', '')}")
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
