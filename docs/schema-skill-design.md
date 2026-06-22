# Schema 校验与 Skill 路由设计详解

## 问题 1: Schema 校验是怎么设计的？为什么要设计？

### 什么是 Schema 校验？

**Schema 校验**是指根据任务类型（task_type），检查必填字段是否齐全的过程。

**代码位置**：`web/index.html` 行 3238-3244 + 3516-3531

```javascript
// 每种任务类型的必填字段定义
const requiredFields = {
  signature_debug: ["api_path", "appid", "raw_sign_string", "error_code", "request_time"],
  callback_debug: ["callback_url", "order_id", "trigger_action", "request_time"],
  api_field_qa: ["field_name"],
  credential_request: ["appid"],
  unknown: []
};

// 校验逻辑
function validate(draft) {
  // 1. 安全边界检查（最高优先级）
  if (draft.security_flags.includes("contains_appsecret")) {
    return {
      status: "blocked",
      missing_fields: [],
      blocked_reasons: ["输入中包含 appsecret，不能进入普通模型上下文或普通日志。"]
    };
  }
  
  // 2. 任务类型未知
  if (draft.task_type === "unknown") {
    return { 
      status: "needs_clarification", 
      missing_fields: ["task_type"], 
      blocked_reasons: [] 
    };
  }
  
  // 3. 检查必填字段
  const missing = requiredFields[draft.task_type].filter((field) => !draft.fields[field]);
  
  return missing.length
    ? { status: "needs_clarification", missing_fields: missing, blocked_reasons: [] }
    : { status: "executable", missing_fields: [], blocked_reasons: [] };
}
```

---

### 为什么要设计 Schema 校验？

#### **原因 1：确保工具可执行**

每个排查工具（Skill）都有**前置条件**，缺少必填字段会导致工具无法执行。

**示例：签名排查工具**
```
签名失败排查需要：
  ✅ api_path       - 定位是哪个接口
  ✅ appid          - 确认调用方身份
  ✅ raw_sign_string - 验证签名计算过程
  ✅ error_code     - 确认具体错误类型
  ✅ request_time   - 定位时间范围，排查时效性问题

缺少任意一个 → 工具无法给出准确结论
```

**没有 Schema 校验的后果**：
```
用户: "你们接口签名失败"
Agent: "我来排查签名问题..."
       → 调用签名工具
       → 缺少 appid、签名前字符串
       → 工具返回"信息不足，无法排查"
       → Agent: "抱歉，需要更多信息"

用户: "appid=xxx"
Agent: "我继续排查..."
       → 还是缺少签名前字符串
       → 又一次失败

用户: "签名前字符串是 ..."
Agent: "我再排查..."
       → 终于可以执行

❌ 问题：重复尝试，浪费对话轮次
```

**有 Schema 校验的效果**：
```
用户: "你们接口签名失败"
Agent: "我已识别为「签名失败排查」，但还缺少阻塞信息：
       接口路径、appid、签名前原始字符串、错误码、请求时间。
       请补充这些信息后我再继续排查。"

用户: "appid=xxx，错误码=SIGN_INVALID，接口是 /open/order/create，
       签名前字符串是 order_id=O1001&timestamp=xxx，
       请求时间 2026-06-15 10:20:00"
       
Agent: "收到，开始排查..."
       → 字段齐全
       → 一次性调用工具
       → 给出准确结论

✅ 优势：一次性收集完整信息，避免多轮来回
```

---

#### **原因 2：提升用户体验（精准追问）**

**精准追问 vs 盲目追问**：

**❌ 没有 Schema 校验（盲目追问）**：
```
Agent: "请提供更多信息"  ← 用户不知道要提供什么
用户: "还要什么？"
Agent: "任何相关信息"     ← 太宽泛，用户困惑
```

**✅ 有 Schema 校验（精准追问）**：
```
Agent: "还缺少阻塞信息：appid、错误码、签名前字符串"
用户: 知道要补充什么 → 直接提供
```

---

