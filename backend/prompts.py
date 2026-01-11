import json
from typing import Any, Dict, List, Union

from .models import Blueprint, CharacterTraits, Node, Worldbook


def build_portrait_prompt(traits: CharacterTraits) -> Dict[str, str]:
    appearance = traits.appearance
    prompt_cn = (
        "二次元立绘，全身站立，16:9，角色外貌：{appearance}。强调身高比例、脸型、发色发型、瞳色、服饰细节与可能的道具，"
        "清晰线条，galgame 角色立绘风。背景透明。仅返回图像，不需要任何说明。"
    ).format(appearance=appearance)
    prompt_en = (
        "full-body standing portrait, 1girl, galgame character illustration, 16:9, "
        f"{appearance}, focus on height proportion, face shape, hairstyle/color, eye color, outfit details, accessories or props if any, clean lines, high quality."
    )
    return {"cn": prompt_cn, "en": prompt_en}


def stage_hint(threshold: int) -> str:
    if threshold >= 91:
        return "[91-100] 宿命/结局"
    if threshold >= 76:
        return "[76-90] 深爱/危机"
    if threshold >= 51:
        return "[51-75] 暧昧/依赖"
    if threshold >= 31:
        return "[31-50] 熟络/共鸣"
    return "[0-30] 初识/防备"


def stage_node_id(node_id: str) -> Union[int, str]:
    s = str(node_id)
    prefix = "".join(ch for ch in s if ch.isdigit())
    if prefix and s.startswith(prefix):
        return int(prefix)
    return s


def build_scene_image_prompt(scene: str, stage_hint_text: str = "") -> Dict[str, str]:
    prompt_cn = (
        "galgame 背景图，16:9，立绘可覆盖前景，需留足主体空间。不允许出现主要角色，只出现场景。仅返回图像，不需要任何说明。"
        f"场景描述：{scene}；突出时间/地点/光影/氛围，与剧情阶段契合"
        f"{'，阶段提示：' + stage_hint_text if stage_hint_text else ''}。"
    )
    prompt_en = (
        "galgame background, 16:9, leave space for character sprite, "
        f"scene: {scene}; highlight time/place/lighting/atmosphere, fit current emotional stage"
        + (f", stage hint: {stage_hint_text}" if stage_hint_text else "")
        + "."
    )
    return {"cn": prompt_cn, "en": prompt_en}


def build_fused_scene_prompt(
    traits: CharacterTraits,
    scene: str,
    stage_hint_text: str = "",
    scene_details: str = "",
) -> Dict[str, str]:
    appearance = traits.appearance
    detail_hint = scene_details or "根据场景自然安排角色姿势与表情"
    prompt_cn = (
        "16:9 高质量 galgame 场景插画，角色已置于画面中。"
        f"角色外貌：{appearance}；"
        f"场景：{scene}；"
        f"剧情/姿态提示：{detail_hint}；"
        f"{'阶段提示：' + stage_hint_text + '；' if stage_hint_text else ''}"
        "要求角色自然融入环境，光影与场景一致，保持角色外观与服装细节，接触面有阴影/接触痕迹，不遮挡关键背景。"
        "避免畸形手脚、双重面部、贴图感或粗糙合成感、低分辨率。"
    )
    prompt_en = (
        "16:9 high-quality galgame scene illustration with the character in-frame. "
        f"Character appearance: {appearance}; "
        f"Scene: {scene}; "
        f"Pose/detail hint: {detail_hint}; "
        + (f"Stage hint: {stage_hint_text}; " if stage_hint_text else "")
        + "Make the character blend naturally into the environment, consistent lighting/color temperature, keep outfit/appearance, add contact shadows, avoid blocking key background. "
        "Avoid distorted limbs, duplicated faces, bad collage artifacts, low resolution."
    )
    return {"cn": prompt_cn, "en": prompt_en}


def build_final_cg_prompt(traits: CharacterTraits, scene: str) -> Dict[str, str]:
    appearance = traits.appearance
    prompt_cn = (
        "终极告白 CG，16:9，高质量、浪漫唯美、可作封面。"
        f"角色外貌：{appearance}；场景：{scene}；"
        "强调眼神交流、近距离亲密动作（牵手/拥抱/手抚脸颊），光影华丽（夕阳/月光/丁达尔），飘落光斑或花瓣。"
    )
    prompt_en = (
        "final confession CG, 16:9, high quality romantic cover-tier. "
        f"character: {appearance}; scene: {scene}; "
        "strong eye contact, intimate pose (holding hands / hugging / hand on cheek), gorgeous lighting (sunset/moonlight/god rays), floating petals or light particles."
    )
    return {"cn": prompt_cn, "en": prompt_en}


