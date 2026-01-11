import base64
import io
import os
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import dashscope
from PIL import Image
from google import genai

from .config import settings


# Allow overriding endpoints via .env (default保持 dashscope SDK 官方地址 https://dashscope.aliyuncs.com/api/v1)
if settings.dashscope_base_url and "compatible-mode" not in settings.dashscope_base_url:
    dashscope.base_http_api_url = settings.dashscope_base_url
if settings.google_vertex_base_url:
    os.environ["GOOGLE_VERTEX_BASE_URL"] = settings.google_vertex_base_url

# Shared clients
_genai_client = genai.Client(api_key=settings.google_api_key) if settings.google_api_key else None


class LLMClient:
    def __init__(self, caller: Callable[[str], str]):
        self.caller = caller

    def __call__(self, prompt: str) -> str:
        return self.caller(prompt)


class OpenAIChatLLM(LLMClient):
    def __init__(self, model: str = settings.dashscope_model, temperature: float = 0.7, timeout: int = 60):
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        super().__init__(self._call)

    def _call(self, prompt: str) -> str:
        if not settings.dashscope_api_key:
            raise RuntimeError("DASHSCOPE_API_KEY 未设置，无法调用大模型")
        resp = dashscope.Generation.call(
            api_key=settings.dashscope_api_key,
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个有用的助手，按要求返回 JSON。"},
                {"role": "user", "content": prompt},
            ],
            enable_search=False,
            result_format="message",
            temperature=self.temperature,
            stream=False,
        )
        status = getattr(resp, "status_code", 200)
        if status != 200 or not getattr(resp, "output", None):
            code = getattr(resp, "code", "")
            msg = getattr(resp, "message", "dashscope 调用失败")
            raise RuntimeError(f"DashScope error status={status} code={code} msg={msg}")
        return resp.output.choices[0].message.content


def _load_image(data: Union[str, bytes]) -> Optional[Image.Image]:
    if isinstance(data, bytes):
        try:
            return Image.open(io.BytesIO(data)).convert("RGB")
        except Exception:
            return None
    if os.path.exists(str(data)):
        try:
            return Image.open(str(data)).convert("RGB")
        except Exception:
            return None
    try:
        decoded = base64.b64decode(data)
        return Image.open(io.BytesIO(decoded)).convert("RGB")
    except Exception:
        return None


def _save_response_images(resp: Any, filename_prefix: str) -> List[str]:
    prefix_path = Path(filename_prefix)
    base_dir = prefix_path.parent if prefix_path.parent != Path(".") else settings.image_output_dir
    stem = prefix_path.name if prefix_path.parent != Path(".") else filename_prefix
    base_dir.mkdir(parents=True, exist_ok=True)
    saved: List[str] = []
    idx = 0
    for part in getattr(resp, "parts", []) or []:
        inline_data = getattr(part, "inline_data", None)
        if inline_data is not None:
            try:
                if hasattr(part, "as_image"):
                    img = part.as_image()
                else:
                    img = Image.open(io.BytesIO(inline_data.data)).convert("RGB")  # type: ignore[arg-type]
                fname = f"{stem}_{idx}.png"
                path = base_dir / fname
                img.save(path)
                saved.append(path.as_posix())
                idx += 1
            except Exception:
                continue
    return saved


def _extract_text_parts(resp: Any) -> List[str]:
    texts: List[str] = []
    for part in getattr(resp, "parts", []) or []:
        if getattr(part, "text", None):
            texts.append(part.text)
    return texts


def text2img(prompt: str, seed: Optional[int] = None, filename_prefix: str = "text2img") -> Dict[str, Any]:
    if not _genai_client:
        raise RuntimeError("GOOGLE_API_KEY 未设置，无法调用图像模型")
    resp = _genai_client.models.generate_content(model="gemini-2.5-flash-image", contents=prompt)
    paths = _save_response_images(resp, filename_prefix)
    return {"response": resp, "saved_paths": paths, "texts": _extract_text_parts(resp)}


def img2img(init_image: str, prompt: str, seed: Optional[int] = None, filename_prefix: str = "img2img") -> Dict[str, Any]:
    if not _genai_client:
        raise RuntimeError("GOOGLE_API_KEY 未设置，无法调用图像模型")
    ref_img = _load_image(init_image)
    contents: List[Any] = [prompt]
    if ref_img is not None:
        contents.append(ref_img)
    else:
        contents.append(prompt)
    resp = _genai_client.models.generate_content(model="gemini-2.5-flash-image", contents=contents)
    paths = _save_response_images(resp, filename_prefix)
    return {"response": resp, "saved_paths": paths, "texts": _extract_text_parts(resp)}


@dataclass
class EchoJSONLLM(LLMClient):
    canned: Dict[str, Any] = None  # type: ignore[assignment]

    def __init__(self, canned: Dict[str, Any]):
        self.canned = canned
        super().__init__(lambda prompt: json.dumps(canned, ensure_ascii=False))