#### **原因 3：防止误执行（安全边界）**

Schema 校验不只是检查"缺什么"，还检查"是否允许执行"：

```javascript
// 安全边界检查
if (draft.security_flags.includes("contains_appsecret")) {
  return {
    status: "blocked",  // ← 阻断执行
    blocked_reasons: ["输入中包含 appsecret，不能进入普通模型上下文"]
  };
}
```

**示例**：
```
用户: "appid=xxx，appsecret=sk_1234567890abcdef"
Agent: "❌ 这个请求触发了安全边界：
       输入中包含 appsecret，不能进入普通模型上下文或普通日志。"

✅ 防止敏感信息泄漏到日志或模型上下文
```

---

#### **原因 4：多轮对话记忆管理**

Schema 校验配合记忆系统，实现**增量收集**：

```
Turn 1: "签名失败"
  → 缺少: ["api_path", "appid", "raw_sign_string", "error_code", "request_time"]
  → 追问: "请补充这些信息"

Turn 2: "appid=xxx，错误码=SIGN_INVALID"
  → 记忆合并: { appid: "xxx", error_code: "SIGN_INVALID" }
  → 还缺少: ["api_path", "raw_sign_string", "request_time"]
  → 追问: "还缺少接口路径、签名前字符串、请求时间"

Turn 3: "接口是 /open/order/create，签名前字符串=xxx，时间=2026-06-15 10:20"
  → 记忆合并: 所有字段齐全
  → 校验通过: status = "executable"
  → 调用工具
```

**没有 Schema 校验的后果**：
- Agent 不知道何时停止追问
- 可能在字段不全时就尝试调用工具（失败）
- 可能追问用户已提供的字段（体验差）

---

### Schema 校验的状态机

```
用户输入
  ↓
[意图识别] → task_type
  ↓
[字段提取] → fields
  ↓
[Schema 校验]
  ├─ contains_appsecret → status = "blocked" (安全阻断)
  ├─ task_type = "unknown" → status = "needs_clarification" (任务不明)
  ├─ 缺少必填字段 → status = "needs_clarification" (缺字段)
  └─ 字段齐全 → status = "executable" (可执行)
  ↓
[执行决策]
  ├─ blocked → 拒绝执行，提示安全边界
  ├─ needs_clarification → 追问缺失信息
  └─ executable → 调用 Skill 工具
```

---

## 问题 2: Skill 路由是怎么设计的？

### 什么是 Skill 路由？

**Skill 路由**是指根据识别出的任务类型（task_type），找到对应的排查工具（Skill）并调用。

**代码位置**：`web/index.html` 行 3259-3265

```javascript
// Skill 路由表
const skills = {
  signature_debug: "signature_debug/SKILL.md",     // 签名排查 Skill
  callback_debug: "callback_debug/SKILL.md",       // 回调排查 Skill
  api_field_qa: "api_field_qa/SKILL.md",          // 字段问答 Skill
  credential_request: "human_review_gate",         // 人工审核闸门
  unknown: null                                    // 未识别任务
};

// 路由逻辑（简化版）
function routeToSkill(task_type) {
  const skillPath = skills[task_type];
  
  if (!skillPath) {
    return { type: "no_skill", message: "未识别的任务类型" };
  }
  
  if (skillPath === "human_review_gate") {
    return { type: "human_gate", message: "需要人工审核" };
  }
  
  // 加载 Skill 定义
  const skill = loadSkillDefinition(skillPath);
  return { type: "skill", skill };
}
```

---

### Skill 路由的设计原理

#### **1. 一对一映射（task_type → Skill）**

```
task_type               →  Skill 文件
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
signature_debug         →  signature_debug/SKILL.md
callback_debug          →  callback_debug/SKILL.md
api_field_qa            →  api_field_qa/SKILL.md
credential_request      →  human_review_gate（特殊：人工闸门）
unknown                 →  null（无法路由）
```

