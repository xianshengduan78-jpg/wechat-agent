#!/usr/bin/env python3
"""微信公众号写作 Agent — Web UI"""

import json
import subprocess
import sys
import threading
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent

st.set_page_config(
    page_title="微信公众号写作 Agent",
    page_icon="📝",
    layout="wide",
)


# ── 工具函数 ─────────────────────────────────────────

def run_cmd(cmd: list, timeout: int = 180) -> tuple:
    """运行命令，返回 (stdout, stderr, exit_code)。"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", "超时", -1
    except Exception as e:
        return "", str(e), -1


def tail_file(path: Path, n: int = 50) -> str:
    """读取文件尾部内容。"""
    if not path.exists():
        return ""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[-n:])


# ── Sidebar ──────────────────────────────────────────

st.sidebar.title("📝 写作 Agent")
st.sidebar.markdown("---")
page = st.sidebar.radio("导航", ["仪表盘", "AI 日报", "深度文章", "配置"])

# 状态信息
st.sidebar.markdown("---")
st.sidebar.caption(f"项目目录: `{ROOT.name}`")

# ── 仪表盘 ───────────────────────────────────────────

if page == "仪表盘":
    st.title("📊 仪表盘")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🧪 测试 DeepSeek", use_container_width=True):
            with st.spinner("正在调用 DeepSeek..."):
                out, err, code = run_cmd([sys.executable, "main.py", "--test"], timeout=60)
            if code == 0:
                st.success("DeepSeek 连通正常")
                st.code(out)
            else:
                st.error(f"失败: {err or out}")

    with col2:
        if st.button("📋 日报预览", use_container_width=True):
            with st.spinner("正在抓取和筛选..."):
                out, err, code = run_cmd([sys.executable, "main.py", "--daily", "--dry-run"], timeout=120)
            if code == 0:
                st.success("预览完成")
                with st.expander("查看日志", expanded=True):
                    st.code(out)
            else:
                st.error(f"失败: {err or out}")

    with col3:
        if st.button("🔄 完整日报", use_container_width=True):
            with st.spinner("抓取 → 筛选 → DeepSeek 写作 → 封面 → HTML..."):
                out, err, code = run_cmd([sys.executable, "main.py", "--daily"], timeout=300)
            if code == 0:
                st.success("日报生成完成")
                with st.expander("查看日志", expanded=True):
                    st.code(out)
            else:
                st.error(f"失败: {err or out}")

    # 最近输出
    st.subheader("最近输出")
    report_path = ROOT / "output" / "topic-selection-report.md"
    report = tail_file(report_path)
    if report:
        st.markdown(report)
    else:
        st.info("还没有输出，先跑一次日报预览")

# ── AI 日报 ──────────────────────────────────────────

elif page == "AI 日报":
    st.title("📋 AI 日报")

    tab1, tab2, tab3 = st.tabs(["运行", "文章", "选题报告"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ 运行日报（完整流程）", use_container_width=True):
                status = st.status("正在运行...")
                with status:
                    st.write("Step 1: 刷新候选池...")
                    out, err, code = run_cmd([sys.executable, "main.py", "--daily"], timeout=300)
                    st.code(out)
                    if code == 0:
                        status.update(label="✅ 完成", state="complete")
                    else:
                        status.update(label=f"❌ 失败: {err}", state="error")

        with col2:
            if st.button("👁 预览（不调 DeepSeek）", use_container_width=True):
                with st.spinner("正在抓取和筛选..."):
                    out, err, code = run_cmd([sys.executable, "main.py", "--daily", "--dry-run"], timeout=120)
                st.code(out)

    with tab2:
        article_path = ROOT / "output" / "article.md"
        if article_path.exists():
            with open(article_path, "r", encoding="utf-8") as f:
                st.markdown(f.read())
        else:
            st.info("还没有生成过日报，先运行一次")

    with tab3:
        report_path = ROOT / "output" / "topic-selection-report.md"
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                st.markdown(f.read())
        else:
            st.info("还没有选题报告")

# ── 深度文章 ─────────────────────────────────────────

elif page == "深度文章":
    st.title("📝 深度文章")

    topic = st.text_input("输入选题", placeholder="例如：DeepSeek 开源新模型、Claude Code 深度体验")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ 生成文章", use_container_width=True, disabled=not topic):
            with st.spinner("诊断 → 大纲 → 写作 → 封面 → HTML..."):
                out, err, code = run_cmd(
                    [sys.executable, "main.py", "--article", topic], timeout=300
                )
            if code == 0:
                st.success("文章生成完成")
                st.code(out)
            else:
                st.error(f"失败: {err or out}")

    with col2:
        if st.button("👁 预览诊断", use_container_width=True, disabled=not topic):
            with st.spinner("正在诊断选题..."):
                out, err, code = run_cmd(
                    [sys.executable, "main.py", "--article", topic, "--dry-run"], timeout=60
                )
            st.code(out)

    st.subheader("最近生成的文章")
    article_path = ROOT / "output" / "article.md"
    if article_path.exists():
        with open(article_path, "r", encoding="utf-8") as f:
            st.markdown(f.read())

# ── 配置 ─────────────────────────────────────────────

elif page == "配置":
    st.title("⚙️ 配置")

    env_path = ROOT / ".env"
    env_content = ""
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            env_content = f.read()

    new_env = st.text_area(
        ".env 配置",
        env_content,
        height=250,
        help="修改后保存即可生效",
    )

    if st.button("💾 保存配置"):
        # 隐藏 key 显示
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(new_env)
        st.success("已保存")

    st.subheader("检查清单")
    downloaded = Path(ROOT / "output" / "article.md").stat().st_size if (ROOT / "output" / "article.md").exists() else 0
    st.json({
        "DeepSeek API": "已配置" if "DEEPSEEK_API_KEY=sk-" in env_content and "xxx" not in env_content else "未配置",
        "微信 AppID": "已配置" if "WECHAT_APPID=" in env_content and "xxx" not in env_content else "未配置",
        "已生成文章": f"{downloaded} bytes" if downloaded else "无",
    })
