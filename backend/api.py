import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import FRONTEND_DIR, GENERATED_DIR
from .llm_client import OpenAIChatLLM
from .models import CharacterTraits
from .services.gameplay import GalGameAgent, dynamic_update, generate_blueprint, roleplay_turn
from .services.images import generate_final_cg, generate_portrait, generate_scene_image
from .services.state import blueprint_list, load_state, state_from_agent


MEDIA_ROUTE = "/media"

app = FastAPI(title="GalGame Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(MEDIA_ROUTE, StaticFiles(directory=str(GENERATED_DIR)), name="media")
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


class GameInitRequest(BaseModel):
    role_desc: str
    world_desc: Optional[str] = ""


class GameActionRequest(BaseModel):
    session_id: str
    user_input: str


SESSIONS: Dict[str, Dict[str, Any]] = {}

LLM1 = OpenAIChatLLM()
LLM2 = OpenAIChatLLM()
LLM3 = OpenAIChatLLM()


def _url_for_path(path: Path) -> str:
    return f"{MEDIA_ROUTE}/{path.name}"


@app.post("/api/v1/game/start")
async def start_game(req: GameInitRequest) -> Dict[str, Any]:
    session_id = uuid.uuid4().hex
    agent = GalGameAgent(LLM1, LLM2, LLM3)
    worldbook = await generate_blueprint(agent, req.role_desc, req.world_desc or "")
    traits = worldbook.traits

    portrait: Optional[Path] = generate_portrait(traits, session_id)
    char_url = _url_for_path(portrait) if portrait and portrait.exists() else ""

    node = worldbook.blueprint.nodes[agent.current_node_id]  # type: ignore[index]
    scene_path = generate_scene_image(session_id, portrait, traits, node)
    scene_url = _url_for_path(scene_path) if scene_path and scene_path.exists() else ""

    SESSIONS[session_id] = {
        "state": state_from_agent(agent),
        "char_url": char_url,
        "scene_url": scene_url,
        "bg_url": scene_url,
        "final_cg_url": "",
        "portrait_path": portrait.as_posix() if portrait else "",
        "scene_paths": {node.id: scene_path.as_posix()} if scene_path else {},
    }

    return {
        "session_id": session_id,
        "opening": worldbook.opening_line,
        "char_url": char_url,
        "scene_url": scene_url,
        "bg_url": scene_url,
        "name": traits.name,
        "appearance": traits.appearance,
        "personality": traits.personality,
        "background_setting": traits.background,
        "world_view": worldbook.worldview,
        "blueprint": blueprint_list(worldbook),
        "affection": agent.affection,
        "current_node_id": agent.current_node_id,
    }


@app.post("/api/v1/game/chat")
async def chat(req: GameActionRequest) -> Dict[str, Any]:
    if req.session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    session = SESSIONS[req.session_id]
    portrait = Path(session.get("portrait_path", "")) if session.get("portrait_path") else None
    scene_paths: Dict[str, str] = dict(session.get("scene_paths") or {})
    agent = GalGameAgent(LLM1, LLM2, LLM3)
    load_state(agent, session["state"])

    affection, current_node_id, logic_reason, node_ext = await dynamic_update(
        agent, agent.affection, agent.current_node_id, req.user_input  # type: ignore[arg-type]
    )

    rp = await roleplay_turn(agent, affection, current_node_id, req.user_input)

    node = agent.worldbook.blueprint.nodes[current_node_id]  # type: ignore[union-attr]
    scene_url = session.get("scene_url", "")
    existing_scene_path = Path(scene_paths.get(node.id, "")) if scene_paths.get(node.id) else None
    if not existing_scene_path or not existing_scene_path.exists():
        existing_scene_path = generate_scene_image(req.session_id, portrait, agent.worldbook.traits, node)  # type: ignore[arg-type]
    if existing_scene_path and existing_scene_path.exists():
        scene_paths[node.id] = existing_scene_path.as_posix()
        scene_url = _url_for_path(existing_scene_path)

    final_cg_url = session.get("final_cg_url", "")
    if affection >= 100 and not final_cg_url:
        maybe_cg = generate_final_cg(req.session_id, agent.worldbook.traits, node, portrait)  # type: ignore[arg-type]
        if maybe_cg and maybe_cg.exists():
            final_cg_url = _url_for_path(maybe_cg)

    session["state"] = state_from_agent(agent)
    session["scene_url"] = scene_url
    session["bg_url"] = scene_url
    session["scene_paths"] = scene_paths
    session["final_cg_url"] = final_cg_url

    return {
        "dialogue": rp.get("dialogue", ""),
        "expression": rp.get("expression", ""),
        "movement": rp.get("movement", ""),
        "options": [rp.get("option_a", ""), rp.get("option_b", "")],
        "affection": affection,
        "current_node_id": current_node_id,
        "scene_url": scene_url,
        "bg_url": scene_url,
        "char_url": session.get("char_url", ""),
        "logic_reason": logic_reason,
        "node_extension": node_ext,
        "final_cg_url": final_cg_url,
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "GalGame Agent API. Web UI served under /app/."}
