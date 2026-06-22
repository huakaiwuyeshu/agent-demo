# Badcase 处理机制设计

## 🎯 设计目标

构建一个**闭环的 Badcase 处理系统**，从发现问题 → 分析根因 → 修复验证 → 持续优化。

---

## 📚 核心概念

### 什么是 Badcase？

**Badcase（坏例）**：Agent 给出的响应不符合预期，导致用户体验差或任务失败。

### Badcase vs Bug

| 维度 | Badcase | Bug |
|------|---------|-----|
| **定义** | 结果不符合预期 | 代码逻辑错误 |
| **表现** | Agent 回答错误、遗漏、误导 | 程序崩溃、报错、功能失效 |
| **原因** | 模型、Prompt、知识、规则 | 代码 Bug |
| **修复** | 优化 Prompt、补充知识、调整规则 | 修复代码 |
| **举例** | "签名失败"被识别为"回调问题" | `TypeError: undefined` |

---

## 🔍 Badcase 分类体系

### **L1：根因分类（用于定位问题）**

```
┌─ 意图识别错误（Intent Recognition Error）
│  • 任务类型识别错误（signature_debug 误识别为 callback_debug）
│  • 关键词命中偏差（"签名"未命中，"回调"误命中）
│  • 置信度阈值问题（confidence < 0.5 但仍然执行）
│
├─ 字段提取错误（Field Extraction Error）
│  • 正则匹配失败（appid 格式特殊，未提取）
│  • 字段值解析错误（时间格式不标准）
│  • 敏感信息误判（正常字段被标记为 appsecret）
│
├─ Schema 校验缺陷（Schema Validation Issue）
│  • 必填字段定义不准确（缺少某个关键字段）
│  • 校验逻辑过严（本可执行的任务被拒绝）
│  • 校验逻辑过松（缺少字段仍然执行）
│
├─ Skill 路由错误（Skill Routing Error）
│  • 路由映射缺失（新任务类型未配置 Skill）
│  • 路由条件错误（task_type 正确但 Skill 不匹配）
│
├─ Skill SOP 问题（Skill SOP Issue）
│  • SOP 内容过时（排查步骤已不适用）
│  • SOP 遗漏场景（未覆盖某类常见错误）
│  • SOP 表述不清（LLM 无法理解或执行）
│
├─ 知识检索失败（Knowledge Retrieval Failure）
│  • 文档不存在（用户询问的 API 文档缺失）
│  • 检索相关性差（返回无关文档）
│  • 向量索引问题（语义相似但未召回）
│
├─ LLM 生成质量（LLM Generation Quality）
│  • 幻觉（Hallucination）：编造不存在的字段、API、错误码
│  • 遗漏（Omission）：未提及关键排查步骤
│  • 误导（Misleading）：给出错误的排查方向
│  • 格式错误（Format Error）：回复格式不符合预期
│
├─ 记忆系统问题（Memory System Issue）
│  • 字段未累积（Turn 1 的 appid 在 Turn 2 丢失）
│  • 错误覆盖（新意图误判，覆盖了当前任务）
│  • 持久化失败（刷新页面后记忆丢失）
│
└─ 安全边界问题（Security Boundary Issue）
   • 误拦截（正常请求被 blocked）
   • 漏拦截（敏感信息未被检测）
```

---

### **L2：影响分类（用于优先级排序）**

```
P0 - 阻断性（Blocker）
  • Agent 完全无法响应（程序崩溃、死循环）
  • 敏感信息泄漏（appsecret 进入日志）
  • 误导用户做危险操作（删除数据、修改配置）

P1 - 严重（Critical）
  • 意图识别完全错误（签名问题识别为回调问题）
  • 关键字段提取失败（appid、error_code 未提取）
  • Skill 路由失败（无法命中任何 SOP）

P2 - 重要（Major）
  • 字段提取部分失败（5 个字段只提取 3 个）
  • Skill SOP 遗漏场景（80% 场景覆盖）
  • LLM 生成遗漏关键步骤（5 步 SOP 只执行 3 步）

P3 - 一般（Minor）
  • 回复格式不美观（换行、缩进问题）
  • 术语不统一（有时说"会话"，有时说"Session"）
  • 置信度显示不准确（实际 0.86，显示 0.8）

P4 - 优化（Enhancement）
  • 回复速度慢（超过 3 秒）
  • UI 交互不流畅（按钮响应慢）
  • 文案优化（"请补充信息" → "还缺少：xxx"）
```

