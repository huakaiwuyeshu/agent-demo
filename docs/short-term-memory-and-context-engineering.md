# 短期记忆设计与上下文工程分析

## 🎯 **核心问题**

短期记忆存储会话中产生的各类消息（用户输入、模型回复、工具调用及其结果），这些消息直接参与模型推理，实时更新，并受模型 maxToken 限制。当消息累积导致上下文窗口超出限制时，需要通过**上下文工程策略**（压缩、卸载、摘要等）进行处理。

---

## 📋 **当前短期记忆设计分析**

### **1. 数据结构**

#### **Session（会话）结构**
```javascript
state.conversation = {
  sessionId: "api-demo-1718998800000",     // 会话唯一标识
  createdAt: 1718998800000,                 // 创建时间戳
  turns: [                                  // 对话轮次（最多 20 轮）
    {
      index: 1,
      text: "你们接口签名失败",
      intent: "signature_debug",
      status: "needs_clarification",
      missing: ["api_path", "appid", ...],
      fields: { error_code: "SIGN_INVALID" },
      timestamp: 1718998800000
    },
    // ... 最多 20 轮
  ],
  memory: {                                 // 字段记忆
    fields: {
      appid: "app_001",
      error_code: "SIGN_INVALID",
      api_path: "/open/order"
    },
    last_intent: "signature_debug",
    last_validation: "needs_clarification",
    last_route: "local_package"
  },
  activeTask: {                             // 当前任务上下文
    id: "task-abc123",
    task_type: "signature_debug",
    status: "waiting_for_user",
    pending_fields: ["raw_sign_string", "request_time"],
    fields: { ... },
    updated_at: "14:30:00"
  }
};
```

---

### **2. 持久化机制**

#### **存储位置**
```javascript
// localStorage 键名
const STORAGE_KEY = "agent_demo_session";

// 保存函数
function saveSession() {
  const session = {
    sessionId: state.conversation.sessionId,
    createdAt: state.conversation.createdAt,
    lastActiveAt: Date.now(),
    turns: state.conversation.turns,        // 最多 20 轮
    memory: state.conversation.memory,
    activeTask: state.conversation.activeTask
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}
```

#### **加载与过期策略**
```javascript
function loadSession() {
  const session = JSON.parse(localStorage.getItem(STORAGE_KEY));
  const age = Date.now() - session.lastActiveAt;
  const MAX_AGE = 24 * 60 * 60 * 1000;  // 24 小时 TTL

  if (age > MAX_AGE) {
    localStorage.removeItem(STORAGE_KEY);
    return null;  // 过期，返回 null
  }

  return session;  // 恢复会话
}
```

**特点**：
- ✅ 刷新页面不丢失（24h 内）
- ✅ 超过 24h 自动清空
- ✅ 手动重置（`resetConversation()`）

---

### **3. Turn 管理策略**

#### **轮次限制**
```javascript
function commitConversationTurn(message, run) {
  const turn = {
    index: state.conversation.turns.length + 1,
    text: message.trim(),
    intent: run.draft.task_type,
    status: run.session.taskState,
    missing: run.validation.missing_fields,
    fields: compactFields(run.draft.fields),
    timestamp: Date.now()
  };

  // 只保留最近 20 轮
  state.conversation.turns = state.conversation.turns.concat(turn).slice(-20);

  saveSession();
}
```

**策略**：
- **保留轮次**：20 轮（硬编码）
- **淘汰策略**：FIFO（先进先出），超过 20 轮时，最早的轮次被丢弃
- **触发时机**：每次用户输入后，`commitConversationTurn()` 自动执行

---

### **4. LLM 上下文构建**

#### **当前实现**

```javascript
async function sendAgentMessage() {
  // 1. 提取任务
  const draft = extractTask(text);

  // 2. 应用对话上下文（合并 Field Memory）
  const contextualDraft = applyConversationContext(draft);

  // 3. 构建 System Prompt
  const systemPrompt = buildSystemPrompt(contextualDraft, validation, docs, tools, analysisResult);

  // 4. 构建 messages 数组
  const messages = [{ role: "system", content: systemPrompt }];

  // 5. 添加对话历史（最近 10 轮）
  const history = state.agentMessages.slice(-10);
  history.forEach(msg => {
    messages.push({
      role: msg.role === "user" ? "user" : "assistant",
      content: msg.text
    });
  });

  // 6. 调用 LLM
  reply = await callLLM(messages);
}
```