**设计优点**：
- ✅ **简单直观**：一个任务类型对应一个 Skill
- ✅ **易于扩展**：新增任务类型只需添加一行映射
- ✅ **便于维护**：修改某个 Skill 不影响其他

---

#### **2. Skill 文件结构（SKILL.md）**

每个 Skill 是一个 Markdown 文件，包含：

**示例：signature_debug/SKILL.md**
```markdown
# 签名失败排查 Skill

## 适用场景
第三方反馈签名失败、验签失败、SIGN_INVALID 错误。

## 必要信息
- 接口路径
- appid
- 签名前原始字符串
- 错误码
- 请求时间

## 排查 SOP
1. 检查参数是否按字典序排序。
2. 检查 timestamp 是否在有效期内（±5分钟）。
3. 检查签名算法是否正确（HMAC-SHA256）。
4. 检查字符编码是否为 UTF-8。
5. 对比签名前字符串与文档示例。
6. 如果仍失败，检查 appid 对应的 appsecret 是否正确。

## 常见错误
- 参数未排序
- 包含了不应该参与签名的字段（如 sign 本身）
- 时间戳格式错误
- 字符编码不一致（GBK vs UTF-8）
```

**Skill 文件的作用**：
1. **文档检索**：LLM 可以读取 Skill 内容作为上下文
2. **SOP 标准化**：确保每次排查遵循相同的步骤
3. **知识沉淀**：历史经验固化为可复用的文档

---

#### **3. 路由决策流程**

```
[意图识别]
  ↓
task_type = "signature_debug"
  ↓
[Schema 校验]
  ↓
status = "executable"（字段齐全）
  ↓
[Skill 路由]
  ↓
skills["signature_debug"] → "signature_debug/SKILL.md"
  ↓
[加载 Skill 定义]
  ↓
读取 SKILL.md 内容 → 作为 System Prompt 的一部分
  ↓
[调用 LLM]
  ↓
LLM 根据 Skill SOP + 用户提供的字段 → 生成排查结论
```

---

#### **4. 特殊路由：人工闸门**

```javascript
credential_request: "human_review_gate"  // 不是 Skill 文件，是特殊标记
```

**触发场景**：
```
用户: "我想要 appid 和 appsecret"
  ↓
识别为: credential_request
  ↓
路由到: human_review_gate
  ↓
拒绝自动处理，提示转人工
```

**原因**：
- 凭证申请涉及权限和安全审核
- 不能由 Agent 自动处理
- 需要人工介入验证身份

---

### Skill 路由的优势

#### **优势 1：解耦意图识别与工具执行**

```
[意图识别层]          [工具执行层]
    ↓                     ↓
task_type  ────→ skills[task_type] ────→ Skill 文件
    ↓                     ↓
简单映射              加载 SOP
    ↓                     ↓
    ↓                 调用 LLM
```

**好处**：
- 修改 Skill 内容不影响意图识别
- 新增 Skill 只需添加文件和路由映射

---

#### **优势 2：支持动态扩展**

```javascript
// 新增一个 Skill 只需两步：

// 1. 创建 Skill 文件
// skills/order_query/SKILL.md

// 2. 添加路由映射
const skills = {
  signature_debug: "signature_debug/SKILL.md",
  callback_debug: "callback_debug/SKILL.md",
  order_query: "order_query/SKILL.md",  // ← 新增
  // ...
};

// 3. 添加必填字段定义（如果需要）
const requiredFields = {
  signature_debug: ["api_path", "appid", "raw_sign_string", "error_code", "request_time"],
  callback_debug: ["callback_url", "order_id", "trigger_action", "request_time"],
  order_query: ["order_id"],  // ← 新增
  // ...
};
```

---

#### **优势 3：知识可复用**

Skill 文件可以被多个地方使用：
1. **LLM 上下文**：作为 System Prompt 的一部分
2. **文档检索**：用户可以直接查看 Skill 文档
3. **人工参考**：运营同学可以参考 Skill 来处理问题
4. **培训材料**：新人培训时学习标准 SOP

---

## 问题 3: Skill 能力库目前是怎么来的？

