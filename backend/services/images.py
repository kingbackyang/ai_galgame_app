from pathlib import Path
from typing import Any, Dict, Optional

from ..config import GENERATED_DIR
from ..llm_client import img2img, text2img
from ..models import CharacterTraits, Node
from ..prompts import build_final_cg_prompt, build_fused_scene_prompt, build_portrait_prompt, stage_hint


def _find_existing_image(base: Path) -> Optional[Path]:
    if base.exists():
        return base
    stem = base.with_suffix("").name
    candidates = sorted(base.parent.glob(f"{stem}*.png"))
    return candidates[0] if candidates else None


def _safe_text2img(prompt: str, output: Path) -> Optional[Path]:
    existing = _find_existing_image(output)
    if existing:
        return existing
    try:
        res = text2img(prompt, filename_prefix=output.with_suffix("").as_posix())
        paths = res.get("saved_paths") or []
        if paths:
            return Path(paths[0])
    except Exception:
        return None
    return None


def _safe_img2img(prompt: str, init_image: Path, output: Path) -> Optional[Path]:
    existing = _find_existing_image(output)
    if existing:
        return existing
    try:
        res = img2img(init_image.as_posix(), prompt, filename_prefix=output.with_suffix("").as_posix())
        paths = res.get("saved_paths") or []
        if paths:
            return Path(paths[0])
    except Exception:
        return None
    return None


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(value))


def portrait_path(session_id: str) -> Path:
    return GENERATED_DIR / f"portrait_{session_id}.png"


def scene_cg_path(session_id: str, node_id: str) -> Path:
    safe_node = _safe_name(node_id)
    return GENERATED_DIR / f"scene_{session_id}_node_{safe_node}.png"


def final_cg_path(session_id: str) -> Path:
    return GENERATED_DIR / f"final_cg_{session_id}.png"


def generate_portrait(traits: CharacterTraits, session_id: str) -> Optional[Path]:
    prompt = build_portrait_prompt(traits)["cn"]
    return _safe_text2img(prompt, portrait_path(session_id))


def generate_scene_image(
    session_id: str,
    portrait: Optional[Path],
    traits: CharacterTraits,
    node: Node,
) -> Optional[Path]:
    target = scene_cg_path(session_id, node.id)
    prompt = build_fused_scene_prompt(traits, node.scene, stage_hint(node.affection_threshold), node.details)["cn"]
    if portrait and portrait.exists():
        maybe = _safe_img2img(prompt, portrait, target)
        if maybe:
            return maybe
    return _safe_text2img(prompt, target)


def generate_final_cg(session_id: str, traits: CharacterTraits, node: Node, portrait: Optional[Path]) -> Optional[Path]:
    prompt_map = build_final_cg_prompt(traits, node.scene)
    prompt_cn = prompt_map["cn"] + " 角色保持外观一致，自然融入场景，光影统一。"
    target = final_cg_path(session_id)
    if portrait and portrait.exists():
        maybe = _safe_img2img(prompt_cn, portrait, target)
        if maybe:
            return maybe
    return _safe_text2img(prompt_cn, target)
