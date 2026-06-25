# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**API 接入 Agent 演示系统** - A progressive demonstration of Agent capabilities from simple Q&A (V0) to a full business Agent (V7) with multi-turn conversations, document retrieval, and tool calling. Uses API troubleshooting scenarios (signature failures, callback issues) to showcase Agent architecture evolution.

**Core Implementation**: Single-page web application (`web/index.html`, ~9500 lines) with embedded JavaScript. No framework dependencies—pure hand-written Agent implementation for educational transparency.

## Running the Demo

### Web Demo (Primary)

```bash
# Quick launch (Windows)
start_services.bat

# Manual launch
python web/proxy.py                          # Port 8081 (LLM API proxy)
python -m http.server 8080 --directory web   # Port 8080 (web server)
# Visit http://localhost:8080/
```

### CLI Demo (Version Comparison)

```bash
# Compare versions
python app.py --version v0 --scenario brief   # V0: Black-box LLM
python app.py --version v2 --scenario brief   # V2: Schema validation
python app.py --version v6 --scenario brief   # V6: Agent Loop
python app.py --version all --scenario complete

# Custom input
python app.py --version v3 --message "你们 /open/order 接口签名失败，appid=xxx"
```

**Stop services**: `stop_services.bat`

**LLM Configuration**: Edit `web/proxy.py` → `LLM_ENDPOINT`, `LLM_KEY`

## Architecture: Hybrid Intent Recognition + ReAct Fallback

The core innovation is **Rule + Vector + LLM fallback** (Layers 1-3) for intent recognition, with **ReAct autonomous loop** (Layer 4) as final fallback. Optimized for token efficiency and deterministic behavior when possible.

### Layer 1: Rule-First (Deterministic)

```javascript
// web/index.html: intentCatalog
signature_debug: { keywords: [
  { word: "签名", weight: 2 },
  { word: "SIGN_INVALID", weight: 3 },
  { word: "验签", weight: 2 }
]}
```

- **Trigger**: Rule score >= 3 OR strong business keywords >= 2
- **Confidence**: 0.42 + score × 0.07 (max 0.92)
- **Cost**: 0 tokens, <10ms
- **Use case**: Clear keyword matches ("签名失败", "SIGN_INVALID")

### Layer 2: Vector Fallback (Semantic)

```javascript
// web/index.html: semanticIntentExamples
signature_debug: [
  "你们接口一直签名失败",
  "验签不通过怎么办",
  "鉴权失败"
]

// Local token overlap similarity (not real embeddings)
textSimilarity(userInput, examples) >= 0.42
```

- **Trigger**: Layer 1 fails AND semantic similarity >= 42%
- **Confidence**: 0.38 + score × 0.55 (max 0.88)
- **Cost**: 0 tokens (local computation)
- **Use case**: Paraphrased expressions

### Layer 3: LLM Fallback (Heuristic)

```javascript
// web/index.html: simulateLlmFallback
// NOTE: Currently simulated with rules, not real LLM call
llmFallbackHints = [
  { intent: "api_onboarding", 
    patterns: ["怎么开始", "准备上线", "对接流程"],
    reason: "LLM 兜底把'开始接入'归并为新 API 接入" }
]
```

- **Trigger**: Layers 1-2 fail AND has business signals (API path, error code, scope keywords)
- **Confidence**: 0.55 - 0.68
- **Cost**: 0 tokens (simulated, but represents where real LLM would sit)
- **Use case**: Ambiguous expressions with contextual clues

### Layer 4: ReAct Autonomous Loop (NEW - Added 2026-06)

**Location**: `web/index.html:8998-9220` (`runReActLoop`)

```javascript
// Triggered when out_of_scope BUT strongBusinessSignal detected
if (validation.status === "out_of_scope" && strongBusinessSignal) {
  const reactResult = await runReActLoop(text, draft, docs);
  reply = reactResult.answer;
}
```

**ReAct Tools** (`defineReActTools`):
- `search_knowledge` - Query docs/FAQ/error codes
- `extract_fields` - Parse structured data from user input
- `check_signature_order` - Verify parameter sorting

