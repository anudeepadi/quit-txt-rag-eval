# QuitTxt Protocol Testing Application

A complete testing system for protocol-guided AI conversations using Google Gemini API, FastAPI, and Streamlit.

## 🎯 Purpose

This application allows you to test how well an AI assistant can follow the QuitTxt smoking cessation protocol when responding to user messages. It provides:

- **Interactive Chat Interface** - Test real conversations with protocol-guided AI
- **Response Comparison** - Compare AI responses with and without protocol context
- **Pre-defined Scenarios** - Test common smoking cessation situations
- **Protocol Context Visibility** - See exactly which protocol sections are being used

## 🏗️ Architecture

```
┌─────────────────┐
│  Streamlit UI   │  (Port 8501)
│  (Frontend)     │
└────────┬────────┘
         │
         │ HTTP Requests
         │
┌────────▼────────┐
│  FastAPI Server │  (Port 8000)
│  (Backend)      │
└────────┬────────┘
         │
         ├──► Protocol Manager (Context Extraction)
         │
         └──► Google Gemini API (AI Responses)
```

## 📋 Prerequisites

- Python 3.8+
- Google API Key (already configured in .env)
- Protocol document (already extracted)

## 🚀 Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt --break-system-packages
```

2. **Verify Setup**
```bash
ls -la
# Should see: api_server.py, streamlit_app.py, protocol_manager.py, protocol_document.txt, .env
```

## 🎮 Usage

### Starting the Application

You need to run TWO terminals:

**Terminal 1 - Start the API Server:**
```bash
cd /home/claude/quittxt_protocol_test
python api_server.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Start the Streamlit App:**
```bash
cd /home/claude/quittxt_protocol_test
streamlit run streamlit_app.py
```

The Streamlit app will open in your browser at http://localhost:8501

### Using the Application

#### 1. Chat Tab
- Type messages as if you were a user trying to quit smoking
- The AI will respond using protocol-guided context
- View the protocol sections used in each response
- Build a conversation history

Example messages to try:
- "I'm having a craving right now"
- "I failed and smoked today"
- "Why should I quit smoking?"
- "Help me deal with stress without cigarettes"

#### 2. Compare Responses Tab
- Enter a message to see two responses:
  - One WITH protocol context
  - One WITHOUT protocol context
- Compare how the protocol improves responses

#### 3. Test Scenarios Tab
- Pre-loaded common smoking cessation scenarios
- Click any button to instantly test that scenario
- Includes situations like:
  - Craving emergencies
  - Relapse confessions
  - Motivation requests
  - Withdrawal symptoms
  - Social pressure

### Configuration Options

In the sidebar, you can adjust:

- **Use Protocol Context**: Toggle protocol-guided responses on/off
- **Max Protocol Sections**: How many relevant sections to include (1-5)
- **Show Protocol Context**: Display the actual protocol text used
- **Clear Conversation**: Reset the chat history

## 🧪 API Testing (Without UI)

You can also test the API directly:

### Health Check
```bash
curl http://localhost:8000/health
```

### Protocol Info
```bash
curl http://localhost:8000/protocol/info
```

### Send a Chat Message
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am having a craving",
    "conversation_history": [],
    "use_protocol": true,
    "max_protocol_sections": 3
  }'
```

### Compare Responses
```bash
curl -X POST http://localhost:8000/chat/compare \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am having a craving",
    "conversation_history": [],
    "max_protocol_sections": 3
  }'
```

## 📊 How It Works

### Protocol Context Manager

The `ProtocolContextManager` class:

1. **Loads** the protocol document
2. **Parses** it into logical sections
3. **Extracts** keywords from each section
4. **Scores** sections based on user message relevance
5. **Returns** the most relevant sections as context

### Relevance Scoring

Messages are scored based on:
- Keyword matches (2 points each)
- Topic terms (1 point each)
- Title relevance (3 points)

Example: "I'm having a craving" would match:
- Keyword: "craving" (+2)
- Topic terms: "craving", "urge" (+2)
- Sections with "craving" in title (+3)

### AI Integration

The FastAPI server:

1. Receives user message
2. Gets relevant protocol sections
3. Constructs prompt with:
   - System instructions
   - Protocol context
   - Conversation history
   - User message
4. Sends to Google Gemini API
5. Returns response

## 🔧 Customization

### Modify Protocol Sections

Edit `protocol_manager.py`:

```python
# Add more keyword mappings
self.keyword_map = {
    'new_topic': ['keyword1', 'keyword2'],
    # ...
}
```

### Adjust AI Behavior

Edit `api_server.py`:

```python
system_prompt = """Your custom instructions here..."""
```

### Change Max Context Length

In `protocol_manager.py`:

```python
# Limit section length
context += f"{section.content[:500]}..."  # Change 500 to desired length
```

## 📱 Integration with Flutter App

Once tested, integrate into your Flutter app:

### 1. Create Flutter Service

```dart
// lib/services/protocol_api_service.dart
class ProtocolApiService {
  final String apiUrl = 'YOUR_DEPLOYED_API_URL';
  
