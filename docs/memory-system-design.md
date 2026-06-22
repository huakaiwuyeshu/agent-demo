# Agent Demo 记忆系统设计文档

## 设计理念（基于 Open Design）

### 核心原则
1. **Agent-Native**: 记忆系统服务于 Agent 工作流（识别 → 收集 → 决策 → 执行）
2. **明确边界**: 精确定义短期记忆 vs 长期记忆的职责和时效
3. **Local-First**: 优先本地存储（localStorage），无云依赖
4. **渐进式披露**: 复杂状态隐藏，只在需要时展示

---

## 术语定义（Domain Language）

### **Session（会话）**
用户打开 Web Demo 到关闭页面（或主动重置）的完整周期。
- 持久化：localStorage
- 时效：刷新页面后恢复，手动重置或超过 24 小时自动清空
- 唯一标识：`sessionId`（格式：`api-demo-${timestamp}`）

_Avoid_: conversation, workspace, context

---

### **Turn（对话轮次）**
用户提交一次输入及 Agent 响应的完整交互。
- 持久化：Session 内存储
- 时效：Session 内保留最近 20 轮（UI 显示最近 5 轮）
- 结构：`{ index, text, intent, status, missing, fields, timestamp }`

_Avoid_: message, round, step

---

### **Task Context（任务上下文）**
当前正在处理的任务的状态快照。
- 持久化：Session 内存储
- 时效：任务完成或强烈新意图时覆盖
- 结构：`{ id, task_type, status, pending_fields, fields, updated_at }`

_Avoid_: active task, current job

---

### **Field Memory（字段记忆）**
从对话中提取并持久化的业务字段。
- 持久化：Session 内存储
- 时效：Session 内累积（字段只增不减，除非手动删除）
- 结构：`{ [field_name]: value }`

_Avoid_: collected data, user input cache

---

### **Short-term Memory（短期记忆）**
Session 内的所有记忆（Turns + Task Context + Field Memory）。
- 持久化：localStorage
- 时效：小时级（一次排查任务通常 5-10 分钟）
- 生命周期：Session 开始 → Session 结束

_Avoid_: temporary memory, session cache

---

### **Long-term Memory（长期记忆）**
⚠️ **未实现**。跨 Session 的用户画像、历史任务、业务上下文。
- 持久化：数据库 + 向量库（假设）
- 时效：天/周/月
- 生命周期：用户注册 → 用户注销

_Avoid_: permanent memory, user profile

---

## 关系定义

- 一个 **Session** 包含多个 **Turn**（最多 20 个）
- 一个 **Session** 有零个或一个 **Task Context**
- 一个 **Task Context** 包含多个 **Field Memory** 条目
- **Short-term Memory** = Session + Turns + Task Context + Field Memory
- **Long-term Memory** 独立于 **Session**，跨会话存在（未实现）

---

## 短期记忆系统架构（已实现）

### 数据结构

```javascript
// localStorage key: 'agent_demo_session'
{
  sessionId: "api-demo-lb3k9x",
  createdAt: 1718937600000,
  lastActiveAt: 1718940000000,
  
  turns: [  // 最近 20 轮
    {
      index: 1,
      text: "你们接口签名失败",
      intent: "signature_debug",
      status: "waiting_for_user",
      missing: ["appid", "error_code"],
      fields: {},
      timestamp: 1718937610000
    },
    {
      index: 2,
      text: "appid=app_001，错误码=SIGN_INVALID",
      intent: "signature_debug",
      status: "ready_with_evidence",
      missing: [],
      fields: { appid: "app_001", error_code: "SIGN_INVALID" },
      timestamp: 1718937650000
    }
  ],
  
  taskContext: {
    id: "task-xyz",
    task_type: "signature_debug",
    status: "ready_with_evidence",  // waiting_for_user | ready_* | blocked | rejected
    pending_fields: [],
    fields: {
      appid: "app_001",
      error_code: "SIGN_INVALID",
      raw_sign_string: "order_id=O1001&timestamp=xxx"
    },
    updated_at: 1718937650000
  },
  
  fieldMemory: {  // 累积的字段（跨任务保留，但实际上每次新任务会清空）
    appid: "app_001",
    error_code: "SIGN_INVALID",
    raw_sign_string: "order_id=O1001&timestamp=xxx"
  },
  
  metadata: {
    last_intent: "signature_debug",
    last_validation: "executable",
    last_route: "local_package",
    total_turns: 2
  }
}
```

---

### 核心函数

#### **1. applyConversationContext(draft)**
**职责**：判断是否使用上下文，合并历史字段