### 当前 Skill 的来源

**代码位置**：`web/index.html` 行 3259-3265

```javascript
const skills = {
  signature_debug: "signature_debug/SKILL.md",      // 手工编写
  callback_debug: "callback_debug/SKILL.md",        // 手工编写
  api_field_qa: "api_field_qa/SKILL.md",           // 手工编写
  credential_request: "human_review_gate",          // 手工定义
  unknown: null
};
```

**来源 1：历史 SOP 文档**
```
企业内部的排查手册 / 运维文档 / 常见问题手册
  ↓ 提炼、结构化
signature_debug/SKILL.md
callback_debug/SKILL.md
```

**来源 2：专家经验沉淀**
```
技术支持同学的排查经验
  ↓ 总结、标准化
api_field_qa/SKILL.md
```

**来源 3：错误码手册**
```
错误码文档
  ↓ 关联到具体排查步骤
集成到 Skill 的"常见错误"章节
```

---

### Skill 文件的实际内容（已有）

#### **1. signature_debug/SKILL.md（签名排查）**

**示例内容**：
```markdown
# 签名失败排查 Skill

## 适用场景
第三方反馈签名失败、验签失败、SIGN_INVALID 错误。

## 必要信息
- 接口路径
- appid
- 签名前原始字符串
- 错误码
- 请求时间

## 排查 SOP
1. 检查参数是否按字典序排序。
2. 检查 timestamp 是否在有效期内（±5分钟）。
3. 检查签名算法是否正确（HMAC-SHA256）。
4. 检查字符编码是否为 UTF-8。
5. 对比签名前字符串与文档示例。

## 常见错误
- 参数未排序 → "请确认参数按字典序排序"
- 时间戳过期 → "timestamp 超出有效范围（±5分钟）"
- 字符编码错误 → "请使用 UTF-8 编码"
```

---

#### **2. callback_debug/SKILL.md（回调排查）**

**示例内容**：
```markdown
# 回调异常排查 Skill

## 适用场景
第三方反馈没有收到回调、回调延迟、回调超时或回调状态异常。

## 必要信息
- 回调地址
- 订单号
- 触发动作
- 回调时间
- 服务端日志

## 排查 SOP
1. 确认回调地址是否为可访问的 HTTPS 地址。
2. 检查订单是否真的触发了回调动作。
3. 查询服务端是否发起过回调。
4. 检查第三方响应状态码和响应体。
5. 如果第三方未返回 2xx，提示第三方修复后等待重试或人工补偿。
```

---

#### **3. api_field_qa/SKILL.md（字段问答）**

**示例内容**：
```markdown
# API 字段问答 Skill

## 适用场景
第三方询问某个字段的含义、枚举值、使用方法。

## 必要信息
- 字段名

## 排查 SOP
1. 在 API 文档中搜索该字段。
2. 返回字段定义、类型、枚举值（如果有）。
3. 如果没有找到，提示可能是拼写错误或该字段不存在。
```

---

### Skill 的维护流程

```
[发现新问题]
  ↓
"用户经常问某个新类型的问题"
  ↓
[编写 Skill]
  ↓
1. 创建 skills/<task_name>/SKILL.md
2. 定义适用场景、必要信息、排查 SOP
  ↓
[添加路由]
  ↓
在 skills 对象中添加映射
  ↓
[添加 Schema]
  ↓
在 requiredFields 中定义必填字段
  ↓
[添加意图识别规则]
  ↓
在 detectTask() 中添加关键词匹配
  ↓
[测试]
  ↓
输入测试问题 → 验证路由正确 → 验证 Schema 校验生效
  ↓
[上线]
```

---

### Skill 的未来扩展方向

#### **方向 1：从知识库自动生成**

```
[llm-wiki 文档]
  ↓ 自动提取
[Skill 草稿]
  ↓ 人工审核
[正式 Skill]
```

**工具**：
- 使用 LLM 分析文档，提取排查步骤
- 自动生成 Skill 模板
- 人工补充细节

