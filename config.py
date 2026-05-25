"""软著工厂运行配置。

本模块负责加载本地 .env 文件，并把脚本中的可变配置集中为环境变量。
"""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


def resolve_path(value: str | Path, base_dir: Path = PROJECT_ROOT) -> Path:
    """
    将配置中的路径解析为绝对路径。

    Args:
        value: 环境变量中的路径值，可以是绝对路径、相对路径或用户目录路径。
        base_dir: 相对路径的基准目录。

    Returns:
        解析后的绝对路径。

    Raises:
        RuntimeError: 当前工作目录不可访问时可能由 Path.resolve 抛出。
    """
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (base_dir / path).resolve()


def _strip_optional_quotes(value: str) -> str:
    """
    去除环境变量值外层的可选引号。

    Args:
        value: 原始环境变量值。

    Returns:
        去除外层引号后的值。
    """
    stripped_value = value.strip()
    if len(stripped_value) >= 2 and stripped_value[0] == stripped_value[-1]:
        if stripped_value[0] in {"'", '"'}:
            return stripped_value[1:-1]
    return stripped_value


def load_env_file(env_path: str | Path = DEFAULT_ENV_FILE) -> int:
    """
    加载 .env 文件到当前进程环境变量。

    Args:
        env_path: .env 文件路径。

    Returns:
        实际写入环境变量的数量。

    Raises:
        OSError: 文件存在但无法读取时抛出。
    """
    resolved_env_path = resolve_path(env_path)
    if not resolved_env_path.exists():
        return 0

    loaded_count = 0
    with resolved_env_path.open("r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, raw_value = line.split("=", 1)
            key = key.strip()
            if not key or key in os.environ:
                continue

            os.environ[key] = _strip_optional_quotes(raw_value)
            loaded_count += 1

    return loaded_count


def get_env_str(name: str, default: str) -> str:
    """
    读取字符串类型环境变量。

    Args:
        name: 环境变量名称。
        default: 环境变量不存在时使用的默认值。

    Returns:
        字符串配置值。
    """
    return os.environ.get(name, default)


def get_env_int(name: str, default: int) -> int:
    """
    读取整数类型环境变量。

    Args:
        name: 环境变量名称。
        default: 环境变量不存在时使用的默认值。

    Returns:
        整数配置值。

    Raises:
        ValueError: 环境变量存在但不是合法整数时抛出。
    """
    raw_value = os.environ.get(name)
    if raw_value is None or raw_value == "":
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"环境变量 {name} 必须是整数，当前值为: {raw_value}") from exc


def get_env_float(name: str, default: float) -> float:
    """
    读取浮点数类型环境变量。

    Args:
        name: 环境变量名称。
        default: 环境变量不存在时使用的默认值。

    Returns:
        浮点数配置值。

    Raises:
        ValueError: 环境变量存在但不是合法浮点数时抛出。
    """
    raw_value = os.environ.get(name)
    if raw_value is None or raw_value == "":
        return default
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(f"环境变量 {name} 必须是浮点数，当前值为: {raw_value}") from exc


def get_env_bool(name: str, default: bool) -> bool:
    """
    读取布尔类型环境变量。

    Args:
        name: 环境变量名称。
        default: 环境变量不存在时使用的默认值。

    Returns:
        布尔配置值。

    Raises:
        ValueError: 环境变量存在但不是合法布尔值时抛出。
    """
    raw_value = os.environ.get(name)
    if raw_value is None or raw_value == "":
        return default

    normalized_value = raw_value.strip().lower()
    if normalized_value in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized_value in {"0", "false", "no", "n", "off"}:
        return False

    raise ValueError(f"环境变量 {name} 必须是布尔值，当前值为: {raw_value}")


def get_env_path(name: str, default: str | Path) -> Path:
    """
    读取路径类型环境变量。

    Args:
        name: 环境变量名称。
        default: 环境变量不存在时使用的默认路径。

    Returns:
        解析后的绝对路径。
    """
    return resolve_path(os.environ.get(name, str(default)))


def get_env_list(name: str, default: list[str], separator: str = ",") -> list[str]:
    """
    读取列表类型环境变量。

    Args:
        name: 环境变量名称。
        default: 环境变量不存在时使用的默认列表。
        separator: 列表分隔符。

    Returns:
        字符串列表配置值。
    """
    raw_value = os.environ.get(name)
    if raw_value is None or raw_value == "":
        return default
    return [item.strip() for item in raw_value.split(separator) if item.strip()]