**Loop Structure**:
```
Max 5 iterations:
  LLM → Thought: [reasoning]
      → Action: [tool_name]
      → Action Input: [JSON args]
  System → Observation: [tool result]
  
  OR
  
  LLM → Thought: [summary]
      → Final Answer: [response to user]
```

**Anti-loop Guards**:
- Track `toolCallHistory` with `${tool}:${args}` signatures
- If same call appears ≥2 times → inject warning observation, skip execution
- Forces LLM to try different approach or admit failure

**Cost Model**:
- Fast path (Layers 1-3): 1 LLM call, ~1-2k tokens
- ReAct fallback: 3-5 LLM calls, ~5-10k tokens
- Triggers ~5-10% of time (edge cases only)

**When It Fires**:
- ✅ Mixed-intent queries: "/api/path 为啥接不到游戏账号" (API question + business issue)
- ✅ New API patterns: "/api/unknown/endpoint 报错了" (not in rule base)
- ✅ Unusual phrasing that bypasses rules but has clear business signal
- ❌ Pure out-of-scope: "今天天气怎么样" (no API/path/error_code) → rejection message

**Decision Flow**:
```javascript
// web/index.html:5607-5617
User Input
  ↓
Layer 1 (Rule) ────────┐ score ≥ 3 → Intent recognized
  ↓ fail               │
Layer 2 (Vector) ──────┤ similarity ≥ 0.42 → Intent recognized  
  ↓ fail               │
Layer 3 (LLM Hints) ───┤ matched pattern → Intent recognized
  ↓ out_of_scope       │
Check strongBusinessSignal?
  ├─ Yes → Layer 4 (ReAct) → LLM autonomous loop → Final Answer
  └─ No  → Rejection message

if (layers[0].passed) return layers[0];      // Rule優先
else if (layers[1].passed) return layers[1]; // Vector補位
else if (layers[2].passed) return layers[2]; // LLM兜底
else if (strongBusinessSignal) runReActLoop(); // ReAct救援
else return "out_of_scope";
```

**Why This Design**:
- Token efficiency: Intent recognition uses 0 tokens
- Explainability: Every decision has traceable reasoning
- Predictability: Same input → same intent (no LLM variance)
- Production-ready: Suitable for fixed-intent scenarios (5-10 task types)

## Agent Workflow Pipeline

```
User Input
  ↓
[evaluateInputGate] → Three-layer intent recognition
  ↓
[extractTask] → Regex-based field extraction (appid, error_code, api_path...)
  ↓
[applyConversationContext] → Merge with Field Memory from previous turns
  ↓
[validate] → Schema validation
  ├─ blocked → Security boundary (contains appsecret)
  ├─ needs_clarification → Missing required fields
  └─ executable → All fields present
  ↓
[Skill Routing] → Load SOP for task_type
  ↓
[buildSystemPrompt] → Assemble: Base + SOP + Long-term Memory + Knowledge + Tools
  ↓
[callLLM] → LLM handles understanding + expression only
  ↓
[commitConversationTurn] → Save to Session + localStorage
```

**Key Principle**: Code handles structure (intent, schema, routing), LLM handles semantics (understanding, expression).

## Memory System

### Short-term Memory (Session-scoped, 24h TTL)

**Terminology** (use consistently):
- **Session**: User lifecycle (page open → close/reset)
- **Turn**: One user input + Agent response (max 20 stored, 5 displayed)
- **Task Context**: Current task snapshot (task_type, status, fields)
- **Field Memory**: Extracted fields accumulated within Session (append-only)

**Storage**: `localStorage` key `agent_demo_session`

**Functions**:
- `loadSession()` / `saveSession()` - Persistence with 24h TTL check
- `applyConversationContext(draft)` - Merge new fields with Field Memory
- `commitConversationTurn(turn)` - Append turn, auto-save, keep last 20
- `resetConversation()` - Clear state + localStorage

### Long-term Memory (Cross-session, unlimited TTL)

