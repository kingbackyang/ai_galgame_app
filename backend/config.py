import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(ENV_PATH)


@dataclass
class Settings:
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    # 留空使用 dashscope SDK 默认 (https://dashscope.aliyuncs.com/api/v1)。
    # 仅在自定义网关时设置；兼容模式 URL 不适用于 dashscope SDK。
    dashscope_base_url: str = os.getenv("DASHSCOPE_BASE_URL", "")
    dashscope_model: str = os.getenv("DASHSCOPE_MODEL", "qwen-plus")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_vertex_base_url: str = os.getenv("GOOGLE_VERTEX_BASE_URL", "")
    image_output_dir: Path = Path(os.getenv("IMAGE_OUTPUT_DIR", ROOT_DIR / "generated"))
    log_file: Path = Path(os.getenv("GALGAME_LOG_FILE", ROOT_DIR / "session_log.txt"))


settings = Settings()


def _abs_path(path_value: Path) -> Path:
    return path_value if path_value.is_absolute() else ROOT_DIR / path_value


settings.image_output_dir = _abs_path(settings.image_output_dir)
settings.log_file = _abs_path(settings.log_file)
settings.image_output_dir.mkdir(parents=True, exist_ok=True)

# Reuse a top-level generated directory for API static serving
GENERATED_DIR = settings.image_output_dir
FRONTEND_DIR = ROOT_DIR / "frontend"
