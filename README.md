# API 接入 Agent 多版本演进 Demo

这个目录是一套用于讲解和实战演示的 Agent 框架。它用同一个 API 接入场景，演示系统如何从“普通问答”逐步演进为“可追问、可查文档、可调工具、可复盘”的业务 Agent。

核心演示问题：

```text
你们接口一直签名失败，帮忙看下
```

## 版本设计

| 版本 | 演示能力 | 关键变化 |
| --- | --- | --- |
| V0 | 普通问答 | 直接让模型回答，容易泛泛而谈 |
| V1 | 任务识别 | 把自然语言转成结构化任务 |
| V2 | Schema 校验 + 追问 | 代码判断缺什么，不让模型硬答 |
| V3 | Skill 路由 | 根据任务类型命中业务 SOP |
| V4 | 文档检索 | 回答前先找依据，减少编造 |
| V5 | 工具调用 | 用工具检查参数排序、错误码、日志 |
| V6 | Agent Loop | Observe -> Think -> Act -> Observe -> Answer |
| V7 | 状态 / 审计 / 安全边界 | 增加 Task State、Audit、敏感信息保护和人工闸门 |

## 快速运行

### 🌐 Web Demo（主力演示，推荐）

**用途**：完整的 Agent 系统演示，包含可视化、交互、多轮对话

```bash
# 方式1：直接打开（Windows）
open_web.bat

# 方式2：启动 LLM 代理 + Web 服务器（支持 Agent Chat 模式）
start_agent.bat
# 或手动启动：
python web/proxy.py          # LLM 代理（端口 8081）
python -m http.server 8080 --directory web  # Web 服务器
# 然后访问 http://localhost:8080/
```

**推荐场景**：
- ✅ 产品演示、客户汇报
- ✅ 展示完整能力（混合意图识别、Agent Chat、白盒追踪）
- ✅ 交互式探索（切换场景、实时对话、可视化决策路径）
- ✅ 多轮对话（会话管理、字段补充、上下文记忆）

页面文件：`web/index.html`

---

### 💻 CLI Demo（版本对比工具）

**用途**：快速切换 V0-V7，体验演进路径，讲解代码实现

```bash
# 对比不同版本的能力差异
python app.py --version v0 --scenario brief  # V0: 黑盒回答，泛泛而谈
python app.py --version v1 --scenario brief  # V1: 任务识别，提取字段
python app.py --version v2 --scenario brief  # V2: Schema 校验，追问缺口
python app.py --version v6 --scenario brief  # V6: Agent Loop 完整流程
python app.py --version v7 --scenario secret # V7: 安全边界，脱敏阻断

# 运行所有版本（看完整演进）
python app.py --version all --scenario brief

# 完整场景（包含工具调用）
python app.py --version all --scenario complete

# 自定义输入
python app.py --version v3 --message “你们 /open/order/create 接口签名失败，appid=app_demo_001，错误码=SIGN_INVALID”

# PowerShell 快捷脚本
.\run_demo.ps1 -Version v6 -Scenario complete
```

**推荐场景**：
- ✅ 技术培训（讲解演进思路，快速切换版本）
- ✅ 代码审查（理解实现逻辑，每个版本独立文件 `src/versions/vX_*.py`）
- ✅ 文档制作（纯文本输出，易截图对比，制作 PPT）
- ✅ 版本对比（无状态干扰，输入输出一一对应）

> **说明**：CLI 是基础实现，用于快速体验版本差异和讲解代码。Web 包含更多能力（混合意图识别、会话管理、可视化）。

## 目录结构

```text
agent/
  app.py                         # CLI 入口，版本切换工具
  web/
    index.html                   # Web Demo 主文件（主力演示）
    proxy.py                     # LLM API 代理（绕过 CORS）
    knowledge.js                 # 内嵌知识包
  data/knowledge/                # 从 llm-wiki 导出的 API 知识包
  skills/                        # 业务 Skill，每个 Skill 是一份 SOP
  src/
    common/                      # 共用模块（意图识别、RAG、工具、Schema）
    versions/                    # V0-V7 版本入口（CLI 用，代码参考）
```

## 知识来源

V4 文档检索会按顺序查找：

1. `data/knowledge/` 中的导出包
2. 本机 `D:/zuhaowan-ai/llm-wiki/projects/api-infra`
3. GitHub 上的远程索引：`huakaiwuyeshu/llm-wiki` 的 `projects/api-infra/exports/agent-demo/search_index.json`

更新 llm-wiki 后，可以同步到 demo：

```powershell
python sync_knowledge.py
```

网页演示会读取 `web/knowledge.js`，本地包未命中时会尝试查询远程 llm-wiki 索引。

## 讲解建议

### 演示流程（推荐）

**主屏幕：Web Demo**
- 打开 `web/index.html`，展示完整 Agent 能力
- 可视化展示决策路径、知识检索、工具调用
- 演示 Agent Chat 模式（多轮对话）

**副屏幕：CLI Demo（版本对比）**
```bash
# 快速切换版本，对比演进路径
python app.py --version v0 --scenario brief  # 黑盒回答
python app.py --version v2 --scenario brief  # 追问机制
python app.py --version v6 --scenario brief  # Agent Loop
```

### 版本讲解顺序

**阶段 1：`brief` 场景（V0-V3）**
- 暴露问题 → 识别任务 → 校验缺口 → 命中 Skill

```bash
python app.py --version v0 --scenario brief  # V0: 泛泛而谈
python app.py --version v1 --scenario brief  # V1: 识别 signature_debug
python app.py --version v2 --scenario brief  # V2: 追问缺失字段
python app.py --version v3 --scenario brief  # V3: 路由到 Skill SOP
```

**阶段 2：`complete` 场景（V4-V7）**
- 查文档 → 调工具 → 循环决策 → 状态审计和安全边界

```bash
python app.py --version v4 --scenario complete  # V4: RAG 检索文档
python app.py --version v5 --scenario complete  # V5: 工具检查签名排序
python app.py --version v6 --scenario complete  # V6: Agent Loop 闭环
python app.py --version v7 --scenario secret    # V7: 安全边界阻断
```

### 代码讲解

查看某个版本的实现逻辑（代码简洁，易讲解）：
- `src/versions/v2_validator_clarify.py`（1.1KB，追问机制）
- `src/versions/v6_agent_loop.py`（3.0KB，Agent Loop 实现）
- `src/common/mock_llm.py`（意图识别正则实现）
- `src/common/rag.py`（三层检索逻辑）
