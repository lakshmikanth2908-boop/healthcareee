import streamlit as st
from google import genai
from google.genai import types

# --- 1. CONFIGURATION AND SAFETY ---

# CRITICAL: System Instruction for ethical and safe use.
SYSTEM_INSTRUCTION = """
You are a helpful, friendly, and **strictly non-diagnostic** Healthcare Companion AI.
Your purpose is to provide general, educational, and organizational health information.

RULES TO STRICTLY FOLLOW:
1.  **NEVER** provide a medical diagnosis, personalized treatment plan, or specific medical advice.
2.  **ALWAYS** preface your response with a strong safety disclaimer.
3.  **DO** encourage the user to consult a qualified healthcare professional (doctor, nurse, or pharmacist) for any symptoms or medical concerns.
4.  **DO** offer reliable, factual, general health information.
"""

MODEL_NAME = 'gemini-2.5-flash'
# 💥 NAME CHANGE HERE
APP_TITLE = "🩺 Healthcare Companion" 

# --- 2. INITIALIZATION FUNCTIONS ---

def get_gemini_client():
    """Initializes, stores, and returns the persistent Gemini Client."""
    # Check if the client is already in session state.
    if 'gemini_client' in st.session_state:
        return st.session_state['gemini_client']

    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ API Key not found. Please set your GEMINI_API_KEY in `.streamlit/secrets.toml`.")
        return None
        
    try:
        # Create the client and store it in session state to prevent closure
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        st.session_state['gemini_client'] = client 
        return client
    except Exception as e:
        st.error(f"❌ Error initializing Gemini Client: {e}")
        return None

def reset_chat():
    """Resets the chat session state and re-initializes the Gemini chat object."""
    # Retrieve the persistent client
    client = get_gemini_client() 
    if not client:
        st.error("Cannot reset chat: Gemini client failed to initialize.")
        return

    # Configuration with the system instruction
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION
    )
    
    # Create a BRAND NEW chat object
    st.session_state['gemini_chat'] = client.chats.create(model=MODEL_NAME, config=config)
    
    # Set a welcome message
    # 💥 NAME CHANGE HERE in the welcome message
    st.session_state.messages = [{"role": "assistant", "content": 
        "**Welcome!** I'm your informational **Healthcare Companion**. I can provide general health facts and tips, but **I am not a doctor**. Please consult a healthcare professional for any medical concerns."}]
    
    st.rerun() 

# --- 3. STREAMLIT APP LOGIC ---

# Set up the page config and header
st.set_page_config(page_title=APP_TITLE, page_icon="🩺", layout="wide")
st.title(APP_TITLE)

# Initialize the chat on first run
if 'gemini_chat' not in st.session_state:
    reset_chat()

# Display the main safety disclaimer (CLEAN UI FOCUS)
with st.container(border=True):
    st.markdown(
        """
        <div style="padding: 5px;">
        <h4 style="color: #FF4B4B; margin-top: 0;">⚠️ SAFETY FIRST: This is NOT Medical Advice</h4>
        <p>I provide **general, educational information only**. I cannot diagnose, treat, or offer personalized medical guidance. **Always** consult a qualified healthcare professional for symptoms or health concerns.</p>
        </div>
        """, unsafe_allow_html=True
    )

# Sidebar for controls (CLEAN UI FOCUS)
with st.sidebar:
    st.header("Chat Controls")
    st.button("Clear Chat History", on_click=reset_chat, type="primary")
    st.caption("Clearing the history starts a completely new conversation with the AI.")
    st.markdown("---")
    st.caption(f"Model: `{MODEL_NAME}`")
    st.caption("Safety rules are strictly enforced.")


# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
# Handle user input
if prompt := st.chat_input("Ask a general health question..."):
    
    # 1. Append and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Call the Gemini API and stream the response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        if 'gemini_chat' in st.session_state:
            try:
                # Correct streaming method: send_message_stream()
                response_stream = st.session_state['gemini_chat'].send_message_stream(prompt) 
                
                for chunk in response_stream:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌") 

                message_placeholder.markdown(full_response)
                
            except Exception as e:
                full_response = f"An error occurred: Chat failed to connect or process the request. Details: {e}"
                message_placeholder.markdown(full_response)
        
        else:
            full_response = "The companion could not be initialized. Please refresh the page and check your API key."
            message_placeholder.markdown(full_response)

    # 3. Append the full assistant response to session state for history persistence
    st.session_state.messages.append({"role": "assistant", "content": full_response})