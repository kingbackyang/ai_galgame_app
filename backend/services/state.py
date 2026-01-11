from typing import Any, Dict, List

from ..models import Worldbook, parse_worldbook
from ..services.gameplay import GalGameAgent


def blueprint_list(worldbook: Worldbook) -> List[Dict[str, Any]]:
    return [
        {
            "id": n.id,
            "label": n.label,
            "details": n.details,
            "scene": n.scene,
            "affection_threshold": n.affection_threshold,
        }
        for n in worldbook.blueprint.sorted_nodes()
    ]


def state_from_agent(agent: GalGameAgent) -> Dict[str, Any]:
    assert agent.worldbook is not None
    wb = agent.worldbook
    traits = wb.traits
    return {
        "worldbook": {
            "角色特征": {
                "名字": traits.name,
                "外貌": traits.appearance,
                "性格": traits.personality,
                "背景设定": traits.background,
                "好感度": traits.affection,
            },
            "世界观": wb.worldview,
            "开场白": wb.opening_line,
            "剧本蓝图": wb.blueprint.to_dict(),
        },
        "affection": agent.affection,
        "current_node_id": agent.current_node_id,
    }


def load_state(agent: GalGameAgent, state: Dict[str, Any]) -> None:
    agent.worldbook = parse_worldbook(state["worldbook"])
    agent.affection = int(state.get("affection", 0))
    agent.current_node_id = str(state.get("current_node_id"))