**Storage**: `localStorage` key `agent_long_term_memory`, max 100 historical tasks

**Retrieval Algorithm** (TF-IDF + time decay):
```javascript
score = taskTypeMatch(50) + fieldOverlap(10×count) + textSimilarity(5×tokens)
finalScore = score × 0.5^(days/30)  // 30-day half-life
```

**Functions**:
- `addHistoricalTask(task)` - Save completed task with resolution notes
- `searchSimilarTasks(currentTask, topK=3)` - Retrieve similar cases
- `injectLongTermMemoryToPrompt(prompt, task)` - Inject top 3 as few-shot examples

**UI**: Session Board (bottom panel) - view/edit/export/clear memory

## Schema Validation & Skill Routing

**Schema Definition**:
```javascript
// web/index.html: requiredFields
signature_debug: ["api_path", "appid", "raw_sign_string", "error_code", "request_time"]
callback_debug: ["callback_url", "order_id", "trigger_action", "request_time"]
api_field_qa: ["field_name"]
volume_analysis: ["analysis_dimension", "analysis_scope"]
api_onboarding: ["target_api"]
```

**Validation States**:
- `executable` → All required fields present → Route to Skill
- `needs_clarification` → Missing fields → Precise追问 (不让 LLM 硬答)
- `blocked` → Security boundary → Refuse execution

**Skill Routing**:
```javascript
// web/index.html: skills
skills = {
  signature_debug: "signature_debug/SKILL.md",  // Load SOP
  callback_debug: "callback_debug/SKILL.md",
  credential_request: "human_review_gate"        // Special: manual review
}
```

**Why Schema First**:
1. Ensures tools are executable (missing appid → tool fails)
2. Precise clarification (not generic "provide more info")
3. Avoids wasted LLM calls on incomplete data

## System Prompt Architecture

**Location**: `web/index.html:7632-7697` (`buildSystemPrompt`)

**Structure** (modular injection):
```
[Base Role]
你是 API 技术支持 Agent。

[Current Task State]
- 类型: signature_debug
- 状态: executable
- 已有字段: appid=xxx, error_code=SIGN_INVALID
- 缺失字段: 无

[Dynamic Execution Flow] ← Based on validation.status
needs_clarification:
  1. 分析缺失字段
  2. 追问(≤3个问题)
  3. 解释为什么需要
  4. 不要硬答

executable:
  1. 检查工具执行结果
  2. 基于知识库回答并引用
  3. 按 SOP 排查
  4. 用数据支撑结论
  5. 无法定位就说明原因

[Skill SOP] ← If task_type recognized
## 签名失败排查 SOP
排查步骤:
1. 检查参数按 ASCII 升序排列
2. 检查签名前字符串...

[Long-term Memory] ← Top 3 similar historical cases
## 历史相似案例
- task-123: signature_debug, 参数未按字典序排序

[Knowledge Retrieval] ← If docs found
## 知识库检索结果
[文档片段1]
[文档片段2]

[Tool Results] ← If tools executed
## 工具执行结果
check_signature_order: fail - 当前顺序错误

[Hard Constraints]
- 绝不复述 appsecret
- 无依据说"文档未覆盖"
- 简洁直接，不寒暄
```

**Key Pattern**: Prompt adapts to validation status with explicit step-by-step instructions, not generic descriptions.

## Version Evolution (V0-V7)

| Version | Capability | Key Change |
|---------|-----------|-----------|
| V0 | Black-box LLM | Direct answer, generic responses |
| V1 | Intent recognition | Three-layer hybrid system |
| V2 | Schema validation | Precise clarification, no guessing |
| V3 | Skill routing | SOP injection based on task_type |
| V4 | Document retrieval | RAG (local → GitHub wiki → security gate) |
| V5 | Tool calling | Deterministic validation chain |
| V6 | Agent Loop | Observe → Think → Act → Observe → Answer |
| V7 | Security boundaries | appsecret detection, human review gate |

**Implementation**: All versions in `web/index.html` via `runVersion()` function and `src/versions/` for CLI.

## Code Structure

