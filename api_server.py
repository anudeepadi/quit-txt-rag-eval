"""
FastAPI Backend for QuitTxt Protocol Testing
Integrates Google Gemini API with protocol document context
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import os
from protocol_manager import ProtocolContextManager

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="QuitTxt Protocol API",
    description="API for testing protocol-guided responses using Google Gemini",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Initialize Protocol Manager
protocol_manager = ProtocolContextManager('protocol_document.txt')


# Request/Response Models
class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    use_protocol: bool = True
    max_protocol_sections: int = 3


class ChatResponse(BaseModel):
    response: str
    protocol_context_used: Optional[str] = None
    model: str = "gemini-2.0-flash-exp"


class ProtocolInfo(BaseModel):
    summary: str
    total_sections: int
    total_length: int


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "QuitTxt Protocol API",
        "version": "1.0.0",
        "endpoints": {
            "/chat": "Send a message and get protocol-guided response",
            "/protocol/info": "Get protocol document information",
            "/health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "api_configured": bool(GOOGLE_API_KEY)}


@app.get("/protocol/info", response_model=ProtocolInfo)
async def get_protocol_info():
    """Get information about the loaded protocol"""
    summary = protocol_manager.get_protocol_summary()
    return ProtocolInfo(
        summary=summary,
        total_sections=len(protocol_manager.sections),
        total_length=len(protocol_manager.full_protocol)
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message and get a protocol-guided response
    
    Args:
        request: ChatRequest containing message, history, and options
        
    Returns:
        ChatResponse with AI response and protocol context used
    """
    try:
        # Get relevant protocol context
        protocol_context = ""
        if request.use_protocol:
            protocol_context = protocol_manager.get_relevant_context(
                request.message,
                max_sections=request.max_protocol_sections
            )
        
        # Build the full prompt
        system_prompt = """You are a compassionate smoking cessation counselor working with the QuitTxt program. You provide personalized, evidence-based support to help people quit smoking.

RESPONSE GUIDELINES:
1. **Use Protocol Strategies**: Draw from the evidence-based strategies in the PROTOCOL SECTIONS below, but express them naturally
2. **Be Conversational**: Don't copy-paste protocol language; explain strategies in your own words adapted to the user's specific situation
3. **Provide Specifics**: When the protocol mentions techniques (4 Ds, breathing exercises, etc.), explain HOW to use them, not just THAT they exist
4. **Vary Your Responses**: Avoid repeating the same phrases or metaphors; use different examples and language each time
5. **Personalize**: Reference the user's specific situation, emotions, or previous messages when relevant
6. **Be Empathetic First**: Acknowledge feelings before jumping to strategies
7. **Length**: Keep responses concise (3-5 sentences) but substantive

AVOID:
- Copying exact protocol phrases verbatim (except specific technique names like "4 Ds")
- Repeating the same metaphors or examples
- Just listing links without explanation
- Generic advice that ignores the protocol strategies

"""

        if protocol_context:
            system_prompt += f"\n{protocol_context}\n"
            system_prompt += """
HOW TO USE THE PROTOCOL:
- Understand the PRINCIPLES and STRATEGIES from the sections above
- Express these strategies in natural, conversational language tailored to this user
- Combine protocol wisdom with empathy and personalization
- Use your own words while staying true to the evidence-based approaches

"""
        
        # Build conversation history
        conversation_text = system_prompt + "\n\n"

        if request.conversation_history:
            conversation_text += "=== CONVERSATION HISTORY ===\n"
            conversation_text += "(Use this history to personalize your response and avoid repeating previous advice)\n\n"
            for msg in request.conversation_history[-5:]:  # Last 5 messages
                conversation_text += f"{msg.role.upper()}: {msg.content}\n"
            conversation_text += "\n"

        conversation_text += f"USER: {request.message}\n\n"
        conversation_text += "ASSISTANT: (Provide a natural, personalized response drawing from protocol strategies but using conversational language)"
        
        # Generate response
        response = model.generate_content(conversation_text)
        
        return ChatResponse(
            response=response.text,
            protocol_context_used=protocol_context if request.use_protocol else None,
            model="gemini-2.0-flash-exp"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


@app.post("/chat/compare")
async def compare_responses(request: ChatRequest):
    """
    Compare responses with and without protocol context
    
    Returns both protocol-guided and non-protocol responses for comparison
    """
    try:
        # Get response WITH protocol
        request_with_protocol = ChatRequest(
            message=request.message,
            conversation_history=request.conversation_history,
            use_protocol=True,
            max_protocol_sections=request.max_protocol_sections
        )
        with_protocol = await chat(request_with_protocol)
        
        # Get response WITHOUT protocol
        request_without_protocol = ChatRequest(
            message=request.message,
            conversation_history=request.conversation_history,
            use_protocol=False
        )
        without_protocol = await chat(request_without_protocol)
        
        return {
            "with_protocol": with_protocol.dict(),
            "without_protocol": without_protocol.dict(),
            "message": request.message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing responses: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
