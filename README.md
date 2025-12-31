# 📞 Alta AI - Hebrew Voice SDR Agent

An end-to-end AI Sales Development Representative (SDR) capable of making outbound calls, handling complex Hebrew conversations using Deepdub TTS, checking availability, and booking meetings.

## 🛠 Project Overview
This project was built for **Alta** as a solution for an automated Revenue Workforce Manager. It features a custom Hebrew-speaking agent that doesn't just talk, but also performs business actions like scheduling and email follow-ups.

## 🏗 Architecture
The system is composed of several moving parts:
* **Streamlit Dashboard**: A custom UI to configure the agent's prompt, voice settings, and customer details before a call.
* **Vapi**: Orchestrates the call, handling transcription (STT) and the LLM response cycle.
* **OpenAI (GPT-4o)**: The "brain" managing the conversation logic and tool calling.
* **Deepdub TTS**: High-quality Hebrew voice synthesis integrated via a custom Python bridge.
* **Python/FastAPI Backend**: A bridge server that processes audio in real-time and executes business tools.
* **Twilio**: Telephony provider for making the actual outbound calls.

## 🚀 Local Setup

### 1. Prerequisites
* Python 3.10+
* **FFmpeg**: Required on your system for audio stream processing.
* **ngrok**: To expose the local bridge server to Vapi.

### 2. Installation
1. Clone the repository:
   ```bash
   git clone [https://github.com/omrihadadi47-jpg/Alta-AI-Hebrew-Agent.git](https://github.com/omrihadadi47-jpg/Alta-AI-Hebrew-Agent.git)
   cd Alta-AI-Hebrew-Agent

### 3. Environment Variables
Create a .env file in the root directory (this file is git-ignored for security) and add your keys:

Code snippet

VAPI_API_KEY=your_vapi_key
ASSISTANT_ID=your_assistant_id
PHONE_NUMBER_ID=your_phone_id
DEEPDUB_API_KEY=your_deepdub_key
SENDER_EMAIL=your_email
EMAIL_APP_PASSWORD=your_app_password

### 4. Running the Agent
# Start the Bridge Server:

Bash

`python server.py`

# Expose via ngrok:

Bash

`ngrok http 8000`

# Run the Dashboard:

Bash

`streamlit run app.py`

### 🧠 Business Logic & Tools
The agent utilizes a dedicated toolset (tools.py) to drive revenue:

check_availability: Queries Google Calendar to find available time slots for a demo.

book_meeting: Records the meeting in the calendar and triggers an automated MIMEMultipart email confirmation to the lead.


Developed by Omri Hadadi as part of the Alta AI technical assessment.