```
web/index.html (9220 lines, single-file SPA)
├─ Lines 5508-5771: evaluateInputGate (三层意图识别)
├─ Lines 5783-5850: extractTask (字段提取)
├─ Lines 3516-3544: validate (Schema 校验)
├─ Lines 7632-7697: buildSystemPrompt (动态 Prompt 组装)
├─ Lines 8354-8540: sendAgentMessage (主对话流程)
├─ Lines 4400-5100: Memory system (Session, Field Memory, Long-term)
├─ Lines 8998-9086: ReAct Layer 4 (defineReActTools, executeReActTool)
└─ Lines 9087-9220: runReActLoop (LLM autonomous loop)

web/proxy.py: CORS proxy (LLM_ENDPOINT, LLM_KEY)
web/knowledge.js: Embedded API docs for RAG

src/common/: CLI shared modules
├─ mock_llm.py: Regex-based intent + field extraction
├─ schemas.py: Task type definitions + required fields
├─ validator.py: Schema validation logic
└─ rag.py: Document retrieval (local → GitHub → security gate)

src/versions/: V0-V7 implementations (CLI)
├─ v2_validator_clarify.py (1KB)
├─ v6_agent_loop.py (3KB)
└─ v7_guardrails.py (4KB)

skills/: Business Skill SOPs
├─ signature_debug/SKILL.md
├─ callback_debug/SKILL.md
└─ api_field_qa/SKILL.md
```

## Adding a New Task Type

**5-step checklist**:

1. **Intent recognition** (`evaluateInputGate` → `intentCatalog`):
```javascript
your_task: { keywords: [{ word: "关键词", weight: 2 }] }
```

2. **Required fields** (`requiredFields`):
```javascript
your_task: ["field1", "field2"]
```

3. **Field extraction patterns** (`extractTask`):
```javascript
fields.field1 = firstMatch(/pattern1/, message);
```

4. **Skill SOP** (`skills` + create `skills/your_task/SKILL.md`):
```javascript
skills = { your_task: "your_task/SKILL.md" }
```

5. **Task label** (`taskLabel` function):
```javascript
your_task: "新任务类型"
```

## Testing Workflow

1. Edit `web/index.html` or `web/proxy.py`
2. Refresh browser (Ctrl+R)
3. Test in Agent Chat mode:
   - **Needs clarification**: "你们接口签名失败" → should ask for missing fields
   - **Executable**: "appid=app_001，错误码=SIGN_INVALID，接口=/open/order，签名前字符串=xxx，时间=2026-06-15 10:00"
   - **Blocked**: "我想要 appsecret" → should refuse
4. Check Session Board (memory persistence across refresh)
5. Check Console logs: `[Memory]`, `[Intent]`, `[Long-term Memory]`

## Important Constraints

### Single-file Architecture
`web/index.html` is intentionally monolithic for demo portability. When editing:
- Preserve `<script>` tag structure (avoid splitting JavaScript into external files)
- Keep CSS in `<style>` block
- Maintain global scope for demo functions (avoid ES modules)

### Memory Terminology
Use precise terms from `docs/memory-system-design.md`:
- **Session** (not conversation/workspace)
- **Turn** (not message/round)
- **Task Context** (not active task)
- **Field Memory** (not cache/collected data)

### Security Boundaries
```javascript
// web/index.html: extractTask
if (message.includes("appsecret")) {
  security_flags.push("contains_appsecret");
}

// validate() blocks execution
if (draft.security_flags.includes("contains_appsecret")) {
  return { status: "blocked", blocked_reasons: [...] };
}
```

Never log sensitive fields (appsecret, credentials) to console. Code-level blocking takes precedence over LLM instructions.

### Field Extraction Patterns
All regex-based, no LLM calls:
```javascript
api_path: /(?:^|[\s，,])((?:\/[A-Za-z0-9_-]+){2,})/
appid: /(?:appid|app_id)\s*[=:：]\s*([A-Za-z0-9_\-]+)/i
error_code: /(?:错误码|error_code)\s*[=:：]\s*([A-Z0-9_\-]+)/i
```

