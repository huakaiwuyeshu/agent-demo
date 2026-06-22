# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **API 接入 Agent 演示系统** - a progressive demonstration of Agent capabilities from simple Q&A to a full business Agent with multi-turn conversations, document retrieval, and tool calling. The system uses API troubleshooting scenarios (signature failures, callback issues) to showcase how Agent architectures evolve.

**Core Architecture**: Single-page web application (`web/index.html`) with embedded JavaScript implementing V0-V7 versions of Agent capabilities.

## Running the Demo

### Web Demo (Primary)

```bash
# Windows: Quick launch
start_services.bat

# Manual (for both LLM proxy and web server):
python web/proxy.py                          # Port 8081 (LLM API proxy)
python -m http.server 8080 --directory web   # Port 8080 (web server)
# Then visit http://localhost:8080/
```

### Stop Services

```bash
stop_services.bat
```

**LLM API Configuration**: Located in `web/proxy.py`
- Endpoint: `LLM_ENDPOINT`
- API Key: `LLM_KEY`
- Model: gpt-5.5 (specified in frontend requests)

## Architecture

### Memory System

#### Short-term Memory

**Terminology** (critical - used consistently across code/UI/docs):
- **Session**: User lifecycle from page open to close/reset (persisted to localStorage, 24h TTL)
- **Turn**: One user input + Agent response (max 20 stored, 5 displayed)
- **Task Context**: Current task snapshot (task_type, status, fields, updated_at)
- **Field Memory**: Extracted business fields accumulated within Session (append-only unless manually edited)

**Implementation**: All in `web/index.html`
- `saveSession()` / `loadSession()` - localStorage persistence
- `commitConversationTurn()` - append Turn with auto-save
- `applyConversationContext()` - merge field memory across turns
- `resetConversation()` - clear state + localStorage

**UI Location**: Session Board (bottom panel in Agent Chat mode)

#### Long-term Memory

**Purpose**: Store and retrieve similar historical tasks to provide context for current queries.

**Data Structure** (localStorage key: `agent_long_term_memory`):
```javascript
{
  userId: "default_user",
  historicalTasks: [  // Max 100 tasks
    {
      taskId: "task-1234567890",
      task_type: "signature_debug",
      created_at: "2026-06-22T14:30:00Z",
      fields: { appid: "app_001", error_code: "SIGN_INVALID" },
      resolution: "success",
      notes: "参数未按字典序排序"
    }
  ],
  commonPatterns: {
    frequent_tasks: [{ task_type: "signature_debug", frequency: 12 }],
    common_fields: { appid: "app_001" }
  }
}
```

**Core Functions**:
- `addHistoricalTask()` - Save completed task to history
- `searchSimilarTasks()` - TF-IDF semantic search for similar tasks (30-day decay factor)
- `injectLongTermMemoryToPrompt()` - Append top 3 similar cases to System Prompt
- `updateCommonPatterns()` - Track task type frequencies and common fields

**Retrieval Algorithm**:
1. Task type match: +50 points
2. Field overlap: +10 points per shared field
3. Text similarity: +5 points per common token (>2 chars)
4. Time decay: score × 0.5^(days/30) (30-day half-life)

**UI Actions**: Export/clear memory via Session Board

### Schema Validation & Skill Routing

**Schema Validation** (`validate()` function):
```javascript
requiredFields = {
  signature_debug: ["api_path", "appid", "raw_sign_string", "error_code", "request_time"],
  callback_debug: ["callback_url", "order_id", "trigger_action", "request_time"],
  api_field_qa: ["field_name"],
  // ...
}
```

Returns one of:
- `executable` - all required fields present → route to Skill
- `needs_clarification` - missing fields → precise follow-up questions
- `blocked` - security boundary (e.g., contains appsecret) → refuse execution

**Skill Routing** (`skills` object):
```javascript
skills = {
  signature_debug: "signature_debug/SKILL.md",
  callback_debug: "callback_debug/SKILL.md",
  api_field_qa: "api_field_qa/SKILL.md",
  credential_request: "human_review_gate",  // special: manual review
}
```

Task type → Skill file path → Load SOP → Inject into LLM context

### Agent Workflow

**Intent Recognition** (`detectTask()`): Keyword matching → task_type
**Field Extraction** (`extractTask()`): Regex patterns → structured fields
**Schema Validation** → Check required fields
**Skill Routing** → Load SOP for task_type
**LLM Call** → System Prompt = Skill SOP + user fields + similar historical cases → diagnosis