```javascript
// 不使用上下文的情况：
// 1. 无活跃任务
// 2. 强烈新意图（置信度 >= 0.72 且任务类型不同）
// 3. 不像补充信息（没有字段提取，也不是追问语气）

// 使用上下文的情况：
// 1. 活跃任务在等待补充
// 2. 本轮是同一任务类型 OR 看起来像补充信息
// 3. 继承历史字段（fieldMemory）
```

#### **2. buildSessionSnapshot(draft, validation, docs)**
**职责**：构建当前会话状态快照

```javascript
// 计算任务状态：
// - rejected: 范围外输入
// - blocked: 触发安全边界
// - waiting_for_user: 缺少必填字段
// - ready_with_evidence: 字段齐全 + 检索到文档
// - ready_without_evidence: 字段齐全但无文档

// 合并字段：
// mergedFields = fieldMemory（历史）+ draft.fields（本轮）
```

#### **3. commitConversationTurn(message, run)**
**职责**：提交对话轮次到历史

```javascript
// 1. 创建 Turn 记录
// 2. 追加到 turns 数组（最多保留 20 轮）
// 3. 更新 fieldMemory
// 4. 更新 taskContext
// 5. 持久化到 localStorage
```

#### **4. loadSession() / saveSession()**
**职责**：从 localStorage 加载/保存会话

```javascript
function loadSession() {
  const saved = localStorage.getItem('agent_demo_session');
  if (!saved) return null;
  
  const session = JSON.parse(saved);
  
  // 检查时效（24 小时）
  if (Date.now() - session.lastActiveAt > 24 * 60 * 60 * 1000) {
    localStorage.removeItem('agent_demo_session');
    return null;
  }
  
  return session;
}

function saveSession() {
  const session = {
    sessionId: state.conversation.sessionId,
    createdAt: state.conversation.createdAt,
    lastActiveAt: Date.now(),
    turns: state.conversation.turns,
    taskContext: state.conversation.activeTask,
    fieldMemory: state.conversation.memory.fields,
    metadata: {
      last_intent: state.conversation.memory.last_intent,
      last_validation: state.conversation.memory.last_validation,
      last_route: state.conversation.memory.last_route,
      total_turns: state.conversation.turns.length
    }
  };
  
  localStorage.setItem('agent_demo_session', JSON.stringify(session));
}
```

---

## 长期记忆系统架构（未实现）

### 数据结构（假设）

```javascript
// 数据库表：user_profiles
{
  userId: "user-12345",
  appid: "app_merchant_001",
  merchantName: "测试商户",
  preferences: {
    responseStyle: "detailed",  // detailed | concise
    language: "zh-CN",
    timezone: "Asia/Shanghai"
  },
  businessContext: {
    environment: "production",
    apiList: ["/open/order/create", "/open/order/query"],
    whitelistedIps: ["192.168.1.100"],
    techStack: ["Java", "Spring Boot"]
  },
  createdAt: 1718937600000,
  updatedAt: 1718940000000
}

// 数据库表：historical_tasks
{
  taskId: "task-001",
  userId: "user-12345",
  date: "2026-06-10",
  task_type: "signature_debug",
  root_cause: "UTF-8 编码问题",
  resolution: "修改代码使用 UTF-8 编码",
  duration_minutes: 15,
  fields: {
    appid: "app_merchant_001",
    error_code: "SIGN_INVALID",
    api_path: "/open/order/create"
  }
}

// 向量库：task_embeddings
{
  taskId: "task-001",
  embedding: [0.1, 0.2, ...],  // 768 维向量
  text: "签名失败，原因是 UTF-8 编码问题",
  metadata: {
    task_type: "signature_debug",
    root_cause: "encoding",
    appid: "app_merchant_001"
  }
}
```

### 召回策略（假设）

```javascript
function retrieveLongTermMemory(currentTask) {
  // 1. 召回用户偏好
  const profile = await db.userProfiles.findOne({ 
    appid: currentTask.fields.appid 
  });
  const style = profile?.preferences.responseStyle || "detailed";
  
  // 2. 召回相似历史任务（向量检索）
  const currentEmbedding = await embed(currentTask.description);
  const similarTasks = await vectorDB.search(currentEmbedding, {
    limit: 5,
    filter: { task_type: currentTask.task_type }
  });
  
  // 3. 召回业务上下文
  const context = profile?.businessContext || {};
  
  return {
    userProfile: profile,
    responseStyle: style,
    similarTasks: similarTasks.map(t => ({
      date: t.date,
      root_cause: t.root_cause,
      resolution: t.resolution
    })),
    businessContext: context
  };
}
```

---

## 可视化设计

### Session Board（会话状态板）

