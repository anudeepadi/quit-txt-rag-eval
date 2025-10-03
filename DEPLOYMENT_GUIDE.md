# 🚭 QuitTxt Protocol Testing System - Complete Setup Guide

## ✅ What's Been Created

Your complete testing system is ready! Here's what you have:

```
quittxt_protocol_test/
├── api_server.py              # FastAPI backend server
├── streamlit_app.py           # Streamlit frontend UI
├── protocol_manager.py        # Protocol context extraction
├── protocol_document.txt      # Your extracted protocol (142KB)
├── requirements.txt           # Python dependencies
├── .env                       # API key configuration
├── start.sh                   # Easy startup script
├── test_setup.py             # System verification
└── README.md                  # Detailed documentation
```

## 🎯 System Status

✅ **Protocol Document**: Loaded (142,243 characters, 315 sections)
✅ **Protocol Manager**: Working (10 keyword topics mapped)
✅ **Package Imports**: All dependencies installed
✅ **Environment Config**: API key configured
⚠️ **Gemini API**: SSL certificate issue in this environment

## 🚀 How to Use (Two Methods)

### Method 1: On Your Local Machine (RECOMMENDED)

Since the API has SSL issues in this environment, run it on your local machine:

#### Step 1: Copy Files to Your Computer

Copy the entire `/home/claude/quittxt_protocol_test` directory to your computer.

Or download individual files:
- api_server.py
- streamlit_app.py
- protocol_manager.py
- protocol_document.txt
- requirements.txt
- .env
- start.sh

#### Step 2: Install Dependencies

```bash
cd quittxt_protocol_test
pip install -r requirements.txt
```

#### Step 3: Verify Setup

```bash
python test_setup.py
```

You should see all tests pass.

#### Step 4: Start the System

**Easy Way (Linux/Mac):**
```bash
./start.sh
```

**Manual Way (All platforms):**

Terminal 1:
```bash
python api_server.py
```

Terminal 2:
```bash
streamlit run streamlit_app.py
```

#### Step 5: Open in Browser

Navigate to: **http://localhost:8501**

### Method 2: Docker Deployment (For Production)

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 8501

CMD ["sh", "start.sh"]
```

Build and run:
```bash
docker build -t quittxt-protocol-test .
docker run -p 8000:8000 -p 8501:8501 quittxt-protocol-test
```

## 📱 Using the Application

### 1. Interactive Chat

Test real conversations:

1. Type a message as if you're a user trying to quit smoking
2. The AI responds using protocol-guided context
3. View which protocol sections were used
4. Build a conversation history

**Example Messages:**
- "I'm having a really strong craving right now"
- "I smoked today after 2 weeks. I feel terrible."
- "Why should I quit smoking? I'm not motivated."
- "I'm so irritable since I quit. Is this normal?"

### 2. Compare Responses

See the difference protocol makes:

1. Enter a test message
2. Click "Compare Responses"
3. View side-by-side:
   - Response WITH protocol guidance
   - Response WITHOUT protocol guidance

**Try comparing:**
- "Help me deal with a craving"
- "I relapsed, what do I do?"
- "I need motivation to quit"

### 3. Test Scenarios

8 pre-defined scenarios ready to test:

- 🔥 Craving Emergency
- 😔 Relapse Confession
- 💪 Motivation Needed
- 😰 Withdrawal Symptoms
- 🎉 Success Celebration
- 🤔 Trigger Identification
- 👨‍👩‍👧 Social Pressure
- 📊 Progress Check

Click any button to instantly test that scenario.

## 🎛️ Configuration Options

### In the Sidebar:

**Use Protocol Context** (Default: ON)
- Toggle protocol guidance on/off
- Test AI with and without protocol

**Max Protocol Sections** (Default: 3)
- 1-5 sections
- More sections = more context but longer prompts

**Show Protocol Context** (Default: ON)
- Display the actual protocol text used
- See which sections are most relevant

**Clear Conversation**
- Reset chat history
- Start fresh conversation

## 🔌 API Endpoints

Once the API server is running, you can also test directly:

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "api_configured": true
}
```

### Get Protocol Info
```bash
curl http://localhost:8000/protocol/info
```

### Send Chat Message
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
    "message": "I need help quitting",
    "conversation_history": []
  }'
