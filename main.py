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
    """运行日报 pipeline（后续 Phase 实现）。"""
    print("📋 日报功能待实现（Phase 3）。")
    print(f"   dry_run={dry_run}")


def cmd_article(topic=None, dry_run=False):
    """运行深度文章 pipeline（后续 Phase 实现）。"""
    print("📝 深度文章功能待实现（Phase 3）。")
    print(f"   topic={topic}, dry_run={dry_run}")


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
