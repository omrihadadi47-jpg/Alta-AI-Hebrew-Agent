import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

vapi_api_key = os.getenv("VAPI_API_KEY")
assistant_id = os.getenv("ASSISTANT_ID")
phone_number_id = os.getenv("PHONE_NUMBER_ID")

CUSTOM_VOICE_URL = "https://transsonic-katheleen-undeputed.ngrok-free.dev/to-speech"

headers = {
    "Authorization": f"Bearer {vapi_api_key}",
    "Content-Type": "application/json"
}

# Page Setup & CSS Styling 
st.set_page_config(page_title="Alta AI Admin", page_icon="small_logo.jpeg", layout="wide")

st.markdown("""
    <style>
    textarea[aria-label="📝 System Prompt (Behavior & Script)"] {
        direction: rtl; text-align: right; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    div.stButton > button {
        background-color: #6c5ce7; color: white; border-radius: 8px; border: none; padding: 10px 24px; font-weight: bold; transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #5b4cc4; box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .main-header { color: #2d3436; }
    .main-header h1 { font-weight: 700; letter-spacing: -1px; margin: 0; padding-top: 10px; }
    .stSelectbox label p, .stTextInput label p, .stTextArea label p {
        font-size: 1.15rem !important; font-weight: 700 !important; color: #2d3436;
    }
    [data-testid="stForm"] {
        background-color: #e6e0ff; padding: 30px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(108, 92, 231, 0.15); border: 1px solid #d1c4e9;
    }
    div[data-testid="stFormSubmitButton"] { display: flex; justify-content: center; width: 100%; }
    div[data-testid="stFormSubmitButton"] > button { min-width: 300px; background-color: #6c5ce7; border: none; }
    .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# Header Section
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("logo.png", width="stretch")
with col_title:
    st.markdown("""
        <div style='display: flex; align-items: center; height: 100%;'>
            <h1 style='color: #2d3436; font-size: 2.5rem;'>AI Revenue Workforce Manager</h1>
        </div>
    """, unsafe_allow_html=True)

# Fetch Data from Vapi 
current_prompt = ""
current_first_msg = ""
current_model = "gpt-4o"

try:
    response = requests.get(f"https://api.vapi.ai/assistant/{assistant_id}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        model_config = data.get('model', {})
        current_model = model_config.get('model', 'gpt-4o')
        current_prompt = model_config.get('systemPrompt')
        if not current_prompt:
            for msg in model_config.get('messages', []):
                if msg.get('role') == 'system':
                    current_prompt = msg.get('content')
                    break
        current_first_msg = data.get('firstMessage')
except Exception as e:
    st.error(f"Connection Error: {e}")

# Section 1: Agent Configuration Form
st.markdown("<h2 style='text-align: center; color: #4b4b4b; margin-bottom: 25px;'>⚙️ Agent Configuration Panel</h2>", unsafe_allow_html=True)

with st.form("agent_settings"):
    c1, c2 = st.columns([1, 1])
    with c1:
        selected_model = st.selectbox("🧠 AI Brain Model", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"], index=0)
    with c2:
        st.info(f"🎙️ Using Custom Voice: Deepdub")

    new_first_msg = st.text_input("👋 First Message (The Hook)", value=current_first_msg)
    new_prompt = st.text_area("📝 System Prompt (Behavior & Script)", value=current_prompt if current_prompt else "", height=350)
    
    submitted = st.form_submit_button("💾 Update Live Agent Configuration")

    if submitted:
        payload = {
            "model": { "model": selected_model, "firstMessage": new_first_msg, "messages": [{ "role": "system", "content": new_prompt }] },
            "voice": {
                "provider": "custom-voice",
                "server": {
                    "url": CUSTOM_VOICE_URL,
                    "timeoutSeconds": 20
                }
            }
        }
        with st.spinner("Updating Vapi to use Deepdub Bridge..."):
            requests.patch(f"https://api.vapi.ai/assistant/{assistant_id}", headers=headers, json=payload)
            st.success("✅ Agent updated! Using Deepdub via your Bridge.")
            st.rerun()

st.write(""); st.divider()

# --- Section 2: Simulation Lab ---
st.markdown("<h2 style='text-align: center;'>🧪 Test Lab Simulation</h2>", unsafe_allow_html=True)
col_pad_l, col_name, col_phone, col_email, col_gender, col_pad_r = st.columns([0.5, 2, 2, 2, 1.5, 0.5])

with col_name: customer_name = st.text_input("Customer Name", "Daniel", placeholder="Lead Name")
with col_phone: customer_phone = st.text_input("Target Phone", "+972524701004", placeholder="+972500000000")
with col_email: customer_email = st.text_input("Customer Email", "omrihadadi47@gmail.com", placeholder="Email")
with col_gender: customer_gender = st.selectbox("Gender", ["Male", "Female"], index=0)

st.write("") 
col_btn_margin_l, col_btn, col_btn_margin_r = st.columns([2, 1, 2])
with col_btn:
    if st.button("🚀 Initiate Test Call Now", use_container_width=True):
        if not customer_phone or len(customer_phone) < 10:
             st.warning("⚠️ Please enter a valid phone number.")
        else:
            # --- Logic to inject variables ---
            prompt_for_call = new_prompt
            
            # Inject Email
            if customer_email:
                prompt_for_call = prompt_for_call.replace("{lead_email}", customer_email)
            else:
                prompt_for_call = prompt_for_call.replace("{lead_email}", "המייל שלך")

            # Inject Gender Instruction
            if customer_gender == "Male":
                gender_instruction = "אתה מדבר עם גבר. פנה אליו בלשון זכר."
            else:
                gender_instruction = "אתה מדבר עם אישה. פנה אליה בלשון נקבה."
            prompt_for_call = prompt_for_call.replace("{gender_instruction}", gender_instruction)

            # Inject Name
            first_msg_for_call = new_first_msg
            if customer_name:
                prompt_for_call = prompt_for_call.replace("{customer_name}", customer_name)
                first_msg_for_call = first_msg_for_call.replace("{customer_name}", customer_name)
            else:
                prompt_for_call = prompt_for_call.replace("{customer_name}", "לקוח יקר")
                first_msg_for_call = first_msg_for_call.replace("{customer_name}", "")         

            call_payload = {
                "assistantId": assistant_id,
                "phoneNumberId": phone_number_id,
                "customer": {
                    "number": customer_phone,
                    "name": customer_name,
                    "email": customer_email
                },
                "assistantOverrides": {
                    "firstMessage": first_msg_for_call,
                    "firstMessageMode": "assistant-speaks-first",
                    "numWordsToInterruptAssistant": 2,
                    
                    "voice": {
                        "provider": "custom-voice",
                        "server": {
                            "url": CUSTOM_VOICE_URL, 
                            "timeoutSeconds": 20
                        }
                    },
                    "model": {
                        "provider": "openai", 
                        "model": selected_model,
                        "systemPrompt": prompt_for_call,
                    },
                    "transcriber": {
                        "provider": "openai",
                        "model": "gpt-4o-mini-transcribe",
                        "language": "he"
                    },
                    "variableValues": {
                        "customer_name": customer_name,
                        "customer_email": customer_email,
                        "customer_gender": customer_gender,
                        "lead_email": customer_email 
                    }
                }
            }
            
            call_resp = requests.post("https://api.vapi.ai/call/phone", headers=headers, json=call_payload)
            
            if call_resp.status_code == 201:
                st.toast(f"Calling {customer_name} via Unified Server...", icon="📞")
                st.success("✅ Call initiated! (First message forced)")
            else:
                st.error(f"Failed: {call_resp.text}")