---

## 📥 Badcase 收集机制

### **方式 1：用户主动反馈**

#### **UI 设计：对话反馈按钮**

```
┌────────────────────────────────────────┐
│ Agent: 我已识别为「签名失败排查」...   │
│                                        │
│ [👍 有帮助] [👎 没帮助] [🐛 报告问题]  │
└────────────────────────────────────────┘
```

**点击「👎 没帮助」后弹窗**：
```
┌──────────────────────────────────────────┐
│ 📋 反馈问题                               │
├──────────────────────────────────────────┤
│ 这次回复哪里不对？（可多选）             │
│                                          │
│ ☐ 识别错任务类型                         │
│ ☐ 提取字段不准确                         │
│ ☐ 追问的问题不对                         │
│ ☐ 排查步骤有问题                         │
│ ☐ 回答不完整                             │
│ ☐ 回答有误导                             │
│ ☐ 其他（请说明）                         │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ 补充说明（选填）：                 │  │
│ │                                    │  │
│ └────────────────────────────────────┘  │
│                                          │
│           [取消]  [提交反馈]             │
└──────────────────────────────────────────┘
```

**提交后数据结构**：
```javascript
{
  feedbackId: "fb_1234567890",
  timestamp: "2026-06-22T14:30:00Z",
  sessionId: "api-demo-1718998800000",
  turnIndex: 3,
  userMessage: "你们接口签名失败，appid=xxx",
  agentResponse: "我已识别为「签名失败排查」...",
  
  // 反馈内容
  feedbackType: "negative",  // positive / negative / bug
  issues: ["识别错任务类型", "提取字段不准确"],
  comment: "appid 没有提取出来",
  
  // 上下文快照
  context: {
    task_type: "signature_debug",
    fields: { error_code: "SIGN_INVALID" },  // 缺少 appid
    confidence: 0.86,
    status: "needs_clarification",
    missing_fields: ["api_path", "appid", "raw_sign_string", "request_time"]
  }
}
```

---

### **方式 2：自动检测（系统主动发现）**

#### **检测规则**

```javascript
// 检测 1：意图识别置信度过低
if (confidence < 0.5) {
  createBadcase({
    type: "低置信度意图识别",
    severity: "P2",
    context: { task_type, confidence, hits }
  });
}

// 检测 2：字段提取失败率高
if (extractedFields.length < requiredFields.length / 2) {
  createBadcase({
    type: "字段提取失败",
    severity: "P1",
    context: { extractedFields, requiredFields }
  });
}

// 检测 3：连续追问超过 3 轮
if (clarificationRounds > 3) {
  createBadcase({
    type: "追问轮次过多",
    severity: "P2",
    context: { clarificationRounds, missingFields }
  });
}

// 检测 4：用户放弃对话
if (timeSinceLastTurn > 5 * 60 * 1000) {  // 5 分钟无响应
  createBadcase({
    type: "用户放弃对话",
    severity: "P3",
    context: { lastTurn, timeSinceLastTurn }
  });
}

// 检测 5：敏感信息误判
if (security_flags.includes("contains_appsecret") && !reallyContainsSecret(message)) {
  createBadcase({
    type: "敏感信息误判",
    severity: "P1",
    context: { message, security_flags }
  });
}
```

---

### **方式 3：数据分析（离线挖掘）**

**定期分析 Session 数据**：
```
每日分析：
  • 平均对话轮次（> 5 轮 → 可能存在问题）
  • 任务完成率（status = "executable" 占比）
  • 字段提取成功率（extracted / required）
  • Skill 命中率（非 unknown 占比）
  
异常模式：
  • 某个 task_type 的置信度普遍较低
  • 某个字段的提取失败率 > 30%
  • 某个 Skill 的用户反馈差评率 > 20%
```

---

## 🔬 Badcase 分析流程

### **Step 1：根因定位**

```
Badcase 报告
  ↓
[自动分类] → L1 根因分类
  ↓
[上下文回溯] → 读取完整 Session 数据
  ↓
[关键决策点追踪]
  • 意图识别：detectTask() 输入/输出
  • 字段提取：extractTask() 输入/输出
  • Schema 校验：validate() 输入/输出
  • Skill 路由：skills[task_type] 映射
  • LLM 调用：System Prompt + User Message
  ↓
[根因确认] → 定位到具体代码/数据/规则
```

