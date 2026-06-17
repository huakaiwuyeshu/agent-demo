# V1 Intent Hybrid Architecture

## Demo Positioning

V1 shows how an API Agent turns one user message into a structured task draft. It is not a final Q&A agent yet. The page focuses on making intent recognition, slot extraction, session state, and retrieval routing visible enough for product demos.

## Runtime Flow

```text
User input
  -> Scope gate
  -> Rule-first intent recognition
  -> Semantic vector-style fallback
  -> LLM fallback decision
  -> Slot extraction
  -> Validation
  -> Session / task state update
  -> Retrieval routing preview
```

## Hybrid Recognition Layers

### 1. Rule First

Rules run first because they are stable, fast, and easy to explain. V1 checks business keywords, API paths, error codes, and common API terms.

Main file:

```text
web/index.html
  intentCatalog
  scopeSignals
  evaluateInputGate(...)
```

Typical examples:

```text
签名 / 验签 / SIGN_INVALID -> signature_debug
回调 / callback / 超时 -> callback_debug
字段 / 含义 / detailinfo -> api_field_qa
```

### 2. Vector Fallback

The current demo uses local semantic examples to simulate vector matching. This is intentionally offline and stable for demos. It does not call an external embedding service yet.

Main file:

```text
web/index.html
  semanticIntentExamples
  rankSemanticIntents(...)
  textSimilarity(...)
```

Future replacement:

```text
semanticIntentExamples -> intent example index
textSimilarity(...) -> embedding cosine similarity
```

### 3. LLM Fallback

The current demo uses a deterministic fallback simulator. It represents where a real LLM classifier would sit after rules and semantic retrieval are both low-confidence.

Main file:

```text
web/index.html
  llmFallbackHints
  simulateLlmFallback(...)
```

Future replacement:

```text
simulateLlmFallback(...) -> real model call with JSON schema output
```

The fallback should still return traceable fields:

```json
{
  "intent": "signature_debug",
  "confidence": 0.66,
  "reason": "why this intent was selected"
}
```

## Session And Task State

V1 now keeps a lightweight client-side session. This lets the demo show how a second user message can supplement the first one.

Main file:

```text
web/index.html
  state.conversation
  applyConversationContext(...)
  buildSessionSnapshot(...)
  commitConversationTurn(...)
  renderSessionBoard(...)
```

Example:

```text
Turn 1: 你们接口签名失败，帮忙看下
V1: task_type=signature_debug, status=waiting_for_user

Turn 2: 接口=/open/order/create，appid=app_demo_001，错误码=SIGN_INVALID
V1: keeps the signature_debug task and merges new fields into the active task
```

## Retrieval Routing

The retrieval path is still separate from intent recognition:

```text
searchDocs(...)       -> local exported package
searchRemoteDocs(...) -> GitHub llm-wiki index
```

V1 shows this routing in the bottom graph. Local package is preferred; GitHub llm-wiki is queried only when the local package misses.

## What Is Real Today

Implemented in the page:

```text
Rule-first recognition
Semantic example fallback
Deterministic LLM fallback simulator
Slot extraction
Validation and clarification state
Session memory and active task state
Local package retrieval
Remote llm-wiki retrieval fallback
White-box visual trace
```

Not implemented as external infrastructure yet:

```text
Real embedding model
Persistent vector database
Real LLM API call for intent classification
Server-side session storage
```

