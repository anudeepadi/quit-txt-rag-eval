"""
Streamlit Frontend for QuitTxt Protocol Testing
Interactive UI for testing protocol-guided conversations
"""
import streamlit as st
import requests
from typing import List, Dict
import time

# Configure page
st.set_page_config(
    page_title="QuitTxt Protocol Tester",
    page_icon="🚭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API endpoint
API_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #6366F1;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        color: #1F2937;
    }
    .user-message {
        background-color: #E0E7FF;
        margin-left: 2rem;
    }
    .assistant-message {
        background-color: #F0FDF4;
        margin-right: 2rem;
    }
    .protocol-context {
        background-color: #FEF3C7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #F59E0B;
        margin: 1rem 0;
    }
    .comparison-box {
        border: 2px solid #E5E7EB;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health() -> bool:
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_protocol_info() -> Dict:
    """Get protocol information from API"""
    try:
        response = requests.get(f"{API_URL}/protocol/info")
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def send_chat_message(message: str, history: List[Dict], use_protocol: bool = True) -> Dict:
    """Send a chat message to the API"""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "message": message,
                "conversation_history": history,
                "use_protocol": use_protocol,
                "max_protocol_sections": st.session_state.get('max_sections', 3)
            },
            timeout=30
        )

        # Check if the request was successful
        if response.status_code != 200:
            error_detail = response.json().get('detail', 'Unknown error')
            return {"error": error_detail}

        return response.json()
    except Exception as e:
        return {"error": str(e)}


def compare_responses(message: str, history: List[Dict]) -> Dict:
    """Get comparison of responses with and without protocol"""
    try:
        response = requests.post(
            f"{API_URL}/chat/compare",
            json={
                "message": message,
                "conversation_history": history,
                "max_protocol_sections": st.session_state.get('max_sections', 3)
            },
            timeout=30
        )

        # Check if the request was successful
        if response.status_code != 200:
            error_detail = response.json().get('detail', 'Unknown error')
            return {"error": error_detail}

        return response.json()
    except Exception as e:
        return {"error": str(e)}


def initialize_session_state():
    """Initialize session state variables"""
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'max_sections' not in st.session_state:
        st.session_state.max_sections = 3
    if 'use_protocol' not in st.session_state:
        st.session_state.use_protocol = True
    if 'show_protocol_context' not in st.session_state:
        st.session_state.show_protocol_context = True


