import os
import re
import streamlit as st
from dotenv import load_dotenv
from mistralai import Mistral

# ======================================================
# CONFIG STREAMLIT
# ======================================================
st.set_page_config(
    page_title="🛡️ Déclaration de Sinistres",
    page_icon="🛡️",
    layout="centered"
)

# ======================================================
# STYLE (CSS)
# ======================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
}

h1 {
    color: #1f2937;
    font-weight: 700;
}

.chat-container {
    margin-bottom: 80px;
}

[data-testid="stChatMessage"] {
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 8px;
}

[data-testid="stChatMessage"]:has(div[data-testid="stMarkdownContainer"]) {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
}

[data-testid="stChatMessage"][data-testid*="user"] {
    background-color: #2563eb;
    color: white;
}

.stChatInputContainer {
    border-top: 1px solid #e5e7eb;
    background: white;
}

button {
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Assistant de Déclaration de Sinistres")

# ======================================================
# API MISTRAL
# ======================================================
load_dotenv()
api_key = os.getenv("API_KEY_MISTRAL")

if not api_key:
    st.error("❌ Clé API_MISTRAL manquante")
    st.stop()

@st.cache_resource
def get_client():
    return Mistral(api_key=api_key)

client = get_client()

# ======================================================
# LLM
# ======================================================
def llm_inference(prompt: str) -> str:
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Answer: Erreur API : {e}"

# ======================================================
# TOOLS (DESCRIPTIFS)
# ======================================================
def ask_human(ask: str):
    """Ask human to input a text."""
    pass

def upload(name: str):
    """Ask human to upload a document."""
    pass

tools = {
    "AskHuman": ask_human,
    "Upload": upload
}

# ======================================================
# PROMPT
# ======================================================
def format_prompt(history: list[str]) -> str:
    prompt = """
Tu es un agent IA spécialiste de la déclaration de sinistres pour une assurance habitation.

Tu dois STRICTEMENT répondre selon UN SEUL des formats suivants :

Thought: <raisonnement>
Action: AskHuman
Arguments:
ask=<question>

OU

Thought: <raisonnement>
Action: Upload
Arguments:
name=<document>

OU

Answer: <réponse finale>

Ne produis JAMAIS autre chose.

## Contexte
{processus}

## Actions
{actions}

## Historique
{history}

### Sortie
""".strip()

    actions = "\n\n".join(
        f"### Action `{t}`\n{tools[t].__doc__}" for t in tools
    )

    try:
        processus = open("processus.md", "r", encoding="utf-8").read()
    except FileNotFoundError:
        processus = "Processus non disponible."

    return prompt.format(
        processus=processus,
        actions=actions,
        history="\n".join(history)
    )

# ======================================================
# PARSER
# ======================================================
def parse_output(output: str):
    answer = re.search(r"Answer:\s*(.*)", output, re.DOTALL)
    action = re.search(r"Action:\s*(\w+)", output)
    args = re.search(r"Arguments:([\s\S]*)", output)

    if answer:
        return "answer", answer.group(1).strip()

    if action:
        tool = action.group(1)
        params = {}
        if args:
            for line in args.group(1).splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    params[k.strip()] = v.strip().strip("\"'")
        return "action", tool, params

    return "invalid", output

# ======================================================
# ÉTAT STREAMLIT
# ======================================================
if "state" not in st.session_state:
    st.session_state.state = "WAIT_USER"  # WAIT_USER | RUN | ASK | UPLOAD | DONE

if "history" not in st.session_state:
    st.session_state.history = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_tool" not in st.session_state:
    st.session_state.pending_tool = None

# ======================================================
# AFFICHAGE CHAT
# ======================================================
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
st.markdown('</div>', unsafe_allow_html=True)

# ======================================================
# AGENT
# ======================================================
def run_agent():
    prompt = format_prompt(st.session_state.history)

    with st.spinner("🤖 Analyse de votre situation en cours..."):
        output = llm_inference(prompt)

    step, *content = parse_output(output)

    if step == "answer":
        st.session_state.messages.append({
            "role": "assistant",
            "content": content[0]
        })
        st.session_state.history.append(f"Answer: {content[0]}")
        st.session_state.state = "DONE"
        return

    if step == "action":
        tool, params = content
        st.session_state.pending_tool = (tool, params)

        if tool == "AskHuman":
            question = params.get("ask", "Pouvez-vous préciser ?")
            st.session_state.messages.append({
                "role": "assistant",
                "content": question
            })
            st.session_state.state = "ASK"
            return

        if tool == "Upload":
            name = params.get("name", "document")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"📎 Merci de charger le document suivant : **{name}**"
            })
            st.session_state.state = "UPLOAD"
            return

    # Sécurité
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Pouvez-vous me donner plus de détails sur le sinistre ?"
    })
    st.session_state.state = "ASK"

# ======================================================
# MACHINE D'ÉTAT
# ======================================================
if st.session_state.state == "WAIT_USER":
    st.markdown("""
    <div style="padding:16px; background:#ffffff; border-radius:12px;
                border:1px solid #e5e7eb; margin-bottom:12px;">
    👋 <b>Bienvenue</b><br>
    Je vais vous accompagner étape par étape pour déclarer votre sinistre habitation.<br><br>
    👉 <i>Expliquez simplement ce qu’il s’est passé.</i>
    </div>
    """, unsafe_allow_html=True)

    user_input = st.chat_input("Décrivez votre situation…")
    if user_input:
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        st.session_state.history.append(f"Question: {user_input}")
        st.session_state.state = "RUN"
        st.rerun()

elif st.session_state.state == "RUN":
    run_agent()
    st.rerun()

elif st.session_state.state == "ASK":
    user_input = st.chat_input("Votre réponse…")
    if user_input:
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        st.session_state.history.append(f"Observation: {user_input}")
        st.session_state.state = "RUN"
        st.rerun()

elif st.session_state.state == "UPLOAD":
    st.markdown("""
    <div style="padding:16px; background:#f9fafb; border-radius:12px;
                border:1px dashed #9ca3af; margin-bottom:12px;">
    📎 <b>Document requis</b><br>
    Merci de déposer le fichier demandé ci-dessous.
    </div>
    """, unsafe_allow_html=True)

    file = st.file_uploader(" ", label_visibility="collapsed")

    if file:
        tool, params = st.session_state.pending_tool
        obs = f"Le document {params.get('name', 'document')} a été uploadé."
        st.session_state.messages.append({
            "role": "user",
            "content": f"📄 {file.name} envoyé avec succès"
        })
        st.session_state.history.append(f"Observation: {obs}")
        st.session_state.state = "RUN"
        st.rerun()

elif st.session_state.state == "DONE":
    st.success("✅ Votre déclaration est complète. Merci pour votre confiance.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Nouvelle déclaration"):
            st.session_state.clear()
            st.rerun()
    with col2:
        st.button("📞 Contacter un conseiller", disabled=True)