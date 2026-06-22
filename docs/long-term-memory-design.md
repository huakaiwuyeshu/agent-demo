# 长期记忆设计：单用户 → 多用户演进方案

## 🎯 **核心思路**

你的方案非常合理！**先在单用户场景下实现长期记忆，验证价值后再扩展到多用户**。这是一个渐进式、低风险的演进路径。

---

## 📋 **方案可行性分析**

### **✅ 为什么这个方案可行？**

#### **1. 单用户场景的优势**

| 维度 | 单用户 | 多用户 |
|------|--------|--------|
| **用户识别** | 无需识别（只有你）| 需要登录/身份认证 |
| **数据隔离** | 无需隔离 | 需要严格隔离 |
| **隐私合规** | 简单（自己的数据）| 复杂（GDPR、隐私协议）|
| **存储方案** | localStorage 即可 | 需要后端数据库 |
| **实施难度** | **低** ⭐⭐ | **高** ⭐⭐⭐⭐⭐ |
| **开发周期** | **1-2 天** | **1-2 周** |

**结论**：单用户场景下实现长期记忆，**实施难度降低 70%，开发周期缩短 80%**。

---

#### **2. 渐进式演进的优势**

```
阶段 1: 单用户 + 长期记忆
  ↓
验证价值（使用频率、记忆命中率、体验提升）
  ↓
阶段 2: 多用户 + 用户识别
  ↓
引入登录机制、用户标识
  ↓
阶段 3: 多用户 + 记忆隔离
  ↓
后端数据库、数据隔离、隐私合规
```

**优势**：
- ✅ **快速验证**：1-2 天即可上线，快速验证长期记忆的价值
- ✅ **降低风险**：单用户场景简单，不会引入复杂的用户管理问题
- ✅ **积累经验**：在简单场景下积累长期记忆的设计经验
- ✅ **平滑演进**：后续扩展到多用户时，只需增加用户识别和数据隔离层

---

#### **3. 技术架构的演进路径**

**阶段 1：单用户（当前 → 1-2 天）**
```
┌─────────────────────────────────────┐
│ 浏览器 localStorage                  │
├─────────────────────────────────────┤
│ 短期记忆（Session）                  │
│  • 对话历史（20 轮）                 │
│  • Field Memory                     │
│  • Task Context                     │
├─────────────────────────────────────┤
│ 长期记忆（User Profile）← 新增      │
│  • 历史任务库                        │
│  • 常见问题模式                      │
│  • 用户偏好                          │
└─────────────────────────────────────┘
```

**阶段 2：多用户识别（1-2 周）**
```
┌─────────────────────────────────────┐
│ 用户识别层 ← 新增                    │
│  • 登录机制（邮箱/手机/工号）         │
│  • userId 生成                       │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ localStorage（带 userId 隔离）       │
│  • user_{userId}_session            │
│  • user_{userId}_long_term          │
└─────────────────────────────────────┘
```

**阶段 3：多用户隔离（2-4 周）**
```
┌─────────────────────────────────────┐
│ 前端（浏览器）                        │
│  • 短期记忆（Session）← localStorage │
└─────────────────────────────────────┘
         ↓ API
┌─────────────────────────────────────┐
│ 后端服务 ← 新增                      │
│  • 用户认证 API                      │
│  • 长期记忆存储 API                  │
│  • 数据隔离逻辑                      │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 数据库（MySQL / MongoDB）← 新增      │
│  users 表                            │
│  ├─ userId, email, createdAt        │
│  long_term_memory 表                 │
│  ├─ userId, memoryType, content     │
│  historical_tasks 表                 │
│  ├─ userId, taskId, fields, ...     │
└─────────────────────────────────────┘
```

---

## 🛠️ **阶段 1：单用户长期记忆设计**

### **1. 长期记忆的内容设计**

#### **L1：历史任务库（Historical Tasks）**

**存储内容**：
```javascript
{
  taskId: "task-abc123",
  task_type: "signature_debug",
  created_at: "2026-06-22T14:30:00Z",
  fields: {
    appid: "app_001",
    api_path: "/open/order",
    error_code: "SIGN_INVALID"
  },
  resolution: "success",  // success / failed / abandoned
  notes: "参数未按字典序排序",
  session_count: 3,       // 用了几轮对话解决
  documents_used: ["签名排查 SOP", "SIGN_INVALID 错误码说明"]
}
```