### Badcase Feedback System

**Purpose**: Collect user feedback on Agent responses to track quality and identify improvement areas.

**Data Structure** (localStorage key: `agent_badcases`):
```javascript
{
  id: "badcase-1234567890",
  timestamp: 1719000000000,
  message_index: 3,
  message_text: "我已识别为「签名排查」...",
  type: "bug" | "positive" | "negative",
  comment: "appid 没有提取出来",  // For bug reports
  context: {
    task_type: "signature_debug",
    fields: { error_code: "SIGN_INVALID" },
    status: "needs_clarification"
  }
}
```

**UI Components**:
- **Feedback buttons** (hover on Agent messages): 👍 有帮助 / 👎 没帮助 / 🐛 报告问题
- **Badcase modal**: Problem type selection + detailed description
- **Storage**: Max 100 feedback entries in localStorage

**Core Functions**:
- `submitFeedback(index, type)` - Quick positive/negative feedback
- `openBadcaseModal(index)` / `closeBadcaseModal()` - Modal management
- `submitBadcaseReport()` - Submit detailed bug report with context snapshot
- `saveBadcaseFeedback()` / `loadBadcaseFeedbacks()` - Persistence

**Problem Types**:
- `wrong_intent` - Intent recognition error
- `missing_field` - Field extraction error
- `wrong_answer` - Inaccurate response
- `hallucination` - Fabricated information
- `other` - Other issues

### Version Evolution (V0-V7)

All versions embedded in `web/index.html` via `versions` array:
- V0: Black-box LLM response
- V1: Intent recognition
- V2: Schema validation + clarification
- V3: Skill routing
- V4: Document retrieval (RAG)
- V5: Tool calling
- V6: Agent Loop (Observe-Think-Act)
- V7: Security boundaries + audit

**Version Comparison Mode**: Users can select scenarios (brief/complete/custom) and switch versions to see capability differences.

## Code Structure

```
web/index.html    - Single-file SPA (~7300 lines)
├─ Styles         - CSS-in-HTML, dark theme, responsive
├─ HTML           - Tabs: Agent Chat / Version Experience / Agent Flow / Data Analytics
├─ JavaScript     - Core Agent logic
│  ├─ State management (conversation, turns, memory)
│  ├─ Intent recognition & field extraction
│  ├─ Schema validation & Skill routing
│  ├─ Short-term memory (Session/Turn/Field Memory)
│  ├─ Long-term memory (TF-IDF similarity search)
│  ├─ Badcase feedback (👍👎🐛 buttons)
│  ├─ Version implementations (V0-V7)
│  ├─ UI rendering (chat, session board, flow diagram)
│  └─ LLM integration (via proxy)
web/proxy.py      - CORS-bypassing proxy for LLM API
web/knowledge.js  - Embedded API documentation knowledge base
docs/             - Design documentation (~17 files)
├─ memory-system-design.md        - Short-term memory architecture
├─ schema-skill-design.md         - Schema validation & Skill routing
├─ phase1-completion-summary.md   - localStorage persistence implementation
└─ flow-diagram-update-summary.md - Flow diagram updates
```

## Key Design Patterns

### Field Extraction (Regex-based)
```javascript
fields = {
  api_path: firstMatch(/(?:^|[\s，,])((?:\/[A-Za-z0-9_-]+){2,})/, message),
  appid: firstMatch(/(?:appid|app_id)\s*[=:：]\s*([A-Za-z0-9_\-]+)/i, message),
  error_code: firstMatch(/(?:错误码|error_code)\s*[=:：]\s*([A-Z0-9_\-]+)/i, message),
  // ...
}
```

### Security Boundaries
```javascript
// Detect sensitive information
if (message.includes("appsecret") || message.includes("密钥")) {
  security_flags.push("contains_appsecret");
}

// Block execution in validate()
if (draft.security_flags.includes("contains_appsecret")) {
  return { status: "blocked", blocked_reasons: [...] };
}
```

### Multi-turn Context Merging
```javascript
// Apply field memory from previous turns
function applyConversationContext(draft) {
  const merged = {
    ...(state.conversation.memory.fields || {}),  // Previous fields
    ...draft.fields                                // New fields
  };
  return merged;
}
```

## Modifying the Demo

### Adding a New Task Type

1. **Add to intent recognition** (`detectTask()`):
```javascript
hits = {
  signature_debug: hitCount(message, ["签名", "SIGN_INVALID", ...]),
  your_new_task: hitCount(message, ["your", "keywords"]),
}
```

