# API 智能客服 Agent 交互架构图 V2

**目标**：将 API 接入八股问答排查 SOP 固定为 Skills，通过 LLM 驱动能力理解、后续工具调用

---

## 核心流程（5 大模块 + 2 大支撑系统）

### 模块 1: 用户/行业输入

**输入形式**：
- 描述 API 接入问题（签名失败、回调异常、错误码等）
- 提供关键字段（appid、错误码、接口路径等）
- 查询数据分析（单量、撤单、渠道对比）

**提取字段**：
- appid、error_code、api_path、request_time
- callback_url、order_id、trigger_action
- analysis_dimension、analysis_scope（数据分析新增）

**可选敏感信息自查**（appsecret → 拒绝）

---

### 模块 2: 安全 + 意图识别

#### 2.1 安全检测 + 范围边界

- **敏感信息检测**（appsecret 标记）
- **范围限定**（非 API 问题 → 拒绝）
- **语义过滤**（内容 + LLM 判定）

#### 2.2 三层混合意图识别（4 层架构）

**Layer 1: Rule-First（确定性）**
- 关键词权重匹配
- 得分 ≥ 3 → 识别成功
- Cost: 0 tokens, <10ms
- 示例：`签名 + SIGN_INVALID` → `signature_debug`

**Layer 2: Vector Fallback（语义）**
- Token overlap 相似度（本地计算，非真实 embedding）
- 相似度 ≥ 0.42 → 识别成功
- Cost: 0 tokens
- 示例：`验签不通过` → `signature_debug`

**Layer 3: LLM Hints（兜底）**
- Pattern 匹配启发式规则
- 模拟 LLM 归并（当前未真实调用 LLM）
- Cost: 0 tokens（simulated）
- 示例：`怎么开始接入` → `api_onboarding`

**Layer 4: ReAct Loop（新增 - 救援）**
- 触发条件：`out_of_scope && strongBusinessSignal`
- LLM 自主决策 Thought → Action → Observation
- 最多 5 轮迭代，防重复调用
- Cost: 3-5 LLM calls (~5-10k tokens)
- 触发率：~5-10%

**输出**：`task_type` + `字段草稿` + `置信度`

---

### 模块 3: LLM 管理路由

#### 3.1 Schema 校验

**按 task_type 检查必填字段**：
- `signature_debug`: 需要 appid、error_code、api_path、raw_sign_string、request_time
- `callback_debug`: 需要 callback_url、order_id、trigger_action、request_time
- `api_field_qa`: 需要 field_name
- `volume_analysis`: 需要 analysis_dimension、**analysis_scope**（新增，防止模糊查询）
- `credential_request`: 需要 appid

**校验结果**：
- `executable` → 字段齐全，进入 Skill 路由
- `needs_clarification` → 缺失字段，精准追问
- `blocked` → 安全边界触发

**追问策略**（数据分析特殊处理）：
- 通用：`缺少：${missing_fields}`
- 数据分析：`你想看「单量」的哪个细分维度？1️⃣ 时间趋势 2️⃣ 渠道对比 3️⃣ 游戏维度 4️⃣ 全部 ⚠️ 数据说明：静态 Excel 数据集，无法拉取指定日期`

#### 3.2 记忆系统（新增）

**短期记忆（Session Memory，24h TTL）**：
- **字段记忆**：跨轮累积字段（appid 一次提供，后续自动继承）
- **对话上下文**：最近 10 轮原始对话 + 压缩摘要（>10 轮时启动 Layer 1/2 压缩）
- **会话状态**：activeTask（task_type、status、fields）

**长期记忆（Long-term Memory，无 TTL）**：
- **存储**：localStorage，最多 100 条历史任务
- **检索算法**：TF-IDF + 时间衰减（30 天半衰期）
- **注入方式**：Top 3 相似案例注入 System Prompt 作为 few-shot
- **触发**：每次 `executable` turn 完成后写入

#### 3.3 Skill 路由