**用途**：
- ✅ 检索相似历史任务（"你上次遇到签名失败，是参数排序问题"）
- ✅ 自动填充常用字段（appid、api_path 记住）
- ✅ 分析常见问题模式（"你最常遇到签名失败"）

---

#### **L2：常见问题模式（Common Patterns）**

**存储内容**：
```javascript
{
  pattern_type: "frequent_task",
  task_type: "signature_debug",
  frequency: 12,          // 出现次数
  last_seen: "2026-06-22",
  common_fields: {
    appid: "app_001",     // 最常用的 appid
    api_path: "/open/order"  // 最常访问的 API
  },
  common_errors: [
    { error_code: "SIGN_INVALID", count: 8 },
    { error_code: "TIMESTAMP_EXPIRED", count: 4 }
  ]
}
```

**用途**：
- ✅ 预测下一个任务（"你通常会问签名排查"）
- ✅ 快速填充（"你的 appid 通常是 app_001"）
- ✅ 个性化推荐（"你最常遇到 SIGN_INVALID 错误"）

---

#### **L3：用户偏好（User Preferences）**

**存储内容**：
```javascript
{
  communication_style: "concise",  // concise / detailed
  preferred_language: "zh-CN",
  frequent_skills: ["signature_debug", "callback_debug"],
  preferred_docs: ["签名排查 SOP"],
  feedback_history: {
    positive_count: 25,
    negative_count: 3,
    badcase_reports: 5
  }
}
```

**用途**：
- ✅ 调整回复风格（"你喜欢简洁的回复"）
- ✅ 优先展示常用 Skill
- ✅ 记住用户满意度

---

### **2. 数据结构设计**

#### **localStorage 存储结构**

```javascript
// 长期记忆主键
const LONG_TERM_MEMORY_KEY = "agent_long_term_memory";

// 数据结构
{
  userId: "default_user",  // 单用户场景固定为 "default_user"
  createdAt: 1718998800000,
  lastUpdatedAt: 1718998900000,

  // L1: 历史任务库
  historicalTasks: [
    {
      taskId: "task-abc123",
      task_type: "signature_debug",
      created_at: "2026-06-22T14:30:00Z",
      fields: { appid: "app_001", api_path: "/open/order", error_code: "SIGN_INVALID" },
      resolution: "success",
      notes: "参数未按字典序排序",
      session_count: 3
    },
    // ... 最多保留 100 个
  ],

  // L2: 常见问题模式
  commonPatterns: {
    frequent_tasks: [
      { task_type: "signature_debug", frequency: 12, last_seen: "2026-06-22" },
      { task_type: "callback_debug", frequency: 5, last_seen: "2026-06-20" }
    ],
    common_fields: {
      appid: "app_001",
      api_path: "/open/order"
    },
    common_errors: [
      { error_code: "SIGN_INVALID", count: 8 },
      { error_code: "TIMESTAMP_EXPIRED", count: 4 }
    ]
  },

  // L3: 用户偏好
  userPreferences: {
    communication_style: "concise",
    preferred_language: "zh-CN",
    frequent_skills: ["signature_debug", "callback_debug"],
    feedback_history: {
      positive_count: 25,
      negative_count: 3
    }
  }
}
```

---

### **3. 核心功能实现**

#### **功能 1：保存历史任务**

```javascript
function saveHistoricalTask(task) {
  const longTermMemory = loadLongTermMemory();

  // 添加到历史任务库
  longTermMemory.historicalTasks.push({
    taskId: task.id,
    task_type: task.task_type,
    created_at: new Date().toISOString(),
    fields: task.fields,
    resolution: task.resolution || "success",
    notes: task.notes || "",
    session_count: task.session_count || 1
  });

  // 只保留最近 100 个任务
  if (longTermMemory.historicalTasks.length > 100) {
    longTermMemory.historicalTasks = longTermMemory.historicalTasks.slice(-100);
  }

  // 更新常见问题模式
  updateCommonPatterns(longTermMemory, task);

  // 保存
  saveLongTermMemory(longTermMemory);
}
```

