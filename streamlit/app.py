import streamlit as st
from google import genai
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Physics Tutor",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for Premium Look ---
st.markdown("""
<style>
    /* Overall App Background & Base Text */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }
    
    /* Headers & Subtitles */
    h1, h2, h3, .stMarkdown p {
        color: #f1f5f9 !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label {
        color: #e2e8f0 !important;
    }

    /* Chat Messages Container */
    .stChatMessage {
        border-radius: 1rem;
        margin-bottom: 0.8rem;
    }

    /* User Message Styling (Blue Background, White Text) */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: rgba(59, 130, 246, 0.15) !important;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    [data-testid="stChatMessage"]:nth-child(even) [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }

    /* Assistant Message Styling (Light Background, Dark Text for contrast) */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: rgba(248, 250, 252, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    [data-testid="stChatMessage"]:nth-child(odd) [data-testid="stMarkdownContainer"] p {
        color: #0f172a !important; /* Dark blue-black for readability */
    }
    [data-testid="stChatMessage"]:nth-child(odd) code {
        color: #e11d48 !important; /* Reddish for code on light background */
        background-color: #f1f5f9 !important;
    }

    /* Input Field */
    .stTextInput > div > div > input {
        background-color: rgba(30, 41, 59, 0.7) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    /* Hide top padding */
    .block-container {
        padding-top: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- System Prompt Definition ---
SYSTEM_PROMPT = """
당신은 고등학생들을 위한 친절하고 전문적인 '물리 튜터'입니다. 
대한민국 고등학교 물리 I 및 물리 II 교육과정을 완벽하게 이해하고 있습니다.

당신의 목표는 학생들이 물리 문제를 스스로 해결할 수 있도록 돕는 것입니다. 
단순히 정답을 알려주기보다는 다음 원칙을 따르세요:
1. 친절하고 격려하는 말투를 사용하세요. (예: "안녕하세요! 물리 공부하시느라 고생이 많네요. 함께 차근차근 해결해 봐요!")
2. 복잡한 개념은 일상생활의 비유를 들어 설명하세요.
3. 단계별로 질문을 던져 학생이 스스로 생각하게 유도하세요.
4. 수식과 기호를 정확하게 사용하되, 각 기호가 의미하는 바를 명확히 설명하세요.
5. 학생이 틀린 대답을 하더라도 비난하지 말고, 왜 그렇게 생각했는지 물어본 뒤 올바른 방향으로 안내하세요.

학생의 수준에 맞춰 설명을 조절하고, 물리 학습에 대한 흥미를 느낄 수 있도록 도와주세요.
"""

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# --- Sidebar ---
with st.sidebar:
    st.title("⚛️ AI Physics Tutor")
    st.markdown("---")
    
    api_key_input = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="Enter your API Key here...",
        help="You can get your API key from Google AI Studio."
    )
    
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        st.rerun()

    st.markdown("---")
    if st.button("🔄 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.info("""
    **학습 도움말**
    - 등가속도 운동 공식이 궁금해요?
    - 뉴턴의 운동 법칙을 설명해 주세요.
    - 상대성 이론이란 무엇인가요?
    """)

# --- Main Interface ---
st.title("👨‍🏫 AI 물리 튜터")
st.caption("궁금한 물리 개념이나 문제를 물어보세요! 친절하게 도와드릴게요.")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("질문을 입력하세요 (예: F=ma가 무엇인가요?)"):
    if not st.session_state.api_key:
        st.warning("먼저 사이드바에서 Gemini API Key를 입력해주세요.")
    else:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        try:
            client = genai.Client(api_key=st.session_state.api_key)
            
            # Prepare full message history for context
            # (In a real app, we might want to trim this to stay within token limits)
            history = []
            for msg in st.session_state.messages[:-1]: # Exclude the current prompt
                history.append({
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [{"text": msg["content"]}]
                })

            response_container = st.empty()
            full_response = ""

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                
                # Use streaming response
                chat = client.chats.create(
                    model="gemini-3-flash-preview",
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                    },
                    history=history
                )
                
                for chunk in chat.send_message_stream(prompt):
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)

            # Add assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                st.error("🚀 API 호출 한도(Rate Limit)를 초과했습니다. 잠시 후(약 1분 뒤) 다시 시도해 주세요.")
                st.info("Google AI Studio의 무료 티어는 분당 호출 제한이 있습니다.")
            elif "API_KEY_INVALID" in str(e):
                st.info("API 키가 올바른지 확인해 주세요.")
            else:
                st.error(f"오류가 발생했습니다: {str(e)}")

