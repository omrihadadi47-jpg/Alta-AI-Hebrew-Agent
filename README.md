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
