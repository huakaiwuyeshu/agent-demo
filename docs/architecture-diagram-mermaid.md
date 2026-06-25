# API 智能客服 Agent 交互架构图 V2

基于当前 demo 实际能力的完整架构图（含记忆系统、ReAct Layer 4、可观测性）

---

## 主流程架构图

```mermaid
flowchart TB
    subgraph Input["模块1: 用户/行业输入"]
        UserInput["用户输入<br/>描述 API 问题 + 关键字段"]
        FieldExtract["字段提取<br/>appid、error_code、api_path<br/>analysis_dimension、analysis_scope"]
        SensitiveCheck["敏感信息自查<br/>appsecret → 拒绝"]
    end

    subgraph Intent["模块2: 安全 + 意图识别"]
        SecurityGate["2.1 安全检测 + 范围边界<br/>敏感信息检测 | 范围限定 | 语义过滤"]
        
        subgraph HybridIntent["2.2 四层混合意图识别"]
            Layer1["Layer 1: Rule-First<br/>关键词权重匹配<br/>Cost: 0 tokens, <10ms"]
            Layer2["Layer 2: Vector Fallback<br/>Token overlap 相似度<br/>Cost: 0 tokens"]
            Layer3["Layer 3: LLM Hints<br/>Pattern 匹配<br/>Cost: 0 tokens (simulated)"]
            Layer4["Layer 4: ReAct Loop 🆕<br/>LLM 自主循环<br/>Cost: 5-10k tokens<br/>触发率: ~5-10%"]
        end
        
        IntentOutput["输出<br/>task_type + 字段草稿 + 置信度"]
    end

    subgraph LLMRouting["模块3: LLM 管理路由"]
        subgraph SchemaValidation["3.1 Schema 校验"]
            SchemaCheck["检查必填字段<br/>signature_debug: appid + error_code + ...<br/>volume_analysis: dimension + scope 🆕"]
            ValidationResult{"校验结果"}
            Executable["executable<br/>字段齐全"]
            NeedsClarification["needs_clarification<br/>缺失字段 → 精准追问"]
            Blocked["blocked<br/>安全边界触发"]
        end
        
        subgraph Memory["3.2 记忆系统 🆕"]
            ShortTerm["短期记忆 (24h TTL)<br/>• 字段记忆：跨轮累积<br/>• 对话上下文：最近10轮+压缩<br/>• 会话状态：activeTask"]
            LongTerm["长期记忆 (无TTL)<br/>• localStorage: 100条任务<br/>• TF-IDF + 时间衰减<br/>• Top 3 相似案例注入 Prompt"]
        end
        
        subgraph SkillRouting["3.3 Skill 路由"]
            SkillMatch["按 task_type 命中 SOP<br/>🔐 签名排查 | 📞 回调异常<br/>❓ 字段问答 | 📊 数据分析<br/>🚀 新接入 | ⚠️ 人工闸门"]
        end
        
        ResultOrchestration["3.4 结果编排<br/>文档 + 工具 + 上下文 → 生成答案"]
    end

    subgraph ToolsRetrieval["模块4: 工具 + 检索执行"]
        subgraph Skills["4.1 Skills / SOP 能力库"]
            SkillDocs["固定 Skills (预定义能力单元)<br/>✅ 签名排查 Skill (15步SOP)<br/>✅ 回调异常排查 Skill<br/>✅ API 字段问答 Skill<br/>✅ 数据分析 Skill 🆕"]
        end
        
        subgraph Tools["4.2 工具调用"]
            SignatureTools["签名工具<br/>check_signature_order<br/>validate_timestamp<br/>check_encoding"]
            DataTools["数据分析工具 🆕<br/>analyze_time_trend<br/>analyze_channel_comparison<br/>⚠️ 静态Excel快照<br/>无法查询指定日期"]
        end
        
        subgraph Knowledge["4.3-4.5 知识检索"]
            LocalKnowledge["本地知识包<br/>FAQ + 错误码表 + SOP"]
            RemoteWiki["远程 llm-wiki<br/>1400+ 文档段"]
            FederatedSearch["联邦搜索 cascade<br/>本地 → 远程 → 安全检查"]
        end
        
        LongTermRetrieval["4.6 长期记忆检索 🆕<br/>Top 3 相似案例 → Prompt"]
    end

    subgraph Output["模块5: 结果反馈用户"]
        StructuredOutput["5.1 结构化组织<br/>问题定位 + 修复建议"]
        ContextCitation["5.2 引用 Context 路径<br/>文档来源 | 工具结果 | 历史案例"]
        UserFeedback["5.3 获取 Session 反馈<br/>(可暂缓)"]
    end

    %% Main flow connections
    UserInput --> FieldExtract --> SensitiveCheck
    SensitiveCheck --> SecurityGate
    SecurityGate --> Layer1
    Layer1 -->|fail| Layer2
    Layer2 -->|fail| Layer3
    Layer3 -->|fail| Layer4
    Layer1 -->|success| IntentOutput
    Layer2 -->|success| IntentOutput
    Layer3 -->|success| IntentOutput
    Layer4 --> IntentOutput
    
    IntentOutput --> SchemaCheck
    SchemaCheck --> ValidationResult
    ValidationResult --> Executable
    ValidationResult --> NeedsClarification
    ValidationResult --> Blocked
    
    NeedsClarification -.回复用户.-> Output
    Blocked -.拒绝.-> Output
    
    Executable --> ShortTerm
    Executable --> LongTerm
    Executable --> SkillMatch
    
    SkillMatch --> Skills
    SkillMatch --> Tools
    SkillMatch --> Knowledge
    SkillMatch --> LongTermRetrieval
    
    Skills --> ResultOrchestration
    Tools --> ResultOrchestration
    Knowledge --> ResultOrchestration
    LongTermRetrieval --> ResultOrchestration
    
    ResultOrchestration --> StructuredOutput
    StructuredOutput --> ContextCitation
    ContextCitation --> UserFeedback

    %% Styling
    classDef newFeature fill:#d4edda,stroke:#28a745,stroke-width:2px
    classDef memory fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    classDef observability fill:#d1ecf1,stroke:#17a2b8,stroke-width:2px
    
    class Layer4,Memory,ShortTerm,LongTerm,LongTermRetrieval,DataTools newFeature
    class Memory memory
```

