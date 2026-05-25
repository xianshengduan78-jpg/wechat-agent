#!/usr/bin/env python3
"""微信公众号写作 Agent — CLI 入口。"""

import argparse
import sys

from config.settings import DEEPSEEK_API_KEY
from llm.client import DeepSeekClient


def cmd_test():
    """调 DeepSeek 写一句话，验证连通性。"""
    if not DEEPSEEK_API_KEY:
        print("❌ 错误：DEEPSEEK_API_KEY 未设置，请在 .env 中配置。")
        sys.exit(1)

    client = DeepSeekClient()
    messages = [
        {"role": "system", "content": "你是一个 AI 助手。用一句话介绍你自己。"},
        {"role": "user", "content": "说一句简短的话，展示你的能力。"},
    ]
    print("🔄 正在调用 DeepSeek API...")
    result = client.chat(messages)
    print(f"✅ DeepSeek 响应：\n{result}")


def cmd_daily(dry_run=False):
    """运行日报 pipeline（Phase 2 + Phase 3）。"""
    import json
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from pathlib import Path

    from sources.pool_manager import refresh_pool
    from selection.selector import select, write_selection_report

    print("📋 Phase 2: 刷新候选池...")
    pool = refresh_pool()
    result = select(pool)
    report_path = write_selection_report(result)

    selected = result["selected_events"]
    print(f"\n📋 入选 {len(selected)} 条事件")

    if not selected:
        print("❌ 没有入选事件，无法继续。")
        return

    if dry_run:
        # Phase 3: 模拟写日报（不调 DeepSeek）
        print("\n📝 Phase 3: 模拟写日报 (--dry-run，不调 DeepSeek)")
        print(f"   事件数: {len(selected)}")
        print(f"   标题示例: AI早报｜{selected[0].get('title', '')[:20]}⋯")
        print(f"\n   入选事件列表:")
        for i, e in enumerate(selected, 1):
            print(f"     {i}. [{e.get('total_score', 0):5.1f}] {e.get('title', '')}")
        print(f"\n   选题报告: {report_path}")
        return

    print("\n📝 Phase 3: 调 DeepSeek 写日报...")
    from writing.daily_writer import write_daily
    from validation.sync_validator import validate_before_sync

    article = write_daily(selected)

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存文章
    article_path = output_dir / "article.md"
    with open(article_path, "w", encoding="utf-8") as f:
        f.write(article.get("body_markdown", ""))
    print(f"   文章已保存: {article_path}")

    # 验证
    print("\n🔍 验证文章...")
    validation = validate_before_sync(article, selected)
    if validation["passed"]:
        print("   ✅ 全部验证通过")
    else:
        print("   ❌ 验证失败:")
        for cat, errs in validation["errors"].items():
            for e in errs:
                print(f"      [{cat}] {e}")

    print(f"\n📋 日报生成完成:")
    print(f"   标题: {article.get('article_title', '')}")
    print(f"   摘要: {article.get('digest', '')[:60]}...")

    # 保存完整结果 JSON
    result_path = output_dir / "daily-result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(article, f, ensure_ascii=False, indent=2)
    print(f"   完整结果: {result_path}")


def cmd_article(topic=None, dry_run=False):
    """运行深度文章 pipeline。"""
    if not topic:
        print("📝 请输入选题，例如: --article 'DeepSeek 开源新模型'")
        return

    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    print(f"📝 深度文章: {topic}")

    from writing.diagnosis import diagnose_topic
    diagnosis = diagnose_topic(topic)
    print(f"\n   选题诊断:")
    print(f"     类型: {diagnosis['event_type']}")
    print(f"     读者: {', '.join(diagnosis['target_audience'])}")
    print(f"     结构: {diagnosis['recommended_structure']}")

    if dry_run:
        print(f"\n   (--dry-run，不调 DeepSeek)")
        return

    from writing.article_writer import write_outline

    print("\n📝 生成大纲...")
    outline = write_outline(topic)
    print(f"   主线: {outline.get('main_line', '')}")
    print(f"   小标题: {', '.join(outline.get('headings', []))}")

    print("\n⏸️  请确认大纲后继续 (y/n)")
    # 实际使用中这里 await 用户确认

    from writing.article_writer import write_full_article
    print("\n📝 写全文...")
    article = write_full_article(topic, outline)

    from validation.article_validator import validate_article
    errors = validate_article(article)
    if errors:
        print("   ❌ 验证失败:")
        for e in errors:
            print(f"      {e}")
    else:
        print("   ✅ 验证通过")

    print(f"\n📝 文章完成:")
    print(f"   标题: {article.get('article_title', '')}")
    print(f"   字数: {len(article.get('body_markdown', ''))}")


def cmd_loop():
    """运行数据闭环（后续 Phase 实现）。"""
    print("🔄 数据闭环功能待实现（Phase 5）。")


def main():
    parser = argparse.ArgumentParser(description="微信公众号写作 Agent")
    parser.add_argument("--test", action="store_true", help="测试 DeepSeek API 连通性")
    parser.add_argument("--daily", action="store_true", help="运行 AI 日报 pipeline")
    parser.add_argument("--article", nargs="?", const=True, default=False, metavar="TOPIC",
                        help="运行深度文章 pipeline，可选指定选题")
    parser.add_argument("--loop", action="store_true", help="运行数据闭环")
    parser.add_argument("--dry-run", action="store_true", help="预览模式（不调 API）")

    args = parser.parse_args()

    if args.test:
        cmd_test()
    elif args.daily:
        cmd_daily(dry_run=args.dry_run)
    elif args.article:
        topic = args.article if isinstance(args.article, str) else None
        cmd_article(topic=topic, dry_run=args.dry_run)
    elif args.loop:
        cmd_loop()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