```

### Interactive API Documentation

Visit: **http://localhost:8000/docs**

FastAPI provides automatic interactive documentation where you can:
- See all endpoints
- Test API calls directly in browser
- View request/response schemas

## 📊 How the Protocol Integration Works

### 1. Protocol Parsing

The system automatically:
- Loads your 142KB protocol document
- Splits it into 315 logical sections
- Extracts keywords from each section
- Maps keywords to topics (craving, motivation, relapse, etc.)

### 2. Relevance Scoring

When a user sends a message:
- Each protocol section gets a relevance score
- Scoring based on:
  - Keyword matches (2 points)
  - Topic matches (1 point)
  - Title relevance (3 points)

Example: "I'm having a craving"
- Matches keyword "craving" (+2)
- Matches topic "craving" (+2)
- Matches section title with "craving" (+3)
- Total score: 7 points

### 3. Context Assembly

The top 3 (configurable) most relevant sections are:
- Extracted from protocol
- Formatted with section titles
- Limited to 500 characters each (configurable)
- Combined into context string

### 4. Prompt Construction

Final prompt sent to Gemini:
```
System Instructions (compassionate counselor role)
+
Relevant Protocol Sections
+
Last 5 Conversation Messages
+
Current User Message
```

### 5. Response Generation

Gemini generates response that:
- Follows protocol guidelines
- Maintains conversational tone
- Provides actionable advice
- Shows empathy and support

## 🧪 Testing Recommendations

### Phase 1: Basic Functionality (Week 1)

Test each scenario:
- ✅ Craving emergency
- ✅ Relapse confession
- ✅ Motivation request
- ✅ Withdrawal symptoms
- ✅ Success celebration
- ✅ Trigger identification
- ✅ Social pressure
- ✅ Progress check

For each:
1. Test with protocol ON
2. Test with protocol OFF
3. Compare responses
4. Note quality differences

### Phase 2: Conversation Flow (Week 2)

Test multi-turn conversations:
- Start with initial concern
- Follow up with questions
- Simulate realistic user behavior
- Test context retention

Example flow:
1. "I want to quit smoking"
2. "Why is it so hard?"
3. "What should I do first?"
4. "I'm afraid I'll fail"

### Phase 3: Edge Cases (Week 3)

Test unusual inputs:
- Very short messages ("help")
- Very long messages (paragraphs)
- Misspellings ("craving" → "carving")
- Multiple topics in one message
- Emotional language
- Questions about the study

### Phase 4: Protocol Refinement (Week 4)

Based on testing:
1. Identify gaps in protocol coverage
2. Adjust keyword mappings
3. Fine-tune relevance scoring
4. Optimize section selection
5. Update protocol document as needed

## 📈 Metrics to Track

### Response Quality
- [ ] Empathy level (1-5)
- [ ] Actionability (specific advice given)
- [ ] Protocol adherence (follows guidelines)
- [ ] Conversational naturalness (1-5)
- [ ] Response length (appropriate)

### Technical Metrics
- [ ] Response time (< 5 seconds)
- [ ] Relevance score of sections used
- [ ] Number of sections needed
- [ ] API success rate

### User Experience
- [ ] Clarity of response
- [ ] Helpfulness (1-5)
- [ ] Would follow advice (yes/no)
- [ ] Appropriate tone (yes/no)

## 🔧 Customization Guide

### Adjust Protocol Context Length

In `protocol_manager.py`, line ~85:
```python
# Change 500 to your desired max characters per section
context += f"{section.content[:500]}..."
```

### Add More Keywords

In `protocol_manager.py`, add to `keyword_map`:
```python
self.keyword_map = {
    'craving': [...],
    'your_new_topic': ['keyword1', 'keyword2', 'keyword3'],
}
```

### Modify AI Personality

In `api_server.py`, edit the `system_prompt`:
```python
system_prompt = """
You are [your custom personality].

Your specific guidelines:
- [guideline 1]
- [guideline 2]
"""
```

### Change Max History

In `api_server.py`, line ~120:
```python
# Change 5 to your desired number
for msg in request.conversation_history[-5:]:
```

## 🚨 Troubleshooting

### Problem: "API Not Connected" in Streamlit

**Solution:**
1. Verify API server is running: `curl http://localhost:8000/health`
2. Check for port conflicts: `lsof -i :8000`
3. Restart API server
4. Check API logs for errors