**示例：字段提取失败**
```
Badcase: appid 未提取

上下文回溯：
  • 用户输入："appid是app_demo_001"
  • 正则规则：/(?:appid|app_id)\s*[=:：]\s*([A-Za-z0-9_\-]+)/i
  • 匹配结果：null
  
根因定位：
  • 正则未匹配"appid是"这种无等号格式
  • 需要扩展正则支持"appid是xxx"、"appid为xxx"
```

---

### **Step 2：影响评估**

```javascript
function assessImpact(badcase) {
  // 影响用户数
  const affectedUsers = countAffectedSessions(badcase.pattern);
  
  // 影响频率
  const frequency = countOccurrences(badcase.pattern, last7Days);
  
  // 修复成本
  const fixCost = estimateCost(badcase.rootCause);
  
  // 优先级计算
  let priority = "P3";
  if (badcase.severity === "P0") priority = "P0";
  else if (affectedUsers > 100 || frequency > 50) priority = "P1";
  else if (affectedUsers > 20 || frequency > 10) priority = "P2";
  
  return { affectedUsers, frequency, fixCost, priority };
}
```

---

## 🔧 Badcase 修复策略

### **根因 → 修复方案映射表**

| 根因分类 | 修复方案 | 修复位置 | 工作量 |
|---------|---------|---------|--------|
| **意图识别错误** | 调整关键词权重 / 增加训练样本 | `detectTask()` 函数 | 低 |
| **字段提取错误** | 扩展正则规则 / 增加容错逻辑 | `extractTask()` 函数 | 低 |
| **Schema 校验缺陷** | 调整必填字段定义 / 优化校验逻辑 | `requiredFields` 对象 + `validate()` 函数 | 中 |
| **Skill 路由错误** | 添加路由映射 / 修复路由条件 | `skills` 对象 | 低 |
| **Skill SOP 问题** | 更新 SKILL.md 内容 / 补充场景 | `skills/*/SKILL.md` 文件 | 中 |
| **知识检索失败** | 补充文档 / 优化检索策略 | `data/knowledge/` + RAG 逻辑 | 高 |
| **LLM 生成质量** | 优化 System Prompt / 调整模型参数 | LLM 调用代码 | 中 |
| **记忆系统问题** | 修复记忆逻辑 / 优化持久化策略 | Memory 相关函数 | 中 |
| **安全边界问题** | 调整安全规则 / 优化检测逻辑 | Security 检查代码 | 中 |

---

### **修复示例 1：扩展正则规则**

**Badcase**: "appid是app_001" 未提取出 appid

**根因**: 正则只匹配"appid=xxx"格式

**修复方案**:
```javascript
// Before
appid: firstMatch(/(?:appid|app_id)\s*[=:：]\s*([A-Za-z0-9_\-]+)/i, message),

// After（支持"是"、"为"）
appid: firstMatch(/(?:appid|app_id)\s*(?:[=:：]|是|为)\s*([A-Za-z0-9_\-]+)/i, message),
```

**验证**:
```javascript
// 测试用例
const testCases = [
  "appid=app_001",          // 原支持 ✓
  "appid: app_001",         // 原支持 ✓
  "appid是app_001",         // 新支持 ✓
  "appid为app_001",         // 新支持 ✓
  "我的appid是app_001",     // 新支持 ✓
];
```

---

### **修复示例 2：调整关键词权重**

**Badcase**: "签名验证失败" 被识别为 unknown（置信度 0.3）

**根因**: "验证" 不在关键词列表中

**修复方案**:
```javascript
// Before
hits = {
  signature_debug: hitCount(message, ["签名", "验签", "SIGN_INVALID"]),
  // ...
}

// After（增加"验证"、"校验"）
hits = {
  signature_debug: hitCount(message, ["签名", "验签", "验证", "校验", "SIGN_INVALID"]),
  // ...
}
```

---

### **修复示例 3：更新 Skill SOP**

**Badcase**: 签名排查 Skill 未提及"URL 编码"问题

**根因**: Skill SOP 遗漏常见错误场景

**修复方案**:
```markdown
// skills/signature_debug/SKILL.md

## 排查 SOP
1. 检查参数是否按字典序排序。
2. 检查 timestamp 是否在有效期内（±5分钟）。
3. 检查签名算法是否正确（HMAC-SHA256）。
4. 检查字符编码是否为 UTF-8。
5. **【新增】检查参数值是否进行了 URL 编码**。  ← 补充
6. 对比签名前字符串与文档示例。
```

