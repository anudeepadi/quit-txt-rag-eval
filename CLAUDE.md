# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QuitTxt Protocol Testing Application - A system for testing protocol-guided AI conversations for smoking cessation support using Google Gemini API, FastAPI backend, and Streamlit frontend.

**Core Purpose**: Enable testing and refinement of how an AI assistant follows a structured smoking cessation protocol when responding to user messages, with side-by-side comparison capabilities.

## Architecture

Three-tier architecture:
- **Frontend**: Streamlit UI (`streamlit_app.py`) on port 8501
- **Backend**: FastAPI server (`api_server.py`) on port 8000
- **Protocol Engine**: Context extraction system (`protocol_manager.py`)

### Request Flow

```
User Message → Streamlit → FastAPI → Protocol Manager → Gemini API → Response
                                    ↓
                            Relevance scoring of 315+ protocol sections
                            Top N sections added as context
```

### Key Integration Points

1. **Protocol Context Extraction** (`protocol_manager.py`):
   - Parses protocol into sections based on headers (all caps or colon-ending lines)
   - Scores relevance using keyword matching (2 pts), topic matching (1 pt), title matching (3 pts)
   - Returns top N sections (configurable 1-5, default 3) limited to 500 chars each
   - Maintains keyword_map for 10 topics: craving, motivation, support, relapse, withdrawal, stress, health, trigger, strategy, progress

2. **Conversation History Management**:
   - Last 5 messages sent to API to maintain context
   - History stored in session state on Streamlit side
   - Each message has role ('user'/'assistant'), content, and optional protocol_context

3. **Prompt Construction** (`api_server.py` lines 122-149):
   - System prompt defines counselor role
   - Protocol context inserted after system prompt
   - History appended in "ROLE: content" format
   - Current message added last

## Development Commands

### Start Servers

**Quick start** (recommended):
```bash
./start.sh
```
This script starts both API server and Streamlit app, handles port cleanup, and waits for health checks.

**Manual start** (for debugging):
```bash
# Terminal 1 - API Server
python api_server.py

# Terminal 2 - Streamlit
streamlit run streamlit_app.py
```

### Testing

**System verification**:
```bash
python test_setup.py
```
Tests: imports, environment config, protocol loading, protocol manager, Gemini API connection

**API health check**:
```bash
curl http://localhost:8000/health
```

**Direct API testing**:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I am having a craving", "conversation_history": [], "use_protocol": true, "max_protocol_sections": 3}'
```

**Interactive API docs**:
Open http://localhost:8000/docs for FastAPI Swagger UI

## Configuration & Environment

### Required Environment Variables
- `GOOGLE_API_KEY`: Google Gemini API key (stored in `.env`)

### Current Gemini Model
**IMPORTANT**: The code uses `gemini-2.0-flash-exp` (as of Oct 2025). If model errors occur:
1. Check available models: `curl -H "x-goog-api-key: $GOOGLE_API_KEY" https://generativelanguage.googleapis.com/v1beta/models`
2. Update model name in THREE places in `api_server.py`:
   - Line ~39: `genai.GenerativeModel()` call
   - Line ~61: `ChatResponse` model field default
   - Line ~157: Response object creation

Free tier limits: 10 req/min, 250 req/day, 250K tokens/min

## Key Customization Points

### Adjust Protocol Context
**Section character limit** (`protocol_manager.py:122`):
```python
context += f"{section.content[:500]}..."  # Change 500
```

**Add keyword mappings** (`protocol_manager.py:91-102`):
```python
self.keyword_map = {
    'new_topic': ['keyword1', 'keyword2'],
    # ...
}
```

### Modify AI Personality
**System prompt** (`api_server.py:123-135`):
```python
system_prompt = """You are a compassionate..."""
```

### Change Context Limits
**Conversation history** (`api_server.py:145`):
```python
for msg in request.conversation_history[-5:]  # Change 5
```

## Common Issues

### Model Not Found Error
**Symptom**: `404 models/gemini-X is not found`
**Fix**: Update model name in api_server.py (see Configuration section above)

### Streamlit KeyError: 'response'
**Symptom**: Chat fails with KeyError accessing response['response']
**Cause**: API returned error dict with 'detail' instead of 'response'
**Fix**: Error handling added in streamlit_app.py lines 99-101 and 122-124 to check status_code

### Text Visibility Issues
**Symptom**: Light text on light background in chat
**Fix**: CSS includes dark text color (#1F2937) for .chat-message class

### No Relevant Context
**Solutions**:
- Lower relevance threshold
- Add keywords to keyword_map
- Increase max_protocol_sections
- Check protocol_document.txt loaded correctly

## File Responsibilities

- **api_server.py**: FastAPI endpoints (/health, /protocol/info, /chat, /chat/compare), Gemini integration, prompt construction
- **streamlit_app.py**: UI with 3 tabs (Chat, Compare, Scenarios), session state, API client calls, CSS styling
- **protocol_manager.py**: Section parsing, keyword extraction, relevance scoring, context assembly
- **protocol_document.txt**: 142KB smoking cessation protocol (315+ sections)
- **start.sh**: Production startup script with health checks and port cleanup
- **test_setup.py**: Development verification tool
- **.env**: API credentials (not in git)

## Testing Protocol Changes

When modifying protocol or scoring logic:
1. Test with pre-defined scenarios in UI (Scenarios tab)
2. Use Compare tab to verify protocol vs non-protocol differences
3. Check protocol context used (toggle "Show Protocol Context")
4. Run test_setup.py to ensure no regressions
5. Monitor relevance scores in protocol_manager for debugging

## Dependencies

Critical packages (see requirements.txt):
- fastapi==0.109.0 (backend framework)
- streamlit==1.31.0 (UI framework)
- google-generativeai==0.3.2 (Gemini SDK)
- python-dotenv==1.0.0 (env config)

When updating packages, retest with test_setup.py and verify Gemini API compatibility.