### Problem: "No relevant protocol context found"

**Solutions:**
1. Lower the relevance threshold
2. Add more keywords to keyword_map
3. Use broader search terms
4. Check protocol document loaded correctly

### Problem: "Responses are too generic"

**Solutions:**
1. Increase max_protocol_sections (3 → 5)
2. Increase section character limit (500 → 1000)
3. Refine keyword mappings
4. Improve protocol section organization

### Problem: "API responses timeout"

**Solutions:**
1. Check internet connection
2. Verify API key is valid
3. Reduce context length
4. Check Gemini API status

### Problem: "SSL Certificate Error"

**Solution:**
This is an environment issue. Run on your local machine or use Docker.

## 📱 Integration with Flutter App

Once you're happy with the testing:

### Step 1: Deploy API

Deploy to production:
- **Google Cloud Run** (recommended)
- AWS Lambda
- Heroku
- Your own server

### Step 2: Create Flutter Service

```dart
// lib/services/protocol_api_service.dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class ProtocolApiService {
  final String _baseUrl = 'YOUR_DEPLOYED_API_URL';
  
  Future<Map<String, dynamic>> sendMessage(
    String message,
    List<Map<String, String>> history,
  ) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/chat'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'message': message,
        'conversation_history': history,
        'use_protocol': true,
        'max_protocol_sections': 3,
      }),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get response');
    }
  }
}
```

### Step 3: Update Provider

```dart
// lib/providers/dash_chat_provider.dart
class DashChatProvider extends ChangeNotifier {
  final ProtocolApiService _apiService = ProtocolApiService();
  
  Future<void> sendUserMessage(String message) async {
    try {
      final history = _buildHistory();
      final response = await _apiService.sendMessage(message, history);
      
      _addMessage(ChatMessage(
        text: response['response'],
        user: _assistantUser,
        createdAt: DateTime.now(),
      ));
      
      notifyListeners();
    } catch (e) {
      _handleError(e);
    }
  }
}
```

## 📚 Additional Resources

### Files in This Package

| File | Purpose |
|------|---------|
| `api_server.py` | FastAPI backend with Gemini integration |
| `streamlit_app.py` | Interactive UI for testing |
| `protocol_manager.py` | Protocol context extraction logic |
| `protocol_document.txt` | Your 142KB protocol document |
| `requirements.txt` | Python dependencies |
| `.env` | API key configuration |
| `start.sh` | Easy startup script |
| `test_setup.py` | System verification tests |
| `README.md` | Detailed documentation |

### Key Technologies

- **FastAPI**: Modern Python web framework
- **Streamlit**: Interactive data apps
- **Google Gemini**: AI model (gemini-pro)
- **Python 3.8+**: Programming language

### Next Steps

1. ✅ Copy files to your local machine
2. ✅ Install dependencies
3. ✅ Run test_setup.py
4. ✅ Start the servers
5. ✅ Test in browser
6. ✅ Iterate on protocol
7. ✅ Deploy to production
8. ✅ Integrate with Flutter app

## 💡 Pro Tips

1. **Start Simple**: Test with protocol ON vs OFF for each scenario
2. **Iterate Fast**: Adjust keywords based on what works
3. **Track Results**: Keep notes on response quality
4. **Refine Protocol**: Update document based on testing
5. **Monitor Usage**: Track which sections are used most
6. **User Feedback**: Test with real users when ready

## 🎓 Understanding the Architecture

```
User Message "I'm having a craving"
        ↓
[Protocol Manager]
  - Extracts keywords: "craving"
  - Scores all 315 sections
  - Returns top 3 relevant sections
        ↓
[Prompt Builder]
  - System instructions
  - Protocol context
  - Conversation history
  - User message
        ↓
[Google Gemini API]
  - Processes full context
  - Generates response
  - Returns text
        ↓
[User sees response]
  - "I understand cravings are tough..."
  - With protocol guidance!
```

## ✅ Ready to Start!

Everything is configured and ready. Just:

1. Copy to your local machine
2. Run `python test_setup.py`
3. Start servers: `./start.sh`
4. Open http://localhost:8501
5. Start testing!

---

**Built for QuitTxt Research Study**
*Helping people quit smoking through AI-powered, protocol-guided support*

Questions? Check the troubleshooting section or review the code comments.