def build_llm1_prompt(role_desc: str, world_desc: str) -> str:
    return f"""
你是顶尖的恋爱游戏剧本作者，也是世界观设定大师，擅长刻画心动的可攻略角色与情绪递进。请用“电影分镜+galgame章节”风格，把简要描述扩写为完整世界书和五阶段剧情蓝图。
要求：
- 好感度阈值固定：0/31/51/76/91，五个阶段各一个节点。
- 节点名需有galgame章节感；details写具体事件+冲突+对白片段，能触发情绪波动；scene包含时间/地点/光线/气氛，便于背景图生成；开场白基于节点1。
- 性格需按好感度区分态度；背景需交代与玩家的关系、动机与隐忧。
- 必须用中文，仅输出合法 JSON，不要额外解释。

用户输入：
- 角色描述：{role_desc}
- 世界观描述：{world_desc}

输出格式：
{{
  "角色特征":{{"名字":"","外貌":"","性格":{{"[0-30]":"","[31-50]":"","[51-75]":"","[76-90]":"","[91-100]":""}},"背景设定":"","好感度":15}},
  "世界观":"",
  "剧本蓝图":{{"node":[{{"ID":1,"label":"","details":"","scene":"","affection_threshold":0}},
    {{"ID":2,"label":"","details":"","scene":"","affection_threshold":31}},
    {{"ID":3,"label":"","details":"","scene":"","affection_threshold":51}},
    {{"ID":4,"label":"","details":"","scene":"","affection_threshold":76}},
    {{"ID":5,"label":"","details":"","scene":"","affection_threshold":91}}]}},
  "开场白":""
}}
"""


def build_llm2_prompt(
    user_input: str,
    current_affection: int,
    current_node: Node,
    blueprint: Blueprint,
) -> str:
    blueprint_json = json.dumps(blueprint.to_dict(), ensure_ascii=False)
    node_json = json.dumps(current_node.to_dict(), ensure_ascii=False)
    return f"""
你是一位业界顶尖的恋爱游戏数值和剧情导演，极其擅长根据玩家输入评估角色的好感度波动，并选择合适的剧情节点或根据用户输入生成支线剧情补救。
规则与要求：
- 好感度0-100，变化需与玩家输入情感逻辑匹配，避免过度剧烈，单轮对话在-15～+15区间内变动。
- 阈值固定：0/31/51/76/91，对应1-5五个剧情节点node阶段，阶段间需有明显剧情/情绪差异，阶段内保持剧情和场景一致性；跨阈值时优先切换场景（时间/地点/氛围）或引入新配角/反派以制造张力，同时保证合理性。
- 在第五阶段用户表白后，好感度必须设置为100，不再生成新剧情。
- 剧情为网格节点式：跨阈值应进入对应蓝图节点；若玩家行为与原节点不符，可新增支线/补救节点，但仍需围绕阈值阶段演进，不要停留在同一阶段到满值。
- 冲突或反差可生成补救/支线节点；输出必须严格为合法 JSON（无需额外文本）。
输出键含义（请全部给出）：
- affection：当前好感度（0-100）。
- is_jump：yes/no，是否需要跳转到新剧情节点。
- is_custom_node：true/false，是否创建新增节点（支线/补救/结局）。
- current_node_id：当 is_custom_node 为 false 时，给出蓝图内的节点ID。
- node_extension：当 is_custom_node 为 true 时，新增节点的 id/label/details/scene/affection_threshold。
- logic_reason：解释好感度数值变化、节点跳转/新增的逻辑原因。
输出示例（请保持 JSON 严格格式）：
{{
  "affection": 0,
  "is_jump": "yes",
  "is_custom_node": false,
  "current_node_id": "2",
  "node_extension": {{
    "id": "",
    "label": "",
    "details": "",
    "scene": "",
    "affection_threshold": 0
  }},
  "logic_reason": "说明数值变动及为何生成此新节点的逻辑"
}}
注意：玩家输入可能是自由输入（未带前缀），也可能是带有 [选项A]/[选项B] 前缀的选项文本；自由输入代表玩家未选择A/B，请按实际内容判定好感变化。

当前好感度：{current_affection}
当前节点：{node_json}
原始蓝图：{blueprint_json}
用户输入：{user_input}

若需新增节点，node_extension需含 id/label/details/scene/affection_threshold。
"""


def build_llm3_prompt(
    user_input: str,
    worldbook: Worldbook,
    current_node: Node,
    affection: int,
) -> str:
    traits = worldbook.traits
    personality = json.dumps(traits.personality, ensure_ascii=False)
    return f"""
你将扮演恋爱游戏中的可攻略角色，用第一人称沉浸式回应用户输入，展示心理、表情、行为，并返回用户两条可选的推动剧情的选项。
输出严格 JSON：{{"心理变化":"","对话回应":"","表情":"","行为":"","option_a":"","option_b":""}}
- 对话应贴合当前节点与好感度语气，可轻微推进事件（移动、靠近、触碰等）。
- 选项需暗示好感度走向（正向/负向），保持角色口吻和场景逻辑。
- 用户输入可能不符合原定的剧情节点走向，需要以用户输入为准，自然地回复用户。

角色特征：
- 名字：{traits.name}
- 外貌：{traits.appearance}
- 性格分布：{personality}
- 背景设定：{traits.background}
- 当前好感度：{affection}

世界观：{worldbook.worldview}
当前节点：{json.dumps(current_node.to_dict(), ensure_ascii=False)}
用户输入：{user_input}
"""
