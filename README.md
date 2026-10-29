# RepoFix-RL

RepoFix-RL 是面向小型 Python 仓库的代码修复 Agent 原型，目标是将 Agent 运行、自动测试奖励和 GRPO 后训练实验串成可观察、可复现的闭环。

## 当前版本

首个本地原型包含：FastAPI 后端、可替换的 Agent Provider、隔离的临时任务工作区、pytest 评分器、运行轨迹与 unified diff API，以及 React/Vite 演示前端。当前默认 Provider 是**确定性演示 Provider**，只用于验证产品链路；它不是语言模型，也不代表已实现训练。

## 快速开始

### 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

后端默认监听 `http://127.0.0.1:8000`。API 文档位于 `/docs`。

### 前端

```powershell
cd frontend
npm install
npm run dev
```

Vite 会将 `/api` 请求代理到本地 FastAPI。页面默认在 `http://127.0.0.1:5173`。

## 项目结构

- `frontend/`：任务选择、运行状态、工具轨迹、评分和补丁 diff。
- `backend/app/`：API、任务定义、Agent provider、工具与评测器。
- `backend/tests/`：后端接口和评测器单元测试。
- `training/`：后续 SFT/GRPO 配置与入口。
- `data/`：任务定义和数据说明；模型、数据等大文件不入 Git。
- `experiments/`：实验记录模板与结果摘要。
- `scripts/`：开发和评测辅助脚本。
- `docs/`：项目书及复现说明。

## 当前边界

执行器仅对内置演示任务创建临时副本并运行固定 pytest 命令，不接受用户上传仓库或任意命令。演示修复由规则 Provider 生成，真实模型调用、模型训练、容器级沙箱和生产部署尚未接入。

项目计划见 [`docs/项目书与任务拆分.md`](docs/项目书与任务拆分.md)。