def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🚭 QuitTxt Protocol Tester</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Test AI-powered smoking cessation support with protocol-guided responses</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Settings")
        
        # API Status
        st.subheader("API Status")
        api_healthy = check_api_health()
        if api_healthy:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Not Connected")
            st.info("Start the API server with: `python api_server.py`")
            return
        
        # Protocol Info
        st.subheader("📋 Protocol Info")
        if st.button("Load Protocol Info"):
            with st.spinner("Loading..."):
                info = get_protocol_info()
                if "error" not in info:
                    st.info(info['summary'])
                else:
                    st.error(f"Error: {info['error']}")
        
        st.divider()
        
        # Configuration
        st.subheader("🎛️ Configuration")
        
        st.session_state.use_protocol = st.checkbox(
            "Use Protocol Context",
            value=st.session_state.use_protocol,
            help="Include relevant protocol sections in AI context"
        )
        
        st.session_state.max_sections = st.slider(
            "Max Protocol Sections",
            min_value=1,
            max_value=5,
            value=st.session_state.max_sections,
            help="Number of protocol sections to include"
        )
        
        st.session_state.show_protocol_context = st.checkbox(
            "Show Protocol Context",
            value=st.session_state.show_protocol_context,
            help="Display the protocol context used"
        )
        
        st.divider()
        
        # Actions
        st.subheader("🔧 Actions")
        
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.conversation_history = []
            st.rerun()
        
        if st.button("📊 Test Scenarios", use_container_width=True):
            st.session_state.show_scenarios = True
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "🔬 Compare Responses", "📝 Test Scenarios"])
    
    # Tab 1: Chat Interface
    with tab1:
        st.subheader("Interactive Chat")
        
        # Display conversation history
        for msg in st.session_state.conversation_history:
            if msg['role'] == 'user':
                st.markdown(
                    f'<div class="chat-message user-message"><strong>You:</strong> {msg["content"]}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="chat-message assistant-message"><strong>QuitTxt Assistant:</strong> {msg["content"]}</div>',
                    unsafe_allow_html=True
                )
                
                # Show protocol context if enabled
                if st.session_state.show_protocol_context and 'protocol_context' in msg and msg['protocol_context']:
                    with st.expander("📋 View Protocol Context Used"):
                        st.text(msg['protocol_context'])
        
        # Chat input
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Your message:",
                placeholder="Type your message here... (e.g., 'I'm having a strong craving right now')",
                height=100
            )
            
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                submit_button = st.form_submit_button("Send 📤", use_container_width=True)
            with col2:
                quick_reply = st.form_submit_button("Quick Test 🚀", use_container_width=True)
        
        if quick_reply:
            user_input = "I'm having a strong craving right now. What should I do?"
        
        if (submit_button or quick_reply) and user_input:
            # Add user message to history
            st.session_state.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Get AI response
            with st.spinner("🤔 Thinking..."):
                response = send_chat_message(
                    user_input,
                    st.session_state.conversation_history[:-1],  # Exclude last message
                    st.session_state.use_protocol
                )
            
            if "error" not in response:
                # Add assistant response to history
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": response['response'],
                    "protocol_context": response.get('protocol_context_used', '')
                })
                st.rerun()
            else:
                st.error(f"Error: {response['error']}")
    
    # Tab 2: Compare Responses
    with tab2:
        st.subheader("Compare Protocol-Guided vs Non-Protocol Responses")
        st.info("This compares how the AI responds with and without protocol context")
        
        compare_input = st.text_area(
            "Test message:",
            placeholder="Enter a message to compare responses...",
            height=100,
            key="compare_input"
        )
        
        if st.button("🔬 Compare Responses", use_container_width=True):
            if compare_input:
                with st.spinner("Generating both responses..."):
                    comparison = compare_responses(compare_input, st.session_state.conversation_history)
                
                if "error" not in comparison:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### ✅ With Protocol")
                        st.markdown(
                            f'<div class="comparison-box" style="border-color: #10B981;">{comparison["with_protocol"]["response"]}</div>',
                            unsafe_allow_html=True
                        )
                        
                        if st.session_state.show_protocol_context:
                            with st.expander("View Protocol Context"):
                                st.text(comparison["with_protocol"].get("protocol_context_used", "No context"))
                    
                    with col2:
                        st.markdown("### ❌ Without Protocol")
                        st.markdown(
                            f'<div class="comparison-box" style="border-color: #EF4444;">{comparison["without_protocol"]["response"]}</div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.error(f"Error: {comparison['error']}")
            else:
                st.warning("Please enter a message to compare")
    
    # Tab 3: Test Scenarios
    with tab3:
        st.subheader("Pre-defined Test Scenarios")
        st.info("Click on any scenario to test how the protocol-guided AI responds")
        
        scenarios = [
            {
                "title": "🔥 Craving Emergency",
                "message": "I'm having a really strong craving right now and I don't know if I can resist!"
            },
            {
                "title": "😔 Relapse Confession",
                "message": "I feel terrible. I smoked a cigarette today after 2 weeks of being smoke-free."
            },
            {
                "title": "💪 Motivation Needed",
                "message": "I'm thinking about quitting, but I'm not sure if I can do it. Why should I even try?"
            },
            {
                "title": "😰 Withdrawal Symptoms",
                "message": "I've been so irritable and anxious since I quit. Is this normal?"
            },
            {
                "title": "🎉 Success Celebration",
                "message": "It's been 30 days since my last cigarette! I'm so proud of myself!"
            },
            {
                "title": "🤔 Trigger Identification",
                "message": "I always want to smoke after meals. How do I deal with this trigger?"
            },
            {
                "title": "👨‍👩‍👧 Social Pressure",
                "message": "All my friends smoke. How do I hang out with them without smoking?"
            },
            {
                "title": "📊 Progress Check",
                "message": "Can you tell me about my progress? How am I doing?"
            }
        ]
        
        cols = st.columns(2)
        for idx, scenario in enumerate(scenarios):
            with cols[idx % 2]:
                if st.button(scenario['title'], key=f"scenario_{idx}", use_container_width=True):
                    # Add scenario to conversation
                    st.session_state.conversation_history.append({
                        "role": "user",
                        "content": scenario['message']
                    })
                    
                    # Get response
                    with st.spinner("Getting response..."):
                        response = send_chat_message(
                            scenario['message'],
                            st.session_state.conversation_history[:-1],
                            st.session_state.use_protocol
                        )
                    
                    if "error" not in response:
                        st.session_state.conversation_history.append({
                            "role": "assistant",
                            "content": response['response'],
                            "protocol_context": response.get('protocol_context_used', '')
                        })
                    
                    st.rerun()


if __name__ == "__main__":
    main()