---

#### **功能 2：检索相似历史任务**

```javascript
function findSimilarHistoricalTasks(currentTask, limit = 3) {
  const longTermMemory = loadLongTermMemory();
  const tasks = longTermMemory.historicalTasks;

  // 按相似度排序
  const scored = tasks.map(task => ({
    task,
    score: calculateSimilarity(currentTask, task)
  })).sort((a, b) => b.score - a.score);

  return scored.slice(0, limit).map(s => s.task);
}

function calculateSimilarity(task1, task2) {
  let score = 0;

  // 任务类型相同：+50
  if (task1.task_type === task2.task_type) {
    score += 50;
  }

  // 字段重叠：每个字段 +10
  const fields1 = Object.keys(task1.fields || {});
  const fields2 = Object.keys(task2.fields || {});
  const overlap = fields1.filter(f => fields2.includes(f)).length;
  score += overlap * 10;

  // 时间衰减：最近的任务得分更高
  const daysSince = (Date.now() - new Date(task2.created_at).getTime()) / (1000 * 60 * 60 * 24);
  score += Math.max(0, 20 - daysSince);

  return score;
}
```

---

#### **功能 3：自动填充常用字段**

```javascript
function autoFillFields(draft) {
  const longTermMemory = loadLongTermMemory();
  const commonFields = longTermMemory.commonPatterns.common_fields;

  // 如果当前任务缺少 appid，且用户有常用 appid，则提示
  if (!draft.fields.appid && commonFields.appid) {
    console.info(`[LongTermMemory] 你的常用 appid 是：${commonFields.appid}`);
    // 可以在 UI 中展示建议
  }

  // 如果当前任务缺少 api_path，且用户有常用 api_path，则提示
  if (!draft.fields.api_path && commonFields.api_path) {
    console.info(`[LongTermMemory] 你最常访问的 API 是：${commonFields.api_path}`);
  }

  return draft;
}
```

---

#### **功能 4：注入到 System Prompt**

```javascript
function buildSystemPromptWithLongTermMemory(draft, validation, docs, tools) {
  let prompt = buildSystemPrompt(draft, validation, docs, tools);

  const longTermMemory = loadLongTermMemory();

  // 注入历史任务
  const similarTasks = findSimilarHistoricalTasks(draft, 2);
  if (similarTasks.length > 0) {
    prompt += `\n\n## 历史任务参考\n`;
    similarTasks.forEach((task, index) => {
      prompt += `${index + 1}. ${taskLabel(task.task_type)} — ${task.notes || "已解决"}\n`;
      prompt += `   字段：${Object.entries(task.fields).map(([k,v]) => `${k}=${v}`).join(", ")}\n`;
    });
  }

  // 注入常见问题模式
  const frequentTasks = longTermMemory.commonPatterns.frequent_tasks.slice(0, 3);
  if (frequentTasks.length > 0) {
    prompt += `\n\n## 用户常见问题\n`;
    frequentTasks.forEach(pattern => {
      prompt += `- ${taskLabel(pattern.task_type)}（${pattern.frequency} 次）\n`;
    });
  }

  // 注入用户偏好
  const prefs = longTermMemory.userPreferences;
  if (prefs.communication_style === "concise") {
    prompt += `\n\n## 回复风格提示\n用户偏好简洁回复，避免冗长解释。`;
  }

  return prompt;
}
```

---

### **4. UI 展示设计**

#### **长期记忆卡片（Session Board 下方）**

```
┌──────────────────────────────────────────┐
│ 💾 长期记忆                               │
├──────────────────────────────────────────┤
│ 📊 统计                                   │
│  • 历史任务：23 个                        │
│  • 最常见问题：签名排查（12 次）          │
│  • 最常用 appid：app_001                  │
│                                          │
│ 🔍 相似历史任务                           │
│  1. 签名失败排查 — 参数未按字典序排序     │
│     appid=app_001, error_code=SIGN_INVALID│
│  2. 签名失败排查 — 时间戳格式错误         │
│     appid=app_001, error_code=TIMESTAMP_...│
│                                          │
│ [查看完整历史] [导出记忆] [清空记忆]      │
└──────────────────────────────────────────┘
```

---

## 🚀 **阶段 2：多用户识别**

### **1. 用户识别方案**

#### **方案 A：简单邮箱识别（推荐）**

```javascript
// 首次访问时，弹窗要求输入邮箱
function initUserIdentity() {
  let userId = localStorage.getItem("agent_user_id");

  if (!userId) {
    const email = prompt("请输入你的邮箱（用于识别身份）：");
    if (!email || !isValidEmail(email)) {
      alert("邮箱格式不正确，请重新输入");
      return initUserIdentity();
    }

    userId = generateUserId(email);  // 如：user_abc123
    localStorage.setItem("agent_user_id", userId);
    localStorage.setItem("agent_user_email", email);
  }

  return userId;
}