---

#### **方向 2：从历史对话学习**

```
[Agent 对话日志]
  ↓ 分析
"某类问题经常出现"
  ↓ 提炼
[新 Skill]
```

**示例**：
```
分析发现：30% 的对话涉及"接口超时"
  ↓
提炼 SOP：
  1. 检查网络连通性
  2. 检查服务端负载
  3. 检查请求参数大小
  ↓
生成 Skill: timeout_debug/SKILL.md
```

---

#### **方向 3：动态 Skill 组合**

**当前**：一个 task_type 对应一个 Skill

**未来**：一个任务可能需要多个 Skill 协作

```
用户: "签名失败，而且回调也没收到"
  ↓
识别为: 复合任务
  ↓
路由到:
  - signature_debug Skill（排查签名）
  - callback_debug Skill（排查回调）
  ↓
并行执行 → 合并结果
```

---

## 总结

### Schema 校验

**是什么**：
- 检查必填字段是否齐全
- 检查是否触发安全边界

**为什么**：
1. 确保工具可执行（避免"信息不足"错误）
2. 提升用户体验（精准追问）
3. 防止误执行（安全阻断）
4. 多轮对话记忆管理（增量收集）

**怎么做**：
```javascript
requiredFields[task_type] → 必填字段列表
  ↓
validate(draft) → status (blocked | needs_clarification | executable)
  ↓
clarify(draft, validation) → 追问消息
```

---

### Skill 路由

**是什么**：
- 根据 task_type 找到对应的 Skill 文件
- 加载 Skill 定义（SOP）作为 LLM 上下文

**为什么**：
1. 解耦意图识别与工具执行
2. 支持动态扩展（新增 Skill 只需添加文件）
3. 知识可复用（文档、培训、人工参考）

**怎么做**：
```javascript
skills[task_type] → Skill 文件路径
  ↓
loadSkillDefinition(path) → Skill 内容
  ↓
作为 System Prompt → 调用 LLM
```

---

### Skill 能力库

**来源**：
1. 历史 SOP 文档（企业内部手册）
2. 专家经验沉淀（技术支持总结）
3. 错误码手册（关联排查步骤）

**当前 Skill**：
- `signature_debug` - 签名失败排查
- `callback_debug` - 回调异常排查
- `api_field_qa` - API 字段问答
- `credential_request` - 人工审核闸门

**维护流程**：
```
发现新问题 → 编写 Skill → 添加路由 → 添加 Schema → 测试 → 上线
```

**未来方向**：
- 从知识库自动生成
- 从历史对话学习
- 动态 Skill 组合

---

## 可视化架构图

```
┌────────────────────────────────────────────────┐
│              用户输入                           │
│        "你们接口签名失败，appid=xxx"             │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│         意图识别（detectTask）                  │
│  关键词匹配 → task_type = "signature_debug"     │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│         字段提取（extractTask）                 │
│  正则提取 → fields = { appid: "xxx" }          │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│         Schema 校验（validate）                 │
│  requiredFields["signature_debug"] 对比 fields  │
│  缺少: ["api_path", "raw_sign_string", ...]    │
│  status = "needs_clarification"                │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│         追问（clarify）                         │
│  "还缺少：接口路径、签名前字符串、错误码..."     │
└────────────────┬───────────────────────────────┘
                 ↓
    用户补充信息（多轮对话）
                 ↓
┌────────────────────────────────────────────────┐
│         Schema 校验通过                         │
│  status = "executable"                         │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│         Skill 路由（routeToSkill）              │
│  skills["signature_debug"]                     │
│  → "signature_debug/SKILL.md"                  │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│         加载 Skill 定义                         │
│  读取 SKILL.md → 排查 SOP                       │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│         调用 LLM                                │
│  System Prompt = Skill SOP + 用户字段          │
│  → 生成排查结论                                 │
└────────────────────────────────────────────────┘
```

---

需要我进一步解释某个部分，或者帮你实现某个新的 Skill 吗？