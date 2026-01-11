const API_BASE = "/api/v1";

let sessionId = null;
let history = [];
let blueprintNodes = [];

const els = {
  startBtn: document.getElementById("start-btn"),
  startInline: document.getElementById("start-inline"),
  roleInput: document.getElementById("role-input"),
  worldInput: document.getElementById("world-input"),
  startHint: document.getElementById("start-hint"),
  bgImage: document.getElementById("bg-image"),
  overlay: document.getElementById("overlay"),
  charName: document.getElementById("char-name"),
  nodeLabel: document.getElementById("node-label"),
  affection: document.getElementById("affection"),
  dialogueName: document.getElementById("dialogue-name"),
  dialogueText: document.getElementById("dialogue-text"),
  choiceA: document.getElementById("choice-a"),
  choiceB: document.getElementById("choice-b"),
  userInput: document.getElementById("user-input"),
  sendBtn: document.getElementById("send-btn"),
  logicText: document.getElementById("logic-text"),
  worldView: document.getElementById("world-view"),
  traitAppearance: document.getElementById("trait-appearance"),
  traitPersonality: document.getElementById("trait-personality"),
  traitBackground: document.getElementById("trait-background"),
  blueprintList: document.getElementById("blueprint-list"),
  convList: document.getElementById("conv-list"),
  copyLog: document.getElementById("copy-log"),
};

function cacheBust(url) {
  return url ? `${url}${url.includes("?") ? "&" : "?"}${Date.now()}` : "";
}

function setScene(url) {
  if (!url) {
    els.bgImage.style.display = "none";
    return;
  }
  els.bgImage.style.display = "block";
  els.bgImage.src = cacheBust(url);
}

function setOverlay(msg) {
  els.overlay.style.display = msg ? "grid" : "none";
  els.overlay.textContent = msg || "";
  els.sendBtn.disabled = !!msg;
  els.userInput.disabled = !!msg;
  els.startBtn.disabled = !!msg;
  els.startInline.disabled = !!msg;
}

function appendHistory(type, text) {
  history.push({ type, text });
  renderConv();
}

function renderConv() {
  els.convList.innerHTML = "";
  if (!history.length) {
    els.convList.innerHTML = '<div class="placeholder">尚无对话</div>';
    return;
  }
  history.forEach((h) => {
    const div = document.createElement("div");
    div.className = `bubble ${h.type}`;
    const meta = h.type === "user" ? "玩家" : h.type === "actor" ? "角色" : "导演";
    div.innerHTML = `<div class="meta">${meta}</div><div>${h.text}</div>`;
    els.convList.appendChild(div);
  });
  els.convList.scrollTop = els.convList.scrollHeight;
}

function renderBlueprint() {
  els.blueprintList.innerHTML = "";
  if (!blueprintNodes.length) {
    els.blueprintList.innerHTML = '<div class="placeholder">暂无蓝图</div>';
    return;
  }
  blueprintNodes.forEach((n) => {
    const card = document.createElement("div");
    card.className = "bp-card";
    card.innerHTML = `
      <div class="title">${n.id} · ${n.label}</div>
      <div class="scene">阈值 ${n.affection_threshold} · ${n.scene || "-"}</div>
      <div class="detail">${n.details || "-"}</div>
    `;
    els.blueprintList.appendChild(card);
  });
}

async function startGame() {
  setOverlay("生成世界中...");
  els.startHint.textContent = "正在调用后端 API...";
  try {
    const res = await fetch(`${API_BASE}/game/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role_desc: els.roleInput.value || "温柔邻家女孩，善良且坚韧",
        world_desc: els.worldInput.value || "现代都市老街小餐馆",
      }),
    });
    if (!res.ok) throw new Error("start failed");
    const data = await res.json();
    sessionId = data.session_id;
    els.charName.textContent = data.name || "角色";
    els.dialogueName.textContent = data.name || "角色";
    els.dialogueText.textContent = data.opening || "......";
    els.affection.textContent = `好感度 ${data.affection ?? "-"}`;
    els.nodeLabel.textContent = `节点 ${data.current_node_id ?? "-"}`;
    setScene(data.scene_url || data.bg_url || "");
    els.startHint.textContent = "";
    els.worldView.textContent = data.world_view || "-";
    els.traitAppearance.textContent = data.appearance || "-";
    els.traitPersonality.textContent = JSON.stringify(data.personality || {});
    els.traitBackground.textContent = data.background_setting || "-";
    blueprintNodes = data.blueprint || [];
    renderBlueprint();
    history = [];
    if (data.opening) appendHistory("actor", data.opening);
  } catch (err) {
    els.startHint.textContent = "启动失败，请检查 .env 与后端";
  } finally {
    setOverlay("");
  }
}

async function sendInput(text) {
  if (!sessionId) {
    alert("请先点击“开始一段新故事”");
    return;
  }
  if (!text.trim()) return;
  appendHistory("user", text);
  els.userInput.value = "";
  els.choiceA.style.display = "none";
  els.choiceB.style.display = "none";
  setOverlay("角色思考中...");
  try {
    const res = await fetch(`${API_BASE}/game/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, user_input: text }),
    });
    if (!res.ok) throw new Error("chat failed");
    const data = await res.json();
    els.dialogueText.textContent = data.dialogue || "";
    els.affection.textContent = `好感度 ${data.affection ?? "-"}`;
    els.nodeLabel.textContent = `节点 ${data.current_node_id ?? "-"}`;
    els.logicText.textContent = data.logic_reason || "-";
    if (data.final_cg_url) {
      setScene(data.final_cg_url);
    } else {
      setScene(data.scene_url || data.bg_url || "");
    }
    appendHistory("actor", data.dialogue || "");
    if (data.logic_reason) appendHistory("director", data.logic_reason);
    const opts = data.options || [];
    if (opts[0]) {
      els.choiceA.textContent = opts[0];
      els.choiceA.style.display = "inline-flex";
      els.choiceA.onclick = () => sendInput(opts[0]);
    }
    if (opts[1]) {
      els.choiceB.textContent = opts[1];
      els.choiceB.style.display = "inline-flex";
      els.choiceB.onclick = () => sendInput(opts[1]);
    }
  } catch (err) {
    appendHistory("director", "请求失败，请检查后端与密钥配置");
  } finally {
    setOverlay("");
  }
}

function wireEvents() {
  els.startBtn.addEventListener("click", startGame);
  els.startInline.addEventListener("click", startGame);
  els.sendBtn.addEventListener("click", () => sendInput(els.userInput.value));
  els.userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendInput(els.userInput.value);
  });
  els.copyLog.addEventListener("click", async () => {
    try {
      const text = history.map((h) => `[${h.type}] ${h.text}`).join("\n");
      await navigator.clipboard.writeText(text);
      alert("已复制对话历史");
    } catch {
      alert("复制失败，请手动选择文本");
    }
  });
}

renderConv();
renderBlueprint();
setScene("");
wireEvents();