#### **System Prompt 结构**

```javascript
function buildSystemPrompt(draft, validation, docs, tools, analysisResult) {
  let prompt = `你是一个 API 接入技术支持 Agent...

## 当前任务状态
- 任务类型：${taskLabel(draft.task_type)}
- 校验状态：${validation.status}
- 已收集字段：${Object.entries(draft.fields).map(...).join("、")}
- 缺失字段：${validation.missing_fields.map(label).join("、")}`;

  // Inject Skill SOP
  if (SKILL_SOPS[draft.task_type]) {
    prompt += `\n\n${SKILL_SOPS[draft.task_type]}`;
  }

  // Inject knowledge retrieval results
  if (docs.length) {
    prompt += `\n\n## 知识库检索结果\n${docs.slice(0, 5).join("\n")}`;
  }

  // Inject tool results
  if (tools.length) {
    prompt += `\n\n## 工具执行结果\n${tools.map(...).join("\n")}`;
  }

  // Inject data analysis results
  if (analysisResult && analysisResult.available) {
    prompt += `\n\n## 数据分析工具执行结果\n${analysisResult.result}`;
  }

  prompt += `\n\n## 安全规则...`;
  prompt += `\n\n## 回复要求...`;

  return prompt;
}
```

---

### **5. 上下文窗口分析**

#### **当前 Token 消耗估算**

假设使用 GPT-4（8K 上下文窗口）或类似模型：

| 组成部分 | Token 估算 | 说明 |
|---------|-----------|------|
| **System Prompt（固定部分）** | ~500 tokens | Agent 角色 + 能力范围 + 安全规则 + 回复要求 |
| **当前任务状态** | ~100 tokens | 任务类型 + 字段 + 缺失字段 |
| **Skill SOP** | ~300-800 tokens | 签名排查 SOP ~500 tokens |
| **知识库检索结果** | ~500-1500 tokens | 最多 5 条，每条 ~100-300 tokens |
| **工具执行结果** | ~100-300 tokens | 工具名称 + 状态 + 结果摘要 |
| **数据分析结果** | ~200-500 tokens | 趋势分析 + 图表数据 |
| **对话历史（10 轮）** | ~1000-2000 tokens | 每轮 ~100-200 tokens（用户 + Agent） |
| **当前用户输入** | ~50-200 tokens | 当前这轮用户消息 |
| **总计** | **~2750-5900 tokens** | **输入侧** |
| **LLM 生成（输出）** | ~500-1000 tokens | Agent 回复 |
| **总上下文消耗** | **~3250-6900 tokens** | **输入 + 输出** |

#### **问题识别**

✅ **当前状态**：
- 对于 8K 模型：**安全**（70-85% 利用率）
- 对于 16K 模型：**非常安全**（20-43% 利用率）

⚠️ **潜在风险**：
- **对话历史增长**：当前只保留 10 轮，但如果每轮都很长（如用户粘贴大段日志），可能迅速超标
- **知识库检索结果膨胀**：当前最多 5 条，但如果每条都是长文档，可能占用大量 Token
- **Skill SOP 过长**：某些复杂排查 SOP 可能超过 1000 tokens
- **数据分析结果过长**：撤单分析结果如果包含大量数据，可能占用较多 Token

❌ **缺少上下文工程机制**：
- 没有动态 Token 监控
- 没有自动压缩/卸载策略
- 没有摘要机制
- 没有优先级管理

---

## 🛠️ **上下文工程优化方案**

### **策略 1：动态 Token 监控**

#### **实现思路**

```javascript
// Token 计数器（简单估算：1 token ≈ 4 字符）
function estimateTokens(text) {
  return Math.ceil(text.length / 4);
}

// 计算当前上下文 Token 数
function calculateContextTokens(systemPrompt, history) {
  let total = estimateTokens(systemPrompt);
  history.forEach(msg => {
    total += estimateTokens(msg.content);
  });
  return total;
}

