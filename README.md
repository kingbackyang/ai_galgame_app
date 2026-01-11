# GalGame World

生成恋爱养成剧情、立绘与场景的演示项目。后端负责调用大模型和图像模型，前端纯渲染，密钥与接口地址通过 `.env` 注入。

## 目录结构
- `backend/`：FastAPI 应用、数据模型、提示词、LLM/图像封装与业务逻辑
- `frontend/`：纯前端静态页面，调用后端 API（无密钥暴露）
- `generated/`：后端生成的图片与媒体文件
- `.env.example`：环境变量示例

## 环境依赖
- Python 3.9+
- pip
- 可访问 DashScope（文本模型）与 Google Gemini Image（图像模型）的网络环境
- [DASHSCOPE_API_KEY](https://bailian.console.aliyun.com/?spm=5176.29597918.J_C-NDPSQ8SFKWB4aef8i6I.1.30977b08c62as2&tab=api#/api)
- [GOOGLE_API_KEY](https://aistudio.google.com/api-keys)
## 快速开始
1. 复制并填写环境变量：
   ```bash
   cp galgame_app/.env.example galgame_app/.env
   # 填写 [DASHSCOPE_API_KEY] () / GOOGLE_API_KEY 等
   ```
   
2. 安装依赖：
   ```bash
   pip install -r galgame_app/backend/requirements.txt
   ```
3. 启动后端（默认 http://localhost:8000）：
   ```bash
   uvicorn galgame_app.backend.api:app --reload
   ```
4. 打开前端：
   - 浏览器访问 `http://localhost:8000/app/`
   - API 基础路径：`/api/v1`

## 环境变量
在 `galgame_app/.env` 中配置：
- `DASHSCOPE_API_KEY`：文本模型密钥
- `DASHSCOPE_BASE_URL`：可选，DashScope 兼容模式 URL
- `DASHSCOPE_MODEL`：默认 `qwen-plus`
- `GOOGLE_API_KEY`：Gemini 图像模型密钥
- `GOOGLE_VERTEX_BASE_URL`：可选，自定义 Vertex 兼容 URL
- `IMAGE_OUTPUT_DIR`：生成图片输出目录（默认 `generated`）
- `GALGAME_LOG_FILE`：日志文件路径（默认 `logs/session_log.txt`）

## API
- `POST /api/v1/game/start`：生成角色、世界观与初始场景
  - 请求：`{ "role_desc": "...", "world_desc": "..." }`
  - 响应：`session_id`、`opening`、`blueprint`、`scene_url` 等
- `POST /api/v1/game/chat`：基于会话继续对话
  - 请求：`{ "session_id": "...", "user_input": "..." }`
  - 响应：角色对话、好感度、当前节点、选项、场景 URL、结局 CG（可选）

## 前端使用
- 入口：`frontend/index.html`（由后端静态托管 `/app`）
- 配置：`frontend/app.js` 中的 `API_BASE` 默认为 `/api/v1`
- 前端不存储或暴露任何密钥

## 开发提示
- 业务逻辑与模型：`backend/services/`、`backend/models.py`
- 提示词集中在：`backend/prompts.py`
- 图像生成封装：`backend/services/images.py`
- 更新 UI 主题/布局：`frontend/styles.css` 和 `frontend/index.html`

## 💖 Support & VIP Edition

如果你对 **GalGame Agent（AI 恋爱养成 / 剧情生成 / 多模态交互）** 项目感兴趣，  
或者正在关注 **AI GalGame / AI 剧情生成 / AI 虚拟角色陪伴** 相关方向，  
欢迎通过微信支持本项目的发展。

**VIP 版本正在开发中**，你的支持将用于更强大的模型、更高质量的图像生成，以及更沉浸的交互体验。

- 微信赞助
<p align="center">
  <img src="assets/shoukuan.jpg" alt="WeChat Pay QR Code" width="220">
</p>

---

## 🌟 GalGame Agent · VIP Edition（规划中）

VIP 版本不仅仅是模型规模的提升，而是一次 **完整的沉浸式 GalGame 体验升级**。

- 🎭 **更精彩、跌宕起伏的剧情**
  - 多阶段叙事结构：序章 / 分支线 / 个人线 / 真结局
  - 角色具备长期记忆、隐性动机与情绪演化
  - 关键选择将永久影响剧情走向，而非一次性分支

- 🎨 **更高质量的图像生成**
  - 角色立绘风格高度一致，角色身份稳定
  - 场景 CG 具备镜头语言、氛围光影与叙事构图
  - 重要剧情节点解锁专属 CG / Ending 插画

- 🔊 **语音与沉浸式体验（规划中）**
  - 角色对白支持 TTS（多情绪、多声线）
  - 自动生成场景环境音与背景音乐（BGM）
  - 可扩展为视觉小说模式或 AI 陪伴模式

- 🧠 **更智能的 GalGame Agent 内核**
  - 好感度升级为关系状态机，而非简单数值
  - 支持隐藏事件、彩蛋路线与多周目体验
  - 提供面向创作者的剧情与世界观扩展接口


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