---

## ✅ Badcase 闭环验证

### **验证流程**

```
Badcase 修复
  ↓
[单元测试] → 测试用例覆盖
  ↓
[回归测试] → 历史 Badcase 集验证
  ↓
[灰度发布] → 10% 用户流量
  ↓
[效果监控]
  • Badcase 数量是否下降
  • 用户满意度是否提升
  • 是否引入新的 Badcase
  ↓
[全量发布] or [回滚]
```

---

### **监控指标**

```javascript
// 每日 Badcase 监控
const metrics = {
  totalBadcases: 120,          // 总 Badcase 数
  p0: 0,                       // P0 数量（阻断性）
  p1: 5,                       // P1 数量（严重）
  p2: 30,                      // P2 数量（重要）
  p3: 85,                      // P3 数量（一般）
  
  // 按根因分类
  byRootCause: {
    intentRecognition: 20,
    fieldExtraction: 35,
    schemaValidation: 10,
    skillRouting: 5,
    skillSOP: 15,
    knowledgeRetrieval: 10,
    llmQuality: 20,
    memory: 3,
    security: 2
  },
  
  // 趋势（与昨日对比）
  trend: {
    total: -8,                 // 总数下降 8 个
    p0: 0,
    p1: -2,
    p2: -3,
    p3: -3
  },
  
  // 修复进度
  fixProgress: {
    fixed: 85,                 // 已修复
    inProgress: 20,            // 修复中
    pending: 15                // 待修复
  }
};
```

---

## 🎨 UI 实现方案

### **1. 对话反馈按钮（最小化设计）**

```html
<!-- 在每条 Agent 回复下方 -->
<div class="message-feedback">
  <button class="feedback-btn" onclick="feedback('positive', turnIndex)">
    <svg>👍</svg>
  </button>
  <button class="feedback-btn" onclick="feedback('negative', turnIndex)">
    <svg>👎</svg>
  </button>
  <button class="feedback-btn" onclick="reportBug(turnIndex)">
    <svg>🐛</svg>
    <span>报告问题</span>
  </button>
</div>
```

**样式**：
- 默认隐藏，鼠标悬停时显示
- 按钮小而简洁（24x24px）
- 与 Agent 回复卡片融为一体

---

### **2. Badcase 上报弹窗**

```html
<div id="badcaseModal" class="modal">
  <div class="modal-content">
    <h3>📋 反馈问题</h3>
    
    <!-- 问题类型（多选） -->
    <div class="issue-types">
      <label><input type="checkbox" value="intent"> 识别错任务类型</label>
      <label><input type="checkbox" value="field"> 提取字段不准确</label>
      <label><input type="checkbox" value="clarify"> 追问的问题不对</label>
      <label><input type="checkbox" value="sop"> 排查步骤有问题</label>
      <label><input type="checkbox" value="incomplete"> 回答不完整</label>
      <label><input type="checkbox" value="misleading"> 回答有误导</label>
      <label><input type="checkbox" value="other"> 其他</label>
    </div>
    
    <!-- 补充说明 -->
    <textarea placeholder="补充说明（选填）"></textarea>
    
    <!-- 按钮 -->
    <div class="modal-actions">
      <button onclick="closeBadcaseModal()">取消</button>
      <button onclick="submitBadcase()">提交反馈</button>
    </div>
  </div>
</div>
```

---

### **3. Badcase 管理面板（开发者视角）**

**新增标签页：Badcase 分析**