// 在构建 messages 前检查
function buildMessagesWithBudget(systemPrompt, history, maxTokens = 6000) {
  const messages = [{ role: "system", content: systemPrompt }];
  let currentTokens = estimateTokens(systemPrompt);

  // 从最新消息开始添加，直到达到预算
  for (let i = history.length - 1; i >= 0; i--) {
    const msgTokens = estimateTokens(history[i].text);
    if (currentTokens + msgTokens > maxTokens) {
      console.warn(`[Context] Reached token budget at turn ${i}, truncating...`);
      break;
    }
    messages.unshift({
      role: history[i].role === "user" ? "user" : "assistant",
      content: history[i].text
    });
    currentTokens += msgTokens;
  }

  console.info(`[Context] Total tokens: ${currentTokens} / ${maxTokens}`);
  return { messages, tokenCount: currentTokens };
}
```

---

### **策略 2：分层压缩**

#### **L1：对话历史压缩**

**方案 A：滑动窗口（当前实现）**
```javascript
// 只保留最近 N 轮
const history = state.agentMessages.slice(-10);
```

**方案 B：关键轮次保留**
```javascript
// 保留：首轮 + 任务变化轮 + 最近 N 轮
function selectImportantTurns(turns, maxTurns = 10) {
  const important = [];

  // 1. 首轮（建立上下文）
  if (turns.length > 0) {
    important.push(turns[0]);
  }

  // 2. 任务类型变化的轮次
  let lastIntent = turns[0]?.intent;
  for (let i = 1; i < turns.length; i++) {
    if (turns[i].intent !== lastIntent) {
      important.push(turns[i]);
      lastIntent = turns[i].intent;
    }
  }

  // 3. 最近 N 轮
  const recent = turns.slice(-maxTurns);
  recent.forEach(turn => {
    if (!important.some(t => t.index === turn.index)) {
      important.push(turn);
    }
  });

  // 按 index 排序
  return important.sort((a, b) => a.index - b.index);
}
```

**方案 C：摘要压缩**
```javascript
// 将早期轮次压缩为摘要
async function compressOldTurns(turns, threshold = 10) {
  if (turns.length <= threshold) return turns;

  const oldTurns = turns.slice(0, -threshold);
  const recentTurns = turns.slice(-threshold);

  // 调用 LLM 压缩早期轮次
  const summary = await summarizeTurns(oldTurns);

  // 返回：摘要 + 最近轮次
  return [
    { role: "system", content: `## 对话摘要\n${summary}` },
    ...recentTurns
  ];
}

async function summarizeTurns(turns) {
  const prompt = `请将以下对话压缩为简洁摘要（100 字以内）：\n\n${turns.map(t => `${t.role}: ${t.text}`).join("\n")}`;
  const summary = await callLLM([{ role: "user", content: prompt }]);
  return summary;
}
```

---

#### **L2：知识库结果压缩**

**方案 A：限制条数（当前实现）**
```javascript
// 最多返回 5 条
docs.slice(0, 5)
```

**方案 B：智能截断**
```javascript
// 每条最多保留 N 字符
function truncateDocs(docs, maxCharsPerDoc = 200) {
  return docs.map(doc => {
    if (doc.length <= maxCharsPerDoc) return doc;
    return doc.slice(0, maxCharsPerDoc) + "...（内容已截断）";
  });
}
```

**方案 C：动态分配 Token 预算**
```javascript
function selectDocsWithBudget(docs, maxTokens = 1500) {
  const selected = [];
  let usedTokens = 0;

  for (const doc of docs) {
    const docTokens = estimateTokens(doc);
    if (usedTokens + docTokens > maxTokens) break;
    selected.push(doc);
    usedTokens += docTokens;
  }

  return selected;
}
```

---

#### **L3：Skill SOP 压缩**

**方案 A：懒加载（按需注入）**
```javascript
// 只在 status = "executable" 时注入完整 SOP
if (validation.status === "executable" && SKILL_SOPS[draft.task_type]) {
  prompt += `\n\n${SKILL_SOPS[draft.task_type]}`;
} else {
  // 其他状态只注入摘要
  prompt += `\n\n## Skill 提示\n任务类型：${taskLabel(draft.task_type)}`;
}
```

**方案 B：分级 SOP**
```javascript
// 定义简版 SOP 和完整版 SOP
const SKILL_SOPS_SHORT = {
  signature_debug: "签名排查：检查参数排序、时间戳、算法、编码。",
  // ...
};

