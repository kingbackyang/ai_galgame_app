# GalGame Agent（前后端分离）

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

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