**按 task_type 命中对应业务 SOP**：
- `signature_debug` → 签名失败排查 Skill（15 步 SOP）
- `callback_debug` → 回调异常排查 Skill
- `api_field_qa` → API 字段问答 Skill
- `volume_analysis` → 数据分析 Skill（新增 SOP：静态数据源限制说明）
- `api_onboarding` → 新 API 接入 Skill
- `credential_request` → 人工审查闸门 Skill

**异常处理**：
- `unknown` → 走 ReAct Layer 4 或提示重新描述
- `out_of_scope` → 检查 strongBusinessSignal，决定是否启动 ReAct

#### 3.4 结果编排

**文档 + 工具结果 + 上下文 → 生成最终答案**：
- 从多源数据（工具、知识库、长期记忆）综合
- 一次性调用 LLM 生成自然语言回复

---

### 模块 4: 工具 + 检索执行

#### 4.1 Skills / SOP 能力库

**固定 Skills**（预定义能力单元）：
- ✅ 签名排查 Skill（参数排序、编码、timestamp）
- ✅ 回调异常排查 Skill
- ✅ API 字段问答 Skill
- ✅ 数据分析 Skill（撤单/单量/渠道）
- ⚠️ 人工审查闸门 Skill（凭证请求 → 拒绝自动处理）
- 🆕 新 API 接入引导 Skill
- 🔧 异常处理 / 数学校验闸 Skill

**非 SOP，语义分层**：
- 每个 Skill 有独立文档（Markdown SOP）
- SOP 文档 vs 零样本决策：固定专家经验，不依赖 LLM 临场发挥

#### 4.2 工具调用（确定性验证工具）

**签名工具**：
- `check_signature_order`：参数排序检查（ASCII 升序）
- `validate_timestamp`：timestamp 格式 + 有效期
- `check_encoding`：UTF-8 编码检查

**数据分析工具**（基于静态 Excel）：
- `analyze_time_trend`：时间趋势分析
- `analyze_channel_comparison`：渠道对比
- `analyze_game_distribution`：游戏维度分布
- **限制说明**：静态快照，无法查询指定日期

**工具执行后结果回传 LLM 解读生成**

#### 4.3 本地知识包检索

**内容**：FAQ + 错误码表 + SOP 文档
**检索方式**：
- 优先级：精确匹配 > 路径段匹配 > 模糊匹配
- 示例：`/api/platformXYZ/hao/search` → 拆分路径段 `platformXYZ`, `hao`, `search` 独立匹配

#### 4.4 远程 llm-wiki 索引

**规模**：1400+ 文档段
**检索**：基于 GitHub Wiki JSON 索引（预构建）

#### 4.5 联邦搜索机制（cascade）

**搜索优先级**：
1. 本地知识包（FAQ + SOP）
2. GitHub llm-wiki（远程索引）
3. 安全边界检查（敏感内容屏蔽）

**检索增强生成（RAG）**：
- 检索结果注入 System Prompt
- 引用来源标注（避免编造）

#### 4.6 长期记忆检索（新增）

**检索时机**：每次 `executable` turn
**注入方式**：Top 3 相似历史案例 → System Prompt
**格式**：
```
## 历史相似案例参考
1. signature_debug (2026-06-01)
   字段: {"appid": "xxx", "error_code": "SIGN_INVALID"}
   解决方案: 参数未按 ASCII 升序排列
```

---

### 模块 5: 结果反馈用户

#### 5.1 结构化组织后（定向到问 + 修复建议）

**输出格式**：
- 问题定位：根据工具 + 文档结果判断
- 修复建议：具体操作步骤
- 引用来源：文档链接 + 相似案例

#### 5.2 引用 Context 路径（有据可查）

**引用类型**：
- 文档来源：`[FAQ] xxxx` 或 `[Wiki] xxxx`
- 工具结果：`check_signature_order: fail - 参数顺序错误`
- 历史案例：`历史案例 #123: 相同错误码，解决方案为...`

#### 5.3 获取 Session 反馈（可暂缓）

**当前状态**：未实现
**未来扩展**：用户反馈（有用/无用）→ 优化长期记忆权重

---

## 支撑系统

### A. 知识与数据底座

