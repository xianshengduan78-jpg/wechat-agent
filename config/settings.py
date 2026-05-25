import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── 路径 ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
ASSETS_DIR = PROJECT_ROOT / "assets"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

for d in [DATA_DIR, OUTPUT_DIR, ASSETS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── API Keys ──────────────────────────────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
WECHAT_APPID = os.getenv("WECHAT_APPID", "")
WECHAT_APPSECRET = os.getenv("WECHAT_APPSECRET", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
WECHAT_COVER_LABEL = os.getenv("WECHAT_COVER_LABEL", "")

# ── DeepSeek ──────────────────────────────────────────
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_TIMEOUT = 120
DEEPSEEK_MAX_RETRIES = 3

# ── 筛选阈值 ──────────────────────────────────────────
MIN_EVENTS = 8
MAX_EVENTS = 16
PRIMARY_WINDOW_HOURS = 24
SECONDARY_WINDOW_HOURS = 72
MIN_USER_RELEVANCE = 12
MIN_COMMUNITY_SIGNAL = 8
DIVERSITY_MIN_SOURCES = 3
SINGLE_SOURCE_MAX = 4
DEDUP_SIMILARITY_THRESHOLD = 0.72

# ── 大厂域名列表 ──────────────────────────────────────
BIG_TECH_DOMAINS = [
    "openai.com", "anthropic.com", "google.com", "deepmind.google",
    "blog.google", "developers.googleblog.com", "meta.com", "ai.meta.com",
    "apple.com", "nvidia.com", "x.ai", "microsoft.com", "github.com",
    "amazon.com", "aws.amazon.com", "huggingface.co", "together.ai",
    "producthunt.com", "simonwillison.net", "karpathy.bearblog.dev",
    "huyenchip.com", "oneusefulthing.org", "jack-clark.net", "arxiv.org",
]

# ── RSS 源列表 ────────────────────────────────────────
FEEDS = [
    ("OpenAI", "OpenAI News", "https://openai.com/news/rss.xml"),
    ("Google", "Google Blog", "https://blog.google/rss/"),
    ("Google DeepMind", "DeepMind Blog", "https://deepmind.google/blog/rss.xml"),
    ("GitHub", "GitHub Changelog", "https://github.blog/changelog/feed/"),
    ("AWS", "AWS ML Blog", "https://aws.amazon.com/blogs/machine-learning/feed/"),
    ("NVIDIA", "NVIDIA GenAI Blog", "https://developer.nvidia.com/blog/category/generative-ai/feed/"),
    ("Hugging Face", "HF Blog", "https://huggingface.co/blog/feed.xml"),
    ("Together AI", "Together Blog", "https://together.ai/blog/rss.xml"),
    ("Product Hunt", "PH AI", "https://www.producthunt.com/feed?category=ai"),
    ("Simon Willison", "Simon Blog", "https://simonwillison.net/atom/everything/"),
    ("Andrej Karpathy", "Karpathy Blog", "https://karpathy.bearblog.dev/feed/"),
    ("Chip Huyen", "Chip Blog", "https://huyenchip.com/feed.xml"),
    ("Ethan Mollick", "One Useful Thing", "https://www.oneusefulthing.org/feed"),
    ("Import AI", "Jack Clark", "https://jack-clark.net/feed/"),
]

# ── 截图 URL 规则 ────────────────────────────────────
SCREENSHOT_URL_MAP = {
    "Google": "google.com",
    "Anthropic": "anthropic.com",
    "AWS": "aws.amazon.com",
    "NVIDIA": "nvidia.com",
    "GitHub": "github.com",
    "Cloudflare": "cloudflare.com",
    "DeepSeek": "deepseek.com",
    "Meta": "meta.com",
    "Microsoft": "microsoft.com",
    "OpenAI": "openai.com",
}

# ── 微信 API 端点 ────────────────────────────────────
TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
MATERIAL_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"
UPLOAD_IMG_URL = "https://api.weixin.qq.com/cgi-bin/media/uploadimg"
DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"
DRAFT_GET_URL = "https://api.weixin.qq.com/cgi-bin/draft/get"
DRAFT_UPDATE_URL = "https://api.weixin.qq.com/cgi-bin/draft/update"
DATACUBE_URL = "https://api.weixin.qq.com/datacube/getarticletotal"