ENV_FILE_PATH = resolve_path(os.environ.get("SOFTCOPYRIGHT_ENV_FILE", str(DEFAULT_ENV_FILE)))
load_env_file(ENV_FILE_PATH)


# AI 调用配置
AI_API_URL = get_env_str(
    "SOFTCOPYRIGHT_AI_API_URL",
    "https://inference-api.nousresearch.com/v1/chat/completions",
)
AI_API_KEY = get_env_str("SOFTCOPYRIGHT_AI_API_KEY", "")
AI_AUTH_PATH = get_env_path("SOFTCOPYRIGHT_AUTH_PATH", "~/.hermes/auth.json")
AI_AUTH_PROVIDER = get_env_str("SOFTCOPYRIGHT_AUTH_PROVIDER", "nous")
AI_MODEL = get_env_str("SOFTCOPYRIGHT_AI_MODEL", "xiaomi/mimo-v2-pro")
AI_MAX_TOKENS = get_env_int("SOFTCOPYRIGHT_AI_MAX_TOKENS", 8192)
AI_TEMPERATURE = get_env_float("SOFTCOPYRIGHT_AI_TEMPERATURE", 0.7)
AI_TIMEOUT_SECONDS = get_env_int("SOFTCOPYRIGHT_AI_TIMEOUT_SECONDS", 300)
AI_JSON_ERROR_PREVIEW_CHARS = get_env_int("SOFTCOPYRIGHT_AI_JSON_ERROR_PREVIEW_CHARS", 500)

# 项目目录与流水线配置
PROJECTS_DIR = get_env_path("SOFTCOPYRIGHT_PROJECTS_DIR", "projects")
PROMPTS_DIR = get_env_path("SOFTCOPYRIGHT_PROMPTS_DIR", "prompts")
TEMPLATES_DIR = get_env_path("SOFTCOPYRIGHT_TEMPLATES_DIR", "templates")
DEFAULT_TEMPLATE_PATH = get_env_path("SOFTCOPYRIGHT_DEFAULT_TEMPLATE_PATH", "template.html")
DEFAULT_DATA_PATH = get_env_path("SOFTCOPYRIGHT_DEFAULT_DATA_PATH", "data.json")
PROJECT_SAFE_NAME_MAX_LENGTH = get_env_int("SOFTCOPYRIGHT_PROJECT_SAFE_NAME_MAX_LENGTH", 50)
P2_MIN_FILE_COUNT = get_env_int("SOFTCOPYRIGHT_P2_MIN_FILE_COUNT", 15)
P2_MAX_FILE_COUNT = get_env_int("SOFTCOPYRIGHT_P2_MAX_FILE_COUNT", 25)
P2_MIN_TOTAL_LINES = get_env_int("SOFTCOPYRIGHT_P2_MIN_TOTAL_LINES", 2500)
P3_CHECKPOINT_COUNT = get_env_int("SOFTCOPYRIGHT_P3_CHECKPOINT_COUNT", 3)
P3_MAX_RETRIES = get_env_int("SOFTCOPYRIGHT_P3_MAX_RETRIES", 3)
P3_RELATED_SUMMARY_CHARS = get_env_int("SOFTCOPYRIGHT_P3_RELATED_SUMMARY_CHARS", 500)
RENDER_TIMEOUT_SECONDS = get_env_int("SOFTCOPYRIGHT_RENDER_TIMEOUT_SECONDS", 120)
PACK_TIMEOUT_SECONDS = get_env_int("SOFTCOPYRIGHT_PACK_TIMEOUT_SECONDS", 120)

# 截图渲染配置
RENDER_OUTPUT_DIR = get_env_path("SOFTCOPYRIGHT_RENDER_OUTPUT_DIR", "render_outputs")
TAILWIND_CDN_URL = get_env_str("SOFTCOPYRIGHT_TAILWIND_CDN_URL", "https://cdn.tailwindcss.com")
THEME_COLOR = get_env_str("SOFTCOPYRIGHT_THEME_COLOR", "#1E40AF")
VIEWPORT_WIDTH = get_env_int("SOFTCOPYRIGHT_VIEWPORT_WIDTH", 1280)
VIEWPORT_HEIGHT = get_env_int("SOFTCOPYRIGHT_VIEWPORT_HEIGHT", 800)
PLAYWRIGHT_HEADLESS = get_env_bool("SOFTCOPYRIGHT_PLAYWRIGHT_HEADLESS", True)
RENDER_WAIT_MS = get_env_int("SOFTCOPYRIGHT_RENDER_WAIT_MS", 1000)
MENU_CLICK_TIMEOUT_MS = get_env_int("SOFTCOPYRIGHT_MENU_CLICK_TIMEOUT_MS", 3000)
SUBMENU_WAIT_MS = get_env_int("SOFTCOPYRIGHT_SUBMENU_WAIT_MS", 500)
CJK_FONT_FAMILY = get_env_list(
    "SOFTCOPYRIGHT_CJK_FONT_FAMILY",
    ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "Microsoft YaHei", "PingFang SC"],
)
MVP_CLICK_MENU_TEXT = get_env_str("SOFTCOPYRIGHT_MVP_CLICK_MENU_TEXT", "能耗分析")