  Future<String> sendMessage(String message, List<ChatMessage> history) async {
    final response = await http.post(
      Uri.parse('$apiUrl/chat'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'message': message,
        'conversation_history': history,
        'use_protocol': true,
      }),
    );
    
    final data = jsonDecode(response.body);
    return data['response'];
  }
}
```

### 2. Update DashChatProvider

```dart
// lib/providers/dash_chat_provider.dart
class DashChatProvider extends ChangeNotifier {
  final ProtocolApiService _apiService = ProtocolApiService();
  
  Future<void> sendUserMessage(String message) async {
    final response = await _apiService.sendMessage(
      message,
      _messageHistory,
    );
    
    _addMessage(ChatMessage(
      text: response,
      user: assistantUser,
      createdAt: DateTime.now(),
    ));
    
    notifyListeners();
  }
}
```

### 3. Deploy API

Deploy the FastAPI server to:
- Google Cloud Run
- AWS Lambda
- Heroku
- Your own server

Update the `apiUrl` in your Flutter app accordingly.

## 🐛 Troubleshooting

### API Not Starting

**Error**: `GOOGLE_API_KEY not found`
**Solution**: Verify `.env` file exists and contains the API key

### Protocol Not Loading

**Error**: `FileNotFoundError: protocol_document.txt`
**Solution**: Ensure the protocol was extracted correctly:
```bash
ls -la protocol_document.txt
```

### Streamlit Can't Connect to API

**Error**: "API Not Connected" in sidebar
**Solution**: Make sure the API server is running first:
```bash
# Terminal 1
python api_server.py
```

### No Protocol Context Showing

**Solution**: 
1. Check "Show Protocol Context" in sidebar
2. Ensure "Use Protocol Context" is enabled
3. Try a message with clear keywords like "craving" or "quit"

## 📈 Performance Considerations

- **Context Length**: Protocol sections are limited to 500 chars each
- **History Limit**: Only last 5 messages sent to API
- **Timeout**: 30 seconds for API responses
- **Max Sections**: Default 3, adjustable 1-5

## 🔐 Security Notes

- API key is stored in `.env` (do not commit to git)
- For production, use environment variables
- Add authentication to API endpoints
- Validate and sanitize all user inputs

## 🔬 RAG Configuration Evaluation

**NEW** (Nov 2025): The system now supports evaluation of 4 different RAG configurations for research comparison:

1. **Baseline Gemini** - No RAG
2. **QA Only** - Curated knowledge base
3. **Protocol + QA** - Hybrid approach (default)
4. **Web RAG** - Vertex AI Search with web sources

### Quick Start for Evaluation

```bash
# Test your setup
python test_rag_setup.py

# Run full evaluation
python evaluate_rag_configurations.py

# Review results
open evaluation_summary.md
```

**Documentation**:
- 📘 **[QUICKSTART_EVALUATION.md](QUICKSTART_EVALUATION.md)** - Step-by-step evaluation guide
- 📗 **[VERTEX_AI_INTEGRATION_GUIDE.md](VERTEX_AI_INTEGRATION_GUIDE.md)** - Complete Vertex AI setup
- 📕 **[INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)** - Implementation overview

## 📝 Next Steps

1. **Test thoroughly** with various scenarios
2. **Refine protocol sections** based on results
3. **Adjust relevance scoring** if needed
4. **Deploy API** to production environment
5. **Integrate with Flutter app**
6. **Add analytics** to track effectiveness

## 🤝 Support

For issues or questions:
1. Check this README
2. Review code comments
3. Test with curl commands
4. Check API logs in terminal

---

**Built for QuitTxt Research Study**
*Helping people quit smoking through AI-powered, protocol-guided support*
# laughing-memory
