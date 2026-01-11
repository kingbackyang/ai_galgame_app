from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class Node:
    id: str
    label: str
    details: str
    scene: str
    affection_threshold: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ID": self.id,
            "label": self.label,
            "details": self.details,
            "scene": self.scene,
            "affection_threshold": self.affection_threshold,
        }


@dataclass
class Blueprint:
    nodes: Dict[str, Node] = field(default_factory=dict)

    def sorted_nodes(self) -> List[Node]:
        return sorted(self.nodes.values(), key=lambda n: n.affection_threshold)

    def to_dict(self) -> Dict[str, Any]:
        return {"node": [n.to_dict() for n in self.sorted_nodes()]}


@dataclass
class CharacterTraits:
    name: str
    appearance: str
    personality: Dict[str, str]
    background: str
    affection: int = 0


@dataclass
class Worldbook:
    traits: CharacterTraits
    worldview: str
    blueprint: Blueprint
    opening_line: str


def parse_worldbook(data: Dict[str, Any]) -> Worldbook:
    traits_raw = data.get("角色特征", {})
    traits = CharacterTraits(
        name=traits_raw.get("名字", ""),
        appearance=traits_raw.get("外貌", ""),
        personality=traits_raw.get("性格", {}),
        background=traits_raw.get("背景设定", ""),
        affection=int(traits_raw.get("好感度", 0)),
    )
    nodes_raw = data.get("剧本蓝图", {}).get("node", [])
    nodes: Dict[str, Node] = {}
    for raw in nodes_raw:
        node = Node(
            id=str(raw.get("ID")),
            label=raw.get("label", ""),
            details=raw.get("details", ""),
            scene=raw.get("scene", ""),
            affection_threshold=int(raw.get("affection_threshold", 0)),
        )
        nodes[node.id] = node
    blueprint = Blueprint(nodes)
    return Worldbook(
        traits=traits,
        worldview=data.get("世界观", ""),
        blueprint=blueprint,
        opening_line=data.get("开场白", ""),
    )


def clamp_affection(value: int) -> int:
    return max(0, min(100, value))


def worldbook_to_blueprint(worldbook: Worldbook) -> Dict[str, Any]:
    nodes = [
        {
            "id": n.id,
            "label": n.label,
            "details": n.details,
            "scene": n.scene,
            "threshold": n.affection_threshold,
        }
        for n in worldbook.blueprint.sorted_nodes()
    ]
    return {
        "name": worldbook.traits.name,
        "appearance": worldbook.traits.appearance,
        "personality": worldbook.traits.personality,
        "speech_style": "",
        "background_setting": worldbook.traits.background,
        "world_view": worldbook.worldview,
        "initial_affection": worldbook.traits.affection,
        "opening_dialogue": worldbook.opening_line,
        "nodes": nodes,
    }


def pick_node_by_affection(nodes: List[Dict[str, Any]], affection: int) -> str:
    if not nodes:
        return ""
    candidate = nodes[0]["id"]
    for n in sorted(nodes, key=lambda x: x.get("threshold", 0)):
        if affection >= int(n.get("threshold", 0)):
            candidate = n["id"]
    return candidate


def find_node(nodes: List[Dict[str, Any]], node_id: str) -> Dict[str, Any]:
    for n in nodes:
        if str(n.get("id")) == str(node_id):
            return n
    return {}