**组成**：
- API 文档库（本地 + 远程 Wiki）
- 错误字典（error_code 映射表）
- 排查 SOP（每个 task_type 的专家流程）
- 远程 llm-wiki 索引（1400+ 文档段）
- 数据分析数据集（静态 Excel，固定时间范围）

**特点**：
- 结构化存储 + 版本控制
- 增量更新 + 索引优化

### B. 规则与风控

**安全边界**：
- appsecret 屏蔽（不进入 LLM 上下文）
- 范围限定（非 API 问题 → 拒绝）
- Schema 必填项强制（防止 LLM 硬猜）

**数据源限制说明**（新增）：
- 数据分析基于静态 Excel 快照
- 无法响应"最近 7 天"、"昨天"等动态时间查询
- SOP 明确告知：用"数据集内"而非"最近"

**人工闸门**：
- 凭证请求 → 转人工
- 敏感信息 → 阻断

---

## 可观测性系统（新增）

**贯穿所有模块的 Trace**：

### 意图识别 Trace
- Layer 1: Rule 得分（命中关键词 + 权重）
- Layer 2: Vector 相似度（top 3 examples + score）
- Layer 3: LLM Hints 匹配的 pattern
- Layer 4: ReAct 循环步骤（Thought/Action/Observation）

### 字段提取 Trace
- 每个字段的匹配规则 + 提取值
- 示例：`appid: 匹配 appid=xxx → app_001`

### 校验 Trace
- Status: executable / needs_clarification / blocked
- Missing fields: 缺失字段列表
- Blocked reasons: 安全边界触发原因

### 工具执行 Trace
- 工具名称 + 输入参数 + 执行状态 + 输出结果
- 示例：`check_signature_order: fail - 当前顺序错误`

### 知识检索 Trace
- 检索来源（local / remote）
- 检索到的文档数量
- 匹配路径（exact / fuzzy / segment）

### ReAct Trace（新增）
- 每轮迭代：Thought（推理）、Action（工具）、Observation（结果）
- Final Answer 或 Max Iterations

**展示位置**：可观测性 Tab（实时 trace 查看）

---

## 底部说明框（三大核心价值）

### 💡 记忆系统：为什么不让 LLM 重问

**核心价值**：
- 自动继承已知字段（appid 提供一次，后续自动带入）
- 代码编排式记忆 vs Prompt 拼接：字段继承不消耗 token，更确定
- 长期记忆注入相似案例：让 LLM 学习历史解决方案

**实现原理**：
- 代码硬记忆 X、Y、Z（appid、error_code、...）并自动合并
- 历史对话存 localStorage（X, Y 已知），比 LLM 模糊上下文可靠
- 长期记忆 TF-IDF 检索 + 时间衰减，注入 Top 3 作为 few-shot

### ⚖️ Schema 校验：为什么不让 LLM 直接猜

**核心价值**：
- 用代码验证 vs LLM 猜测：工具需要字段时，代码判断（逻辑 + schema），LLM 判断容易出错
- 规则驱动 vs LLM 判断：代码逻辑比 LLM 更"可靠"，比 LLM 判断更便宜（0 token）
- Schema 必填项强制：防止 LLM 凭不完整信息硬答，提高回答质量

**实现原理**：
- 代码检查必填 X、Y（appid、error_code、timestamp 等）并对比 rule
- 缺失 → 追问，齐全 → 工具调用
- 15 步签名 SOP（参数顺序 → timestamp → 签名方法...）比让 LLM 先猜再验 prompt 更短

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

## 新增能力总结（相比原架构图）

1. **记忆系统**：短期（字段 + 对话上下文）+ 长期（相似案例检索）
2. **ReAct Layer 4**：LLM 自主循环兜底，处理 out_of_scope + business signal
3. **数据分析追问策略**：analysis_scope 必填，防止模糊查询
4. **数据源限制说明**：静态 Excel，明确告知无法查询指定日期
5. **可观测性系统**：完整 trace（意图/字段/校验/工具/ReAct）
6. **三层混合意图识别细节**：Rule → Vector → LLM Hints → ReAct（4 层）
