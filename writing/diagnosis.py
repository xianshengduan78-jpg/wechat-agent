"""选题诊断模块。

根据关键词判断选题类型、目标读者、推荐结构。
"""

# 八种文章结构
STRUCTURES = {
    "A": "线性观察：按时间线或逻辑顺序展开",
    "B": "问题拆解：定义问题 → 分析根因 → 给解法",
    "C": "对比实测：两个方案并行对比 → 结论",
    "D": "使用场景：不同人群/场景下的应用 → 启示",
    "E": "观点短评：一个核心判断 → 多角度论证",
    "F": "避坑提醒：常见误区 → 正确做法",
    "G": "决策指南：选择项罗列 → 适用条件 → 建议",
    "H": "深度解析：技术/商业原理 → 影响 → 判断",
}

# 事件类型 → 推荐结构映射
TYPE_STRUCTURE_MAP = {
    "release": ("H", ["趋势判断", "用户影响"]),
    "product": ("D", ["使用场景", "上手体验"]),
    "open_source": ("F", ["开发者关注", "对比选择"]),
    "price": ("C", ["性价比分析", "市场影响"]),
    "agent": ("B", ["能力拆解", "实用场景"]),
    "policy": ("E", ["观点短评", "行业影响"]),
    "research": ("H", ["技术原理", "影响判断"]),
}


def diagnose_topic(topic: str, events: list = None) -> dict:
    """诊断选题，返回结构计划。"""
    topic_lower = topic.lower()

    # 判断事件类型
    event_type = _detect_event_type(topic_lower, events)

    # 推荐结构
    struct_key, struct_suggestions = TYPE_STRUCTURE_MAP.get(event_type, ("H", ["深度解析"]))

    # 目标读者
    target_audience = _detect_audience(topic_lower)

    return {
        "topic": topic,
        "event_type": event_type,
        "target_audience": target_audience,
        "recommended_structure": STRUCTURES.get(struct_key, STRUCTURES["H"]),
        "suggestions": struct_suggestions,
        "main_line": "",
        "headings": [],
        "not_write": "",
        "writing_mode": "观察笔记",
    }


def _detect_event_type(topic_lower: str, events: list = None) -> str:
    """从选题关键词判断事件类型。"""
    if any(kw in topic_lower for kw in ["发布", "推出", "上线", "release", "launch"]):
        return "release"
    if any(kw in topic_lower for kw in ["开源", "open source", "代码"]):
        return "open_source"
    if any(kw in topic_lower for kw in ["降价", "免费", "价格", "收费"]):
        return "price"
    if any(kw in topic_lower for kw in ["agent", "智能体", "工具"]):
        return "agent"
    if any(kw in topic_lower for kw in ["政策", "监管", "法规"]):
        return "policy"
    if any(kw in topic_lower for kw in ["研究", "论文", "发现"]):
        return "research"
    return "product"


def _detect_audience(topic_lower: str) -> list:
    """判断目标读者群体。"""
    audiences = []
    if any(kw in topic_lower for kw in ["开发者", "开发", "代码", "API", "SDK"]):
        audiences.append("开发者")
    if any(kw in topic_lower for kw in ["产品", "产品经理"]):
        audiences.append("产品经理")
    if any(kw in topic_lower for kw in ["企业", "商业", "公司"]):
        audiences.append("企业决策者")
    if any(kw in topic_lower for kw in ["用户", "使用", "体验"]):
        audiences.append("普通用户")
    if not audiences:
        audiences.append("AI 从业者")
    return audiences
