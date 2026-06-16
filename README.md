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

Web 演示台可以直接双击：

```text
open_web.bat
```

页面文件在：

```text
web/index.html
```

Windows 上可以直接双击：

```text
run_demo.bat
```

默认会运行完整链路：

```text
python app.py --version all --scenario complete
```

在 `sz` 目录下运行：

```bash
python app.py --version all --scenario brief
```

`brief` 场景用于演示“信息不完整时如何追问”。

如果要演示工具调用和完整链路：

```bash
python app.py --version all --scenario complete
```

只看某一个版本：

```bash
python app.py --version v2 --scenario brief
python app.py --version v6 --scenario complete
```

也可以输入自定义问题：

```bash
python app.py --version v3 --message "你们 /open/order/create 接口签名失败，appid=app_demo_001，错误码=SIGN_INVALID"
```

如果想用一键脚本指定版本和场景：

```powershell
.\run_demo.ps1 -Version v6 -Scenario complete
.\run_demo.ps1 -Version all -Scenario brief
.\run_demo.ps1 -Version v7 -Scenario secret
```

## 目录结构

```text
sz/
  app.py                         # 总入口，可选择不同版本
  data/knowledge/                # 从 llm-wiki 导出的 API 知识包
  skills/                        # 业务 Skill，每个 Skill 是一份 SOP
  src/
    common/                      # 多版本共用能力
    versions/                    # V0-V7 版本入口
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

建议先用 `brief` 场景讲 V0-V3：

```text
普通回答 -> 结构化识别 -> 校验缺口 -> 命中 Skill
```

然后切到 `complete` 场景讲 V4-V7：

```text
查文档 -> 调工具 -> 循环决策 -> 状态审计和安全边界
```

这套框架刻意不依赖真实 LLM key，便于课堂或内部分享稳定演示。后续如果要接真实模型，可以优先替换 `src/common/mock_llm.py`。