2. **Define required fields** (`requiredFields` object):
```javascript
const requiredFields = {
  your_new_task: ["field1", "field2"],
}
```

3. **Add field extraction patterns** (`extractTask()`):
```javascript
fields = {
  field1: firstMatch(/pattern1/, message),
  field2: firstMatch(/pattern2/, message),
}
```

4. **Create Skill route** (`skills` object):
```javascript
const skills = {
  your_new_task: "your_new_task/SKILL.md",
}
```

5. **Add task label** (`taskLabel()` function):
```javascript
function taskLabel(taskType) {
  return {
    your_new_task: "新任务类型",
    // ...
  }[taskType] || taskType;
}
```

### Updating LLM Configuration

Edit `web/proxy.py`:
```python
LLM_ENDPOINT = "https://your-api.com/v1/chat/completions"
LLM_KEY = "your-api-key"
```

Then restart the proxy server.

### Modifying Memory System

**Change TTL**: Modify `MAX_AGE` in `loadSession()`:
```javascript
const MAX_AGE = 24 * 60 * 60 * 1000; // 24 hours → change value
```

**Change Turn Retention**: Modify slice parameter in `commitConversationTurn()`:
```javascript
state.conversation.turns = turns.concat(turn).slice(-20); // Keep last 20 → change value
```

## Important Constraints

### Single-file Architecture
`web/index.html` is intentionally monolithic for demo portability. When editing:
- Preserve the `<script>` tag structure
- Keep CSS in `<style>` block
- Maintain variable scoping (`const` at top level)

### Memory System Terminology
Use precise terms defined in `docs/memory-system-design.md`:
- Session (not conversation/workspace)
- Turn (not message/round)
- Task Context (not active task)
- Field Memory (not cache/collected data)

### Security
- Never log sensitive fields (appsecret, credentials) to console
- Always check `security_flags` before LLM calls
- Keep `validate()` security checks as first priority

### Schema Validation
- Required fields must match Skill needs
- Validation status must be one of: `executable`, `needs_clarification`, `blocked`
- Missing field clarification must be specific (not generic "provide more info")

## Testing Changes

1. Make changes to `web/index.html` or `web/proxy.py`
2. Refresh browser (Ctrl+R / Cmd+R)
3. Test in Agent Chat mode with sample inputs:
   - "你们接口签名失败" (should trigger needs_clarification)
   - "appid=app_001，错误码=SIGN_INVALID，接口=/open/order，签名前字符串=xxx，时间=2026-06-15 10:00" (should be executable)
   - "我想要 appsecret" (should trigger blocked status)
4. Check Session Board for memory persistence (refresh page, verify restoration)
5. Test Badcase feedback: hover on Agent messages, click 👍👎🐛 buttons
6. Test Long-term memory: complete a task, ask a similar question, verify historical cases appear in System Prompt
7. Use browser DevTools Console for `[Memory]` / `[Badcase]` / `[Long-term Memory]` logs

## Current Feature Status (Post-Restoration)

✅ **Fully Implemented**:
- localStorage persistence (24h TTL, 20-turn history)
- Session Board optimization (terminology: Short-term Memory, Task Context, Field Memory)
- Field editing/deletion buttons (✏️ 🗑️)
- Reset session button
- Badcase feedback system (👍👎🐛 buttons, modal with 5 problem types, max 100 entries)
- Long-term memory (TF-IDF similarity search, max 100 historical tasks, 30-day decay)
- Architecture diagram detailed explanation modules (3 cards: Memory System / Schema Validation / Skill SOP)
- Toast notifications for user actions

## Documentation

Detailed design docs in `docs/`:
- **memory-system-design.md**: Short-term memory architecture, terminology, data structures
- **long-term-memory-design.md**: TF-IDF similarity search, historical task storage (max 100)
- **simple-long-term-memory-implementation.md**: Long-term memory implementation details
- **badcase-handling-design.md**: Feedback collection design and data structure
- **badcase-implementation-summary.md**: Badcase UI components (👍👎🐛 buttons, modal)
- **schema-skill-design.md**: Why Schema validation exists, how Skill routing works, source of Skills
- **phase1-completion-summary.md**: localStorage implementation, field editing, session reset
- **flow-diagram-update-summary.md**: Agent implementation flow diagram updates
- **flow-diagram-optimization-implementation.md**: Flow diagram terminology and layout optimization