---

## 支撑系统

```mermaid
flowchart LR
    subgraph KnowledgeBase["A. 知识与数据底座"]
        APIDocs["API 文档库<br/>本地 + 远程 Wiki"]
        ErrorDict["错误字典<br/>error_code 映射表"]
        SOPDocs["排查 SOP<br/>每个 task_type 的专家流程"]
        WikiIndex["远程 llm-wiki 索引<br/>1400+ 文档段"]
        DataSet["数据分析数据集 🆕<br/>静态 Excel (固定时间范围)"]
    end
    
    subgraph RiskControl["B. 规则与风控"]
        SecurityBoundary["安全边界<br/>appsecret 屏蔽<br/>范围限定<br/>Schema 必填项强制"]
        DataSourceLimit["数据源限制说明 🆕<br/>静态快照<br/>无法响应动态日期查询<br/>SOP: 用'数据集内'而非'最近'"]
        HumanGate["人工闸门<br/>凭证请求 → 转人工<br/>敏感信息 → 阻断"]
    end
    
    KnowledgeBase -.支撑.-> MainFlow[主流程]
    RiskControl -.保护.-> MainFlow
    
    classDef newFeature fill:#d4edda,stroke:#28a745,stroke-width:2px
    class DataSet,DataSourceLimit newFeature
```

---

## 可观测性系统（贯穿所有模块）

```mermaid
flowchart TB
    subgraph Observability["可观测性系统 🆕"]
        IntentTrace["意图识别 Trace<br/>Layer 1-4 得分 + 匹配路径"]
        FieldTrace["字段提取 Trace<br/>每个字段的规则 + 值"]
        ValidationTrace["校验 Trace<br/>status + missing + blocked reasons"]
        ToolTrace["工具执行 Trace<br/>name + input + status + output"]
        KnowledgeTrace["知识检索 Trace<br/>来源 + 数量 + 匹配路径"]
        ReActTrace["ReAct Trace 🆕<br/>Thought/Action/Observation<br/>每轮迭代"]
    end
    
    IntentTrace --> TracePanel["Trace 面板<br/>实时查看 + 调试"]
    FieldTrace --> TracePanel
    ValidationTrace --> TracePanel
    ToolTrace --> TracePanel
    KnowledgeTrace --> TracePanel
    ReActTrace --> TracePanel
    
    classDef observability fill:#d1ecf1,stroke:#17a2b8,stroke-width:2px
    class Observability,IntentTrace,FieldTrace,ValidationTrace,ToolTrace,KnowledgeTrace,ReActTrace,TracePanel observability
```

---

## 三大核心价值（架构图底部说明框）

### 💡 记忆系统：为什么不让 LLM 重问

**核心价值**：
- 自动继承已知字段（appid 提供一次，后续自动带入）
- 代码编排式记忆 vs Prompt 拼接：字段继承不消耗 token，更确定
- 长期记忆注入相似案例：让 LLM 学习历史解决方案

**实现原理**：
- 代码硬记忆 X、Y、Z（appid、error_code、...）并自动合并
- 历史对话存 localStorage（X, Y 已知），比 LLM 模糊上下文可靠
- 长期记忆 TF-IDF 检索 + 时间衰减，注入 Top 3 作为 few-shot

---

### ⚖️ Schema 校验：为什么不让 LLM 直接猜

**核心价值**：
- 用代码验证 vs LLM 猜测：工具需要字段时，代码判断（逻辑 + schema），LLM 判断容易出错
- 规则驱动 vs LLM 判断：代码逻辑比 LLM 更"可靠"，比 LLM 判断更便宜（0 token）
- Schema 必填项强制：防止 LLM 凭不完整信息硬答，提高回答质量

**实现原理**：
- 代码检查必填 X、Y（appid、error_code、timestamp 等）并对比 rule
- 缺失 → 追问，齐全 → 工具调用
- 15 步签名 SOP（参数顺序 → timestamp → 签名方法...）比让 LLM 先猜再验 prompt 更短

---

### 📚 Skill SOP: 为什么不让 LLM 现场发挥

**核心价值**：
- 把专家经验固化为 SOP 文档，保证回答质量一致
- SOP 文档 vs 零样本决策：固定的排查流程，不依赖 LLM 临场发挥
- 知识更新只需改 SOP，不用重新训练或调整 prompt

**实现原理**：
- 15 步签名排查 SOP（参数排序 → timestamp → 签名方法...）
- 注入 System Prompt，LLM 遵循 SOP 执行
- 数据分析 SOP：明确数据源限制，指导 LLM 正确表述时间范围

---

## 图例说明

🆕 = V2 新增功能
🔐 = 签名排查
📞 = 回调异常
❓ = 字段问答
📊 = 数据分析
🚀 = 新接入
⚠️ = 人工闸门 / 数据限制

**颜色标注**：
- 🟢 绿色：新增功能（记忆系统、ReAct、数据分析增强）
- 🟡 黄色：记忆系统相关
- 🔵 蓝色：可观测性系统
