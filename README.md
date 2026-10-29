# RepoFix-RL

RepoFix-RL（产品名 CodeReview Tutor）是面向算法题学习者的代码诊断与复盘 Agent。用户提交题目描述、自己的代码并选择 Python 或 C++，Agent 运行代码、定位错误、构造反例并给出分层提示和解题复盘。

## 当前版本

当前技术原型包含：React/Vite 前端、FastAPI 后端、Ollama + Qwen2.5-Coder 1.5B Provider，以及用于验证模型调用和测试评分的 Python 微任务。新的题目/代码输入流程与 C++ 执行器尚在开发中；内置微任务不是正式评测集，当前也尚未进行 SFT/GRPO。

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

### 接入本地 Qwen 模型（可选）

默认仍运行确定性 demo provider。要让本地模型生成补丁，先安装 [Ollama for Windows](https://ollama.com/download/windows)，在 PowerShell 下载并启动模型：

```powershell
ollama pull qwen2.5-coder:1.5b
ollama serve
```

保持 Ollama 窗口运行，另开 PowerShell，在启动 FastAPI 前设置：

```powershell
$env:AGENT_PROVIDER = "openai-compatible"
$env:MODEL_BASE_URL = "http://127.0.0.1:11434/v1"
$env:MODEL_NAME = "qwen2.5-coder:1.5b"
```

本地 Ollama 不需要 API key。随后照常运行 `uvicorn app.main:app --reload`。健康检查 `/api/health` 会报告当前 Provider。要恢复演示模式，可在新终端（未设置这些变量）启动后端。

### 提交 ACM 模式代码进行诊断

前端接收题目描述、完整 ACM 模式 Python/C++ 程序（包含输入解析和输出）和多组样例。程序从标准输入读取数据并向标准输出打印答案。样例按 JSON 数组填写，例如：

```json
[
  {"input": "3 4\n", "expected_output": "7"},
  {"input": "10 -2\n", "expected_output": "8"}
]
```

当前 runner 面向**完整、可独立运行的 ACM stdin/stdout 程序**。每组样例会启动程序、传入对应 stdin，并将 stdout 与期望输出比较（忽略首尾空白）。当前只校验用户提供的样例，不会声称通过未提供的隐藏测试。

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

## 产品边界

MVP 面向本地算法考试练习。公开仓库使用原创题目和评测样本；执行用户代码前会设置语言专属 runner 和超时。在完整 OS/container 沙箱完成前，不应对不可信公网用户开放。

项目计划见 [`docs/项目书与任务拆分.md`](docs/项目书与任务拆分.md)。