# 模板显示配置
TEMPLATE_VERSION_TEXT = get_env_str("SOFTCOPYRIGHT_TEMPLATE_VERSION_TEXT", "版本 v2.4.1 · 企业版")
TEMPLATE_ADMIN_NAME = get_env_str("SOFTCOPYRIGHT_TEMPLATE_ADMIN_NAME", "Admin")
TEMPLATE_REFRESH_TEXT = get_env_str("SOFTCOPYRIGHT_TEMPLATE_REFRESH_TEXT", "自动刷新：30s")
TEMPLATE_DATA_SOURCE_TEXT = get_env_str(
    "SOFTCOPYRIGHT_TEMPLATE_DATA_SOURCE_TEXT",
    "数据源：Modbus-TCP / OPC-UA 双通道",
)

# Word 文档配置
DOC_BODY_FONT = get_env_str("SOFTCOPYRIGHT_DOC_BODY_FONT", "仿宋_GB2312")
DOC_HEADER_FONT = get_env_str("SOFTCOPYRIGHT_DOC_HEADER_FONT", "宋体")
DOC_TITLE_FONT = get_env_str("SOFTCOPYRIGHT_DOC_TITLE_FONT", "黑体")
DOC_CODE_FONT = get_env_str("SOFTCOPYRIGHT_DOC_CODE_FONT", "Courier New")
DOC_BODY_FONT_SIZE = get_env_float("SOFTCOPYRIGHT_DOC_BODY_FONT_SIZE", 12)
DOC_SOURCE_BODY_FONT_SIZE = get_env_float("SOFTCOPYRIGHT_DOC_SOURCE_BODY_FONT_SIZE", 10.5)
DOC_TITLE_FONT_SIZE = get_env_float("SOFTCOPYRIGHT_DOC_TITLE_FONT_SIZE", 18)
DOC_SOURCE_TITLE_FONT_SIZE = get_env_float("SOFTCOPYRIGHT_DOC_SOURCE_TITLE_FONT_SIZE", 16)
DOC_CODE_FONT_SIZE = get_env_float("SOFTCOPYRIGHT_DOC_CODE_FONT_SIZE", 9)
DOC_HEADER_FONT_SIZE = get_env_float("SOFTCOPYRIGHT_DOC_HEADER_FONT_SIZE", 10)
DOC_FOOTER_FONT_SIZE = get_env_float("SOFTCOPYRIGHT_DOC_FOOTER_FONT_SIZE", 9)
SOURCE_LINES_PER_PAGE = get_env_int("SOFTCOPYRIGHT_SOURCE_LINES_PER_PAGE", 50)
SOURCE_FRONT_PAGES = get_env_int("SOFTCOPYRIGHT_SOURCE_FRONT_PAGES", 30)
SOURCE_BACK_PAGES = get_env_int("SOFTCOPYRIGHT_SOURCE_BACK_PAGES", 30)
SCREENSHOT_WIDTH_CM = get_env_float("SOFTCOPYRIGHT_SCREENSHOT_WIDTH_CM", 14)

# 校验配置
SIMILARITY_WARN_THRESHOLD = get_env_float("SOFTCOPYRIGHT_SIMILARITY_WARN_THRESHOLD", 0.3)
SIMILARITY_FAIL_THRESHOLD = get_env_float("SOFTCOPYRIGHT_SIMILARITY_FAIL_THRESHOLD", 0.4)

# 补生成脚本配置
TARGET_PROJECT_DIR = get_env_str("SOFTCOPYRIGHT_TARGET_PROJECT_DIR", "")
GENERATE_REMAINING_RELATED_CHARS = get_env_int(
    "SOFTCOPYRIGHT_GENERATE_REMAINING_RELATED_CHARS",
    400,
)