function generateUserId(email) {
  // 简单哈希：email → userId
  const hash = btoa(email).replace(/[^a-zA-Z0-9]/g, "").substring(0, 10);
  return `user_${hash}`;
}
```

#### **方案 B：企业工号识别**

```javascript
// 假设你们公司有统一的工号系统
function initUserIdentity() {
  const workId = prompt("请输入你的工号：");
  const userId = `user_${workId}`;
  localStorage.setItem("agent_user_id", userId);
  return userId;
}
```

---

### **2. 数据隔离方案**

#### **localStorage 按 userId 隔离**

```javascript
// 短期记忆键名
function getSessionKey(userId) {
  return `agent_session_${userId}`;
}

// 长期记忆键名
function getLongTermMemoryKey(userId) {
  return `agent_long_term_memory_${userId}`;
}

// 保存会话（带 userId）
function saveSession(userId) {
  const session = {
    sessionId: state.conversation.sessionId,
    userId,  // 新增
    turns: state.conversation.turns,
    memory: state.conversation.memory,
    activeTask: state.conversation.activeTask
  };
  localStorage.setItem(getSessionKey(userId), JSON.stringify(session));
}

// 加载会话（带 userId）
function loadSession(userId) {
  const saved = localStorage.getItem(getSessionKey(userId));
  if (!saved) return null;
  const session = JSON.parse(saved);
  return session;
}
```

---

## 🚀 **阶段 3：多用户隔离（后端）**

### **1. 后端 API 设计**

#### **用户认证 API**

```
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "***"
}

Response:
{
  "userId": "user_abc123",
  "token": "jwt_token_here",
  "email": "user@example.com"
}
```

#### **长期记忆存储 API**

```
GET /api/long-term-memory/{userId}
Response:
{
  "userId": "user_abc123",
  "historicalTasks": [...],
  "commonPatterns": {...},
  "userPreferences": {...}
}