const SKILL_SOPS_FULL = {
  signature_debug: "...<完整 SOP 内容>...",
  // ...
};

// 根据上下文预算选择版本
if (remainingTokens > 2000) {
  prompt += SKILL_SOPS_FULL[draft.task_type];
} else {
  prompt += SKILL_SOPS_SHORT[draft.task_type];
}
```

---

### **策略 3：卸载（Offloading）**

#### **方案 A：外部状态管理**

将某些信息存储在会话外，只在需要时检索：

```javascript
// 将 Field Memory 存储到独立的 key
localStorage.setItem(`field_memory_${sessionId}`, JSON.stringify(fields));

// 只在需要时加载
function getFieldMemory(sessionId) {
  return JSON.parse(localStorage.getItem(`field_memory_${sessionId}`) || "{}");
}
```

#### **方案 B：向量数据库（长期方案）**

```javascript
// 将对话历史存储到向量数据库
async function indexTurn(turn) {
  const embedding = await getEmbedding(turn.text);
  await vectorDB.insert({
    id: `turn_${turn.index}`,
    sessionId: state.conversation.sessionId,
    text: turn.text,
    embedding,
    metadata: { intent: turn.intent, timestamp: turn.timestamp }
  });
}

// 只检索相关轮次
async function retrieveRelevantTurns(query, maxTurns = 5) {
  const queryEmbedding = await getEmbedding(query);
  const results = await vectorDB.search(queryEmbedding, {
    filter: { sessionId: state.conversation.sessionId },
    limit: maxTurns
  });
  return results.map(r => r.text);
}
```

---

### **策略 4：优先级管理**

#### **信息优先级定义**

| 优先级 | 信息类型 | 必要性 | Token 预算 |
|--------|---------|--------|-----------|
| **P0（必须）** | System Prompt（核心部分）| 必须 | ~300 tokens |
| **P0（必须）** | 当前任务状态 | 必须 | ~100 tokens |
| **P0（必须）** | 当前用户输入 | 必须 | ~50-200 tokens |
| **P1（高）** | 最近 3 轮对话 | 高 | ~300-600 tokens |
| **P1（高）** | 当前任务的 Skill SOP | 高 | ~300-800 tokens |
| **P2（中）** | 知识库检索结果 | 中 | ~500-1500 tokens |
| **P2（中）** | 工具执行结果 | 中 | ~100-300 tokens |
| **P3（低）** | 更早的对话历史（3-10 轮）| 低 | ~700-1400 tokens |
| **P3（低）** | 数据分析结果 | 低 | ~200-500 tokens |

#### **动态预算分配**

```javascript
function allocateTokenBudget(totalBudget = 6000) {
  const budget = {
    systemPrompt: 300,      // P0
    taskState: 100,         // P0
    currentInput: 200,      // P0
    recentTurns: 600,       // P1 (3 轮 × 200 tokens)
    skillSOP: 500,          // P1
    knowledgeDocs: 0,       // P2 (动态分配)
    toolResults: 0,         // P2 (动态分配)
    oldTurns: 0,            // P3 (动态分配)
    dataAnalysis: 0         // P3 (动态分配)
  };

  const mandatoryTokens = budget.systemPrompt + budget.taskState + budget.currentInput + budget.recentTurns + budget.skillSOP;
  const remainingTokens = totalBudget - mandatoryTokens;

  // 按优先级分配剩余预算
  if (remainingTokens > 0) {
    budget.knowledgeDocs = Math.min(remainingTokens * 0.4, 1500);
    budget.toolResults = Math.min(remainingTokens * 0.2, 300);
    budget.oldTurns = Math.min(remainingTokens * 0.3, 1400);
    budget.dataAnalysis = Math.min(remainingTokens * 0.1, 500);
  }

  return budget;
}
```

---

## 📊 **优化方案对比**

| 策略 | 优点 | 缺点 | 适用场景 | 实施难度 |
|------|------|------|---------|---------|
| **滑动窗口** | 简单、可靠 | 丢失早期上下文 | 短对话（< 20 轮）| 低（已实现）|
| **关键轮次保留** | 保留重要信息 | 判断逻辑复杂 | 多任务切换场景 | 中 |
| **摘要压缩** | 保留语义 | 需要额外 LLM 调用 | 长对话（> 20 轮）| 高 |
| **智能截断** | 降低单项 Token | 可能丢失关键细节 | 文档/日志过长 | 低 |
| **动态预算分配** | 资源利用最优 | 计算开销 | 所有场景 | 中 |
| **外部状态管理** | 降低上下文压力 | 增加 I/O | 字段较多 | 中 |
| **向量检索** | 只检索相关上下文 | 基础设施要求高 | 超长对话 | 高 |

---

## 🚀 **推荐实施路径**

### **阶段 1：基础监控（立即实施）**

**目标**：了解当前 Token 消耗情况

**实施内容**：
1. 添加 `estimateTokens()` 函数
2. 在每次 LLM 调用前输出 Token 统计
3. 在 Session Board 中显示当前 Token 使用量

**工作量**：~2 小时  
**改动量**：~50 行代码

```javascript
// 示例代码
function buildMessagesWithLogging(systemPrompt, history) {
  const systemTokens = estimateTokens(systemPrompt);
  const historyTokens = history.reduce((sum, msg) => sum + estimateTokens(msg.text), 0);
  const total = systemTokens + historyTokens;

  console.info(`[Context] System: ${systemTokens}, History: ${historyTokens}, Total: ${total}`);

  return messages;
}
```

---

### **阶段 2：动态预算管理（短期）**

**目标**：根据 Token 预算动态调整上下文

**实施内容**：
1. 实现 `allocateTokenBudget()` 函数
2. 实现 `buildMessagesWithBudget()` 函数
3. 对知识库检索结果、对话历史应用预算限制

**工作量**：~1 天  
**改动量**：~200 行代码

---

### **阶段 3：智能压缩（中期）**

**目标**：对超长内容进行智能压缩

**实施内容**：
1. 实现关键轮次保留算法
2. 对知识库文档应用智能截断
3. Skill SOP 分级（简版/完整版）

**工作量**：~2 天  
**改动量**：~300 行代码

---

### **阶段 4：摘要机制（长期）**

**目标**：对早期对话进行摘要压缩

**实施内容**：
1. 实现 `summarizeTurns()` 函数
2. 在对话历史超过阈值时自动触发摘要
3. 将摘要注入到 System Prompt

**工作量**：~3 天  
**改动量**：~400 行代码

---

## 📝 **总结**

### **当前短期记忆设计**

✅ **优点**：
- 简单可靠（localStorage 持久化）
- 24h TTL 自动过期
- Turn 轮次限制（20 轮）
- 对话历史限制（10 轮进 LLM）

⚠️ **不足**：
- **缺少 Token 监控**：不知道当前 Token 消耗
- **缺少动态调整**：固定 10 轮历史，无论 Token 是否充足
- **缺少压缩机制**：长文档、长对话无法压缩
- **缺少优先级管理**：所有信息平等对待

### **上下文工程的核心价值**

1. **延长对话长度**：通过压缩/卸载，支持更长的对话
2. **提升回复质量**：保留关键上下文，丢弃冗余信息
3. **降低成本**：减少 Token 消耗
4. **提升稳定性**：避免超出上下文窗口导致的错误

### **建议优先级**

1. **立即实施**：Token 监控（了解现状）
2. **短期实施**：动态预算管理（解决 80% 问题）
3. **中期实施**：智能压缩（应对复杂场景）
4. **长期规划**：摘要机制 + 向量检索（支持超长对话）

---

需要我立即实施**阶段 1（基础监控）**吗？只需 ~2 小时就能看到当前 Token 消耗情况！😊