When adding new fields, follow same pattern: flexible separators (=:：), case-insensitive, capture group for value.

## Documentation

Key design docs in `docs/`:
- `memory-system-design.md` - Short-term memory architecture, terminology
- `v1-intent-hybrid-architecture.md` - Three-layer intent recognition system
- `schema-skill-design.md` - Why Schema validation exists, how Skill routing works
- `long-term-memory-design.md` - TF-IDF similarity search, time decay algorithm

## CLI vs Web Demo Differences

**CLI** (`app.py` + `src/versions/`):
- Stateless version comparison tool
- No memory system
- Simpler intent recognition (keyword-only, no three-layer)
- Educational: each version is separate `.py` file (easy to read)

**Web** (`web/index.html`):
- Full Agent with memory, multi-turn, badcase feedback
- Three-layer hybrid intent recognition
- Real-time LLM integration via proxy
- Production-like: single deployment artifact

Use CLI for technical training, Web for product demos and real usage.

## Context Compression

When `agentMessages > 10`, a two-layer compression system activates:

**Layer 1 (Always, 0 tokens)**: Local rule extraction from expired messages:
- Intent chain: `签名排查(第1-3轮) → 回调排查(第4-6轮)`
- Accumulated fields snapshot
- Agent conclusions (last 3, 80 chars each)
- User supplements containing field values

**Layer 2 (Optional, ~500 tokens)**: LLM refinement triggered when:
- `state.conversation.turns.length > 20` (auto)
- User enables "深度记忆" toggle in Session Board

Functions: `compressConversationContext()`, `compressWithLLM()`, `extractIntentChain()`

## Observability Tab

A dedicated "可观测性" tab records full decision traces for each user message:
- Each trace entry shows: timestamp, user input, final status, error summary
- Each step expands to: Input (full params), Output (full results), Reasoning, Decision
- ReAct iterations appear as `react-1`, `react-2`, etc.

Functions: `renderObservePanel()`, `renderObserveStep()`, `buildErrorSummary()`

## Knowledge Pipeline

Knowledge flows from llm-wiki → agent:

```bash
# In llm-wiki/projects/api-infra:
python notes/ingest/parse_api_endpoints.py      # Extract per-endpoint docs from 119-page PDF markdown
python notes/ingest/build_curated_outputs.py    # Build export package (merges detailed docs)

# In agent/:
python sync_knowledge.py                         # Sync to data/knowledge/ + web/knowledge.js
```

`parse_api_endpoints.py` extracts: endpoint path, description, request parameters (name/type/required/description), response examples.

`knowledge.js` structure: `window.AGENT_DEMO_KNOWLEDGE = { api_docs, faq, error_codes, sops }`

Knowledge retrieval uses `queryTerms()` which splits API paths into segments for fuzzy matching (e.g., `/api/zhwaihub/hao/search` → also searches `hao`, `search`, `hao/search`).

## Data Analysis Limitations

`volume_analysis` task type uses static Excel data (not real-time). The system:
- Requires `analysis_scope` field (time trend / channel / game / all) to prevent vague queries
- Injects `volume_analysis` SOP into system prompt warning LLM about static data
- Uses "数据集内" phrasing instead of "最近" when describing time ranges

## Deployment

**Netlify** (configured via `netlify.toml`):
- Publish directory: `web/`
- No build step required (static SPA)
- Auto-deploys on push to `main`

## Common Editing Pitfall

**Curly quote corruption**: The Edit tool sometimes converts ASCII `"` (U+0022) to Unicode curly quotes `"` (U+201C) / `"` (U+201D) when editing strings containing Chinese text. This breaks JavaScript parsing silently. After any edit involving Chinese-quoted strings, verify with:
```bash
node -e "const vm=require('vm'); const html=require('fs').readFileSync('web/index.html','utf-8'); const s=html.match(/<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/g).pop().replace(/<\/?script[^>]*>/g,''); new vm.Script(s)"
```
If it fails, use PowerShell byte-level replacement to fix curly quotes back to ASCII in the affected function block.