POST /api/long-term-memory/{userId}/tasks
{
  "taskId": "task-abc123",
  "task_type": "signature_debug",
  "fields": {...},
  "resolution": "success"
}
```

---

### **2. 数据库设计**

#### **users 表**
```sql
CREATE TABLE users (
  user_id VARCHAR(50) PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_active_at TIMESTAMP
);
```

#### **long_term_memory 表**
```sql
CREATE TABLE long_term_memory (
  memory_id VARCHAR(50) PRIMARY KEY,
  user_id VARCHAR(50) NOT NULL,
  memory_type ENUM('historical_task', 'common_pattern', 'user_preference'),
  content JSON NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

#### **historical_tasks 表**
```sql
CREATE TABLE historical_tasks (
  task_id VARCHAR(50) PRIMARY KEY,
  user_id VARCHAR(50) NOT NULL,
  task_type VARCHAR(50) NOT NULL,
  fields JSON,
  resolution VARCHAR(20),
  notes TEXT,
  session_count INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

---

## 📊 **实施路径对比**

| 阶段 | 实施内容 | 工作量 | 开发周期 | 成本 | 风险 |
|------|---------|--------|---------|------|------|
| **阶段 1** | 单用户 + 长期记忆 | 低 | 1-2 天 | 0（localStorage）| 低 |
| **阶段 2** | 多用户识别 | 中 | 1 周 | 0（localStorage）| 中 |
| **阶段 3** | 多用户隔离（后端）| 高 | 2-4 周 | 高（服务器 + 数据库）| 高 |

---

## 🎯 **推荐实施计划**

### **第 1 周：阶段 1（单用户长期记忆）**

**Day 1-2：数据结构设计**
- ✅ 定义 `long_term_memory` 数据结构
- ✅ 实现 `saveLongTermMemory()` / `loadLongTermMemory()`
- ✅ 实现 `saveHistoricalTask()`

**Day 3-4：核心功能实现**
- ✅ 实现 `findSimilarHistoricalTasks()`
- ✅ 实现 `autoFillFields()`
- ✅ 实现 `updateCommonPatterns()`

**Day 5：UI 展示**
- ✅ 在 Session Board 下方增加"长期记忆"卡片
- ✅ 展示统计、相似历史任务
- ✅ 增加"清空记忆"按钮

**Day 6-7：测试与优化**
- ✅ 测试记忆存储/加载
- ✅ 测试相似任务检索
- ✅ 优化 UI 展示

---

### **第 2 周：验证价值**

**使用跟踪**：
- 记录长期记忆的命中率（多少次检索到相似任务）
- 记录自动填充的使用率（多少次自动填充生效）
- 记录用户满意度（Badcase 数量是否下降）

**价值评估**：
- 如果命中率 > 30%：说明长期记忆有价值，继续优化
- 如果命中率 < 10%：说明检索算法需要优化
- 如果用户体验提升明显：考虑进入阶段 2（多用户识别）

---

### **第 3-4 周：阶段 2（多用户识别）**

**前提条件**：
- ✅ 阶段 1 验证成功
- ✅ 有多个用户开始使用

**实施内容**：
- 增加用户识别（邮箱 / 工号）
- localStorage 按 userId 隔离
- 测试多用户数据隔离

---

### **第 5-8 周：阶段 3（多用户隔离 - 后端）**

**前提条件**：
- ✅ 用户数量 > 10
- ✅ 需要跨设备访问

**实施内容**：
- 后端 API 开发
- 数据库设计与迁移
- 前后端联调
- 隐私合规（GDPR）

---

## 📚 **关键设计决策**

### **Q1：长期记忆存储在哪里？**

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **localStorage** | 简单、快速、无成本 | 单设备、容量限制（5MB）| 单用户 / 少量用户 |
| **IndexedDB** | 容量大（50MB+）| 复杂度高 | 需要存储大量数据 |
| **后端数据库** | 跨设备、无限容量 | 需要服务器、成本高 | 多用户 / 跨设备 |

**推荐**：
- 阶段 1-2：**localStorage**（简单、快速）
- 阶段 3：**后端数据库**（跨设备、多用户）

---

### **Q2：如何保证长期记忆的隐私？**

| 阶段 | 隐私风险 | 保护措施 |
|------|---------|---------|
| **阶段 1** | 低（只有你）| 无需特殊保护 |
| **阶段 2** | 中（多用户，localStorage）| 数据按 userId 隔离 |
| **阶段 3** | 高（多用户，后端）| 数据加密、访问控制、审计日志 |

---

### **Q3：长期记忆会占用多少空间？**

**估算**（单用户）：
- 历史任务（100 个）：~50 KB
- 常见问题模式：~5 KB
- 用户偏好：~2 KB
- **总计**：~60 KB（远低于 localStorage 5MB 限制）

**多用户**（10 个用户）：
- 总计：~600 KB（仍在 localStorage 限制内）

---

## 🎉 **总结**

### ✅ **你的方案完全可行！**

1. **先在单用户场景下实现长期记忆**
   - 实施难度低（1-2 天）
   - 成本低（localStorage 免费）
   - 风险低（只有你自己使用）

2. **验证价值后再扩展到多用户**
   - 渐进式演进（单用户 → 多用户识别 → 多用户隔离）
   - 每个阶段可独立验证
   - 避免过度设计

3. **最终目标：根据用户适配长短期记忆**
   - 短期记忆：对话上下文（所有用户）
   - 长期记忆：用户画像 + 历史任务（按 userId 隔离）

---

### 🚀 **立即行动**

需要我立即实施**阶段 1（单用户长期记忆）**吗？只需 1-2 天就能让 Agent 记住你的使用习惯！😊

完整设计文档已保存：`docs/long-term-memory-design.md`