```
┌─────────────────────────────────────────────────────────┐
│ 会话状态 / 任务状态                                        │
│ V6 · 第 2 轮 · ready_with_evidence · 已使用上下文          │
├──────────────┬──────────────┬────────────────────────────┤
│ 多轮会话      │ 当前任务      │ 已记住字段                  │
│              │              │                            │
│ #1 签名失败   │ 任务类型:     │ appid: app_001             │
│  → 等待补充   │  签名失败排查 │ error_code: SIGN_INVALID   │
│              │              │ raw_sign_string: order_... │
│ #2 appid=... │ 任务状态:     │                            │
│  → 可继续     │  ready_*     │ [编辑] [删除]               │
│              │              │                            │
│              │ 待补信息: 无  │                            │
│              │              │                            │
│              │ 上下文:       │                            │
│              │  沿用任务，   │                            │
│              │  合并字段     │                            │
└──────────────┴──────────────┴────────────────────────────┘
```

### Memory System Diagram（记忆系统架构图）

```
用户输入
  ↓
┌──────────────────── 范围门控 ──────────────────────┐
│ scopeSignals检测 → 业务范围判断                      │
└─────────────────────┬──────────────────────────────┘
                      ↓
┌──────────────────── 意图识别 ──────────────────────┐
│ 规则优先 → 向量补位 → LLM兜底                        │
└─────────────────────┬──────────────────────────────┘
                      ↓
┌──────────────────── 短期记忆 ──────────────────────┐
│ ┌─ Task Context ────────────────────────────────┐  │
│ │ 当前任务: signature_debug                      │  │
│ │ 状态: waiting_for_user                        │  │
│ │ 缺失: appid, error_code                       │  │
│ └───────────────────────────────────────────────┘  │
│                      ↓                             │
│ ┌─ Field Memory ────────────────────────────────┐  │
│ │ appid: app_001                                │  │
│ │ error_code: SIGN_INVALID                      │  │
│ │ (累积，任务内保留)                              │  │
│ └───────────────────────────────────────────────┘  │
│                      ↓                             │
│ ┌─ Turns History ───────────────────────────────┐  │
│ │ #1: "签名失败" → waiting_for_user              │  │
│ │ #2: "appid=xxx" → ready                       │  │
│ │ (最近 20 轮，UI 显示 5 轮)                      │  │
│ └───────────────────────────────────────────────┘  │
│                                                    │
│ 持久化: localStorage (24h 时效)                    │
└────────────────────────────────────────────────────┘
                      ↓
┌──────────────────── 长期记忆 ──────────────────────┐
│ ⚠️ 未实现                                          │
│                                                    │
│ ┌─ User Profile ────────────────────────────────┐  │
│ │ userId: user-12345                            │  │
│ │ preferences: { style: "detailed" }            │  │
│ │ businessContext: { env: "prod", apis: [...] } │  │
│ └───────────────────────────────────────────────┘  │
│                      ↓                             │
│ ┌─ Historical Tasks ────────────────────────────┐  │
│ │ task-001: 签名失败 (UTF-8编码)                 │  │
│ │ task-002: 回调超时 (HTTPS证书)                 │  │
│ │ (向量检索相似任务)                              │  │
│ └───────────────────────────────────────────────┘  │
│                                                    │
│ 持久化: 数据库 + 向量库                             │
│ 召回: 当前任务 → 检索相似历史 → 提供参考              │
└────────────────────────────────────────────────────┘
```

---

## 改进计划

### Phase 1: 优化短期记忆（当前 PR）

**已完成**：
- ✅ 会话内字段继承
- ✅ 任务状态管理
- ✅ 最近 5 轮对话可视化

**待完成**：
- [ ] localStorage 持久化（刷新页面后恢复）
- [ ] 扩展历史轮次（5 → 20 轮，UI 显示前 5 轮）
- [ ] 字段编辑/删除功能
- [ ] Session 时效管理（24 小时自动清空）
- [ ] 手动重置按钮

### Phase 2: 长期记忆基础（未来）

**前置条件**：
- 用户登录系统
- 用户身份识别（appid → 商户信息）
- 数据库基础设施

**功能**：
- 用户画像（偏好、业务上下文）
- 历史任务记录
- 向量检索相似任务

### Phase 3: 记忆召回策略（未来）

**功能**：
- 自动召回相似历史任务
- 用户偏好注入到 System Prompt
- 业务上下文补全（环境、API 列表）

---

## 参考资料

- Open Design CONTEXT.md: 精确术语定义
- Open Design 设计系统：Local-First + Agent-Native
- 当前实现：`web/index.html` 行 3320-4655