```
┌────────────────────────────────────────────┐
│ Agent Chat | 版本体验 | 实现流程 | 数据分析 | Badcase 分析 │ ← 新增
└────────────────────────────────────────────┘

【Badcase 分析】面板内容：

┌──────────────────────────────────────────┐
│ 📊 Badcase 概览                           │
├──────────────────────────────────────────┤
│ 总数：120    P0: 0   P1: 5   P2: 30   P3: 85 │
│ 趋势：↓ -8（较昨日）                      │
├──────────────────────────────────────────┤
│ 📋 按根因分类                             │
│  • 字段提取错误：35 (29%)                 │
│  • 意图识别错误：20 (17%)                 │
│  • LLM 生成质量：20 (17%)                 │
│  • Skill SOP 问题：15 (13%)               │
│  • 知识检索失败：10 (8%)                  │
│  • 其他：20 (16%)                         │
├──────────────────────────────────────────┤
│ 🔥 Top 5 高频 Badcase                     │
│  1. appid 格式"是"未匹配 (12次)           │
│  2. "验证"关键词未命中 (8次)              │
│  3. 签名 SOP 遗漏 URL 编码 (6次)          │
│  4. 时间格式"yyyy/mm/dd"未识别 (5次)      │
│  5. callback_url 提取遗漏端口 (4次)       │
└──────────────────────────────────────────┘

【点击某个 Badcase 展开详情】：
┌──────────────────────────────────────────┐
│ Badcase #BC_001                           │
├──────────────────────────────────────────┤
│ 类型：字段提取错误                        │
│ 严重性：P2（重要）                        │
│ 频率：12 次/周                            │
│ 影响用户：8 人                            │
├──────────────────────────────────────────┤
│ 📝 问题描述                               │
│ 用户输入"appid是app_001"，appid 未提取    │
│                                          │
│ 🔍 根因分析                               │
│ 正则只匹配"appid=xxx"，不支持"appid是xxx" │
│                                          │
│ 🛠️ 修复方案                               │
│ 扩展正则：/(?:appid|app_id)\s*(?:[=:：]|是|为).../ │
│                                          │
│ ✅ 修复状态                               │
│ [已修复] 2026-06-20 15:30                │
│                                          │
│ 📊 修复效果                               │
│ 修复后 7 天：0 次复现 ✓                  │
└──────────────────────────────────────────┘
```

---

## 📈 Badcase 持续优化

### **优化循环**

```
Week 1: 收集 Badcase
  ↓
Week 2: 分析 Top 10 高频 Badcase
  ↓
Week 3: 修复 P0/P1 Badcase
  ↓
Week 4: 灰度验证 + 全量发布
  ↓
Week 5: 监控新 Badcase，重新进入循环
```

---

### **优化目标（示例）**

```
Q1 目标：
  • P0 Badcase 数量 = 0
  • P1 Badcase 数量 < 5
  • 总 Badcase 数量下降 30%
  • 用户满意度（👍 比例）> 80%
  
Q2 目标：
  • P1 Badcase 数量 < 3
  • 总 Badcase 数量下降 50%（相比 Q1 初）
  • 平均对话轮次 < 3 轮
  • Skill 命中率 > 90%
```

---

## 🛠️ 实施建议

### **阶段 1：基础收集（立即实施）**

✅ **最小化反馈按钮**
- 在每条 Agent 回复下方增加 👍 / 👎 / 🐛 按钮
- 点击 👎 弹出简单的问题类型选择
- 数据存储到 localStorage（临时）

**工作量**：~2 小时  
**改动量**：~50 行代码

---

### **阶段 2：自动检测（短期）**

✅ **内置检测规则**
- 置信度过低自动标记
- 字段提取失败率监控
- 连续追问次数监控

**工作量**：~4 小时  
**改动量**：~100 行代码

---

### **阶段 3：分析面板（中期）**

✅ **Badcase 管理面板**
- 新增"Badcase 分析"标签页
- 展示概览、分类、Top 高频问题
- 支持查看详情和修复状态

**工作量**：~1 天  
**改动量**：~300 行代码

---

### **阶段 4：闭环优化（长期）**

✅ **持续优化机制**
- 定期分析（每周/每月）
- 优先级排序
- 修复验证
- 效果监控

**工作量**：持续投入  
**改动量**：根据 Badcase 类型动态调整

---

## 📚 相关文档

- **记忆系统设计**：`docs/memory-system-design.md`
- **Schema/Skill 设计**：`docs/schema-skill-design.md`
- **架构图优化**：`docs/flow-diagram-optimization-proposal.md`

---

## 🎯 总结

### **Badcase 处理的核心**

1. **收集**：用户反馈 + 自动检测 + 数据分析
2. **分类**：L1 根因分类 + L2 影响分类
3. **分析**：根因定位 + 影响评估
4. **修复**：针对性方案 + 快速迭代
5. **验证**：闭环监控 + 效果评估

### **关键指标**

- **Badcase 数量**：总数及 P0/P1/P2/P3 分布
- **修复速度**：P0 < 24h，P1 < 3 天，P2 < 1 周
- **复现率**：修复后 7 天内复现率 < 5%
- **用户满意度**：👍 比例 > 80%

---

需要我立即实施**阶段 1（基础收集）**吗？只需 ~2 小时就能上线用户反馈功能！😊