import asyncio
import json
from typing import Any, Dict, Optional, Tuple

from ..llm_client import LLMClient
from ..models import Blueprint, CharacterTraits, Node, Worldbook, clamp_affection, parse_worldbook
from ..prompts import build_llm1_prompt, build_llm2_prompt, build_llm3_prompt


class GalGameAgent:
    def __init__(self, llm1: LLMClient, llm2: LLMClient, llm3: LLMClient):
        self.llm1 = llm1
        self.llm2 = llm2
        self.llm3 = llm3
        self.worldbook: Optional[Worldbook] = None
        self.affection: int = 0
        self.current_node_id: Optional[str] = None

    def _select_node_for_affection(self, affection: int) -> str:
        assert self.worldbook is not None, "Worldbook not initialized"
        nodes = self.worldbook.blueprint.sorted_nodes()
        candidate = nodes[0].id
        for node in nodes:
            if affection >= node.affection_threshold:
                candidate = node.id
        return candidate


async def _call_llm(llm: LLMClient, prompt: str) -> str:
    return await asyncio.to_thread(llm, prompt)


async def generate_blueprint(agent: GalGameAgent, role_desc: str, world_desc: str) -> Worldbook:
    prompt = build_llm1_prompt(role_desc, world_desc)
    raw = await _call_llm(agent.llm1, prompt)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"蓝图生成 LLM 输出非 JSON: {e} | output={raw}") from e
    worldbook = parse_worldbook(data)
    if not worldbook.blueprint.nodes:
        raise ValueError(f"蓝图生成为空，请检查 LLM 输出: {raw}")
    agent.worldbook = worldbook
    agent.affection = worldbook.traits.affection
    agent.current_node_id = agent._select_node_for_affection(agent.affection)
    return worldbook


async def dynamic_update(
    agent: GalGameAgent,
    affection: int,
    current_node_id: str,
    user_input: str,
) -> Tuple[int, str, str, Dict[str, Any]]:
    assert agent.worldbook is not None, "Worldbook not initialized"
    current_node = agent.worldbook.blueprint.nodes[current_node_id]
    prompt2 = build_llm2_prompt(user_input, affection, current_node, agent.worldbook.blueprint)
    raw2 = await _call_llm(agent.llm2, prompt2)
    try:
        llm2_out = json.loads(raw2)
    except json.JSONDecodeError as e:
        raise ValueError(f"导演数值 LLM 输出非 JSON: {e} | output={raw2}") from e

    affection = clamp_affection(int(llm2_out.get("affection", affection)))

    node_ext: Dict[str, Any] = llm2_out.get("node_extension", {}) if llm2_out.get("is_custom_node") else {}
    if llm2_out.get("is_custom_node"):
        new_node = Node(
            id=str(node_ext.get("id")),
            label=node_ext.get("label", ""),
            details=node_ext.get("details", ""),
            scene=node_ext.get("scene", ""),
            affection_threshold=int(node_ext.get("affection_threshold", affection)),
        )
        agent.worldbook.blueprint.nodes[new_node.id] = new_node
        current_node_id = new_node.id
    else:
        current_node_id = str(llm2_out.get("current_node_id", current_node_id))

    current_node_id = agent._select_node_for_affection(affection)
    agent.current_node_id = current_node_id
    logic_reason = llm2_out.get("logic_reason", "")
    return affection, current_node_id, logic_reason, node_ext


async def roleplay_turn(
    agent: GalGameAgent,
    affection: int,
    current_node_id: str,
    user_input: str,
) -> Dict[str, Any]:
    assert agent.worldbook is not None, "Worldbook not initialized"
    current_node = agent.worldbook.blueprint.nodes[current_node_id]
    prompt3 = build_llm3_prompt(user_input, agent.worldbook, current_node, affection)
    raw3 = await _call_llm(agent.llm3, prompt3)
    try:
        llm3_out = json.loads(raw3)
    except json.JSONDecodeError as e:
        raise ValueError(f"角色对话 LLM 输出非 JSON: {e} | output={raw3}") from e
    return {
        "dialogue": llm3_out.get("对话回应", ""),
        "expression": llm3_out.get("表情", ""),
        "movement": llm3_out.get("行为", ""),
        "option_a": llm3_out.get("option_a", ""),
        "option_b": llm3_out.get("option_b", ""),
    }
