# InsureAssist AI  
### Intelligent Home Insurance Claim Assistant

InsureAssist AI is a conversational AI assistant designed to guide users step by step through the process of declaring a home insurance claim.  
The application combines a **ReAct-based AI agent** with a **modern Streamlit chat interface** to deliver a smooth, intuitive, and reliable user experience.

---

## Features

- **Conversational claim declaration** (ChatGPT-like UX)
- **ReAct AI Agent** (Reasoning + Action)
- **Dynamic document upload handling**
- **Insurance-oriented workflow** (guided, step-by-step)
- **Modern & professional UI** built with Streamlit
- **Robust state machine** (no infinite loops, no blank screens)

---

## How It Works

InsureAssist AI uses a **ReAct (Reason + Act) architecture**:

1. The user describes their situation
2. The AI reasons about missing information
3. The AI asks targeted questions or requests documents
4. The process continues until all required claim information is collected
5. A final structured response is provided

The AI agent is powered by **Mistral AI** and controlled through a **strict prompt and parsing logic** to ensure reliability.

---

## Architecture Overview

- **Frontend**: Streamlit (chat-based UI)
- **Agent Logic**: ReAct pattern
- **LLM**: Mistral (`mistral-small-latest`)
- **State Management**: Streamlit Session State
- **Prompt Control**: Strict output formatting & parsing
- **Document Handling**: Streamlit file uploader

---

## Project Structure
.
├── app.py # Main Streamlit application

├── processus.md # Insurance claim process definition

├── .env # API keys (not committed)

├── README.md # Project documentation


---

## Installation

### Clone the repository

git clone https://github.com/BouchraBENGHAZALA/InsureAssist-ai.git
cd InsureAssist-ai

### Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows

### Install dependencies
pip install -r requirements.txt

## Environment Variables

Create a .env file at the root of the project:

API_KEY_MISTRAL=your_mistral_api_key_here

## Run the Application
streamlit run app.py

Then open your browser at: http://localhost:8501