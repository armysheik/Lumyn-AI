from modules.audio_generator import generate_audio
import streamlit as st

st.set_page_config(
    page_title="Lumyn-AI | Smart Study Assistant",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import json

from database import (
    create_tables,
    save_quiz,
    save_flashcards,
    save_quiz_result,
    save_flashcard_activity,
    get_subjects,
    get_study_history,
    get_overall_progress,
    get_subject_progress,
    get_total_flashcards,
)

from modules.pdf_quiz.pdf_extractor import extract_text_from_pdf
from modules.pdf_quiz.quiz_generator import generate_quiz
from modules.flashcards.flashcard_generator import generate_flashcards

from modules.document_processing.txt_extractor import (
    extract_text_from_txt
)

from modules.document_processing.docx_extractor import (
    extract_text_from_docx
)

# ============================================================
# AUDIO GENERATOR
# ============================================================

try:
    from modules.audio_generator import generate_audio
    AUDIO_AVAILABLE = True
except Exception:
    AUDIO_AVAILABLE = False


# ============================================================
# YOUTUBE
# ============================================================

try:
    from modules.educational_content.youtube_api import (
        search_educational_videos
    )
    YOUTUBE_AVAILABLE = True
except Exception:
    YOUTUBE_AVAILABLE = False


# ============================================================
# INITIALIZE
# ============================================================

create_tables()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# SESSION STATE
# Initialize every state value before any UI/backend section
# accesses it. This prevents Streamlit session-state errors.
# ============================================================
defaults = {
    "quiz": None,
    "flashcards": None,
    "submitted": False,
    "score": 0,
    "quiz_subject": "General",
    "quiz_type": "MCQ",
    "quiz_difficulty": "Medium",
    "flashcard_subject": "General",
    "document_name": None,
    "extracted_text": "",
    "youtube_results": [],
    "audio_file": None,
    "chat_messages": [],
    "chat_subject": None,
    "app_page": "chat",
    "chat_history": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Keep the active conversation in Recents as it grows.
_current_messages = st.session_state.get("chat_messages", [])
if _current_messages:
    _first_user_message = next(
        (m.get("content", "") for m in _current_messages if m.get("role") == "user"),
        "Study conversation",
    )
    _current_title = _first_user_message.strip().replace("\n", " ")[:36] or "Study conversation"
    _saved_history = st.session_state.get("chat_history", [])
    _active_entry = {"title": _current_title, "messages": _current_messages.copy()}
    _saved_history = [h for h in _saved_history if h.get("title") != _current_title]
    _saved_history.insert(0, _active_entry)
    st.session_state.chat_history = _saved_history[:15]


# ============================================================
# CHATGPT-STYLE FRONTEND
# Existing backend modules below remain unchanged.
# ============================================================
st.markdown(r"""
<style>
:root{--bg:#212121;--sidebar:#171717;--panel:#2b2b2b;--panel-hover:#353535;--text:#ececec;--muted:#a1a1a1;--line:#3d3d3d;--white:#fff;--accent:#fff;}
html,body,[class*="css"]{font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important;}
html{scroll-behavior:smooth; background:var(--bg)!important;}
body,.stApp{background:var(--bg)!important;color:var(--text)!important;}
[data-testid="stHeader"]{background:rgba(33,33,33,.96)!important;border-bottom:1px solid #303030!important;}
[data-testid="stToolbar"],#MainMenu,footer{visibility:hidden!important;}
.block-container{max-width:900px;padding:1.25rem 1.35rem 7rem!important;}
[data-testid="stSidebar"]{background:var(--sidebar)!important;border-right:1px solid #292929!important;}
[data-testid="stSidebarContent"]{padding:.9rem .8rem!important;}
[data-testid="stSidebar"] *{color:var(--text)!important;}
.lumyn-brand{display:flex;align-items:center;gap:.68rem;margin:.15rem .4rem 1.25rem;color:var(--text)!important;font-size:1.04rem;font-weight:800;letter-spacing:.075em;}
.lumyn-brand .lumyn-logo{width:34px;height:34px;display:inline-flex;align-items:center;justify-content:center;border:1px solid #515151;border-radius:11px;background:linear-gradient(145deg,#f8f8f8,#cfcfcf);box-shadow:0 2px 10px rgba(0,0,0,.18);flex:0 0 auto;}
.lumyn-brand .lumyn-logo svg{width:23px;height:23px;display:block;}
.lumyn-brand .brand-name{color:#f5f5f5!important;}
.lumyn-brand .brand-name .brand-separator{color:#999!important;font-weight:500;}
.sidebar-label{color:#929292!important;font-size:.66rem;text-transform:uppercase;letter-spacing:.13em;margin:1.15rem .45rem .4rem;font-weight:750;}
.sidebar-item{display:block;color:#d4d4d4!important;text-decoration:none!important;padding:.68rem .72rem;margin:.16rem 0;border-radius:9px;font-size:.86rem;transition:background .16s ease;}
.sidebar-item:hover{background:#292929!important;color:#fff!important;}
.stButton>button{background:#252525!important;color:var(--text)!important;border:1px solid #444!important;border-radius:10px!important;font-weight:600!important;box-shadow:none!important;transition:background .16s ease,border-color .16s ease!important;}
.stButton>button:hover{background:#363636!important;border-color:#666!important;}
.chat-welcome{position:relative;overflow:hidden;background:transparent;color:var(--text);text-align:center;padding:4.3rem 1rem 2.4rem;margin:.3rem 0 .8rem;}
.chat-welcome:before{content:"";position:absolute;width:240px;height:240px;border:1px solid #333;border-radius:50%;top:-160px;right:-40px;pointer-events:none;}
.chat-welcome:after{content:"";position:absolute;width:130px;height:130px;border:1px solid #303030;border-radius:50%;bottom:-105px;left:-40px;pointer-events:none;}
.chat-welcome h1{position:relative;z-index:1;font-size:2.55rem;line-height:1.15;margin:0 0 .8rem;font-weight:680;letter-spacing:-.06em;color:var(--text)!important;}
.chat-welcome p{position:relative;z-index:1;color:#b4b4b4!important;margin:0 auto;max-width:620px;line-height:1.7;font-size:.94rem;}
.prompt-card,.home-mini-card,.feature-card{height:100%;background:#262626!important;border:1px solid #393939!important;border-radius:15px!important;padding:1rem 1.05rem;box-shadow:none!important;transition:background .16s ease,border-color .16s ease,transform .16s ease;}
.prompt-card{min-height:115px;margin-top:.5rem;}
.prompt-card:hover,.home-mini-card:hover,.feature-card:hover{background:#303030!important;border-color:#555!important;transform:translateY(-2px);}
.prompt-card .icon,.feature-icon{font-size:1rem;filter:grayscale(1);}
.prompt-card .title,.feature-title,.home-mini-card .mini-heading{font-weight:700;margin-top:.45rem;color:var(--text)!important;}
.prompt-card .desc,.feature-text,.home-mini-card .mini-copy{color:#b5b5b5!important;font-size:.8rem;line-height:1.55;margin-top:.3rem;}
.home-section-label{font-size:1.02rem;font-weight:700;letter-spacing:-.02em;color:var(--text)!important;margin:1.5rem 0 .65rem;}
.home-mini-card{min-height:125px;}
.home-mini-card .mini-kicker{font-size:.66rem;letter-spacing:.11em;text-transform:uppercase;color:#a3a3a3!important;font-weight:750;margin-bottom:.4rem;}
.home-mini-card .mini-symbol{display:inline-flex;width:27px;height:27px;border-radius:9px;align-items:center;justify-content:center;background:#3a3a3a;color:#fff!important;font-size:.8rem;margin-bottom:.5rem;}
/* Chat transcript: seamless dark canvas with restrained user bubbles. */
[data-testid="stChatMessage"]{background:transparent!important;color:var(--text)!important;border:0!important;padding:1.05rem .4rem!important;margin:0!important;}
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"]{background:#e7e7e7!important;color:#202020!important;border:1px solid #666!important;border-radius:11px!important;}
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"]{border-radius:11px!important;}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],[data-testid="stChatMessage"] p,[data-testid="stChatMessage"] li,[data-testid="stChatMessage"] span,[data-testid="stChatMessage"] strong{color:var(--text)!important;line-height:1.72;}
[data-testid="stChatMessage"] code{background:#3a3a3a!important;color:#f2f2f2!important;border-radius:5px;padding:.12rem .3rem;}
[data-testid="stChatMessage"] pre{background:#171717!important;color:#eee!important;border:1px solid #3b3b3b!important;border-radius:12px;padding:1rem;}
[data-testid="stChatMessage"] pre code{background:transparent!important;}
[data-testid="stChatMessage"] img{border-radius:10px;}
[data-testid="stChatInput"]{max-width:900px!important;}
[data-testid="stChatInput"]>div{background:#2f2f2f!important;border:1px solid #454545!important;border-radius:24px!important;box-shadow:0 2px 12px rgba(0,0,0,.18)!important;padding:.25rem .45rem!important;}
[data-testid="stChatInput"] textarea{background:transparent!important;color:#f5f5f5!important;caret-color:#fff!important;border:0!important;}
[data-testid="stChatInput"] textarea::placeholder{color:#a1a1a1!important;}
[data-testid="stChatInput"] button{color:#fff!important;background:#f1f1f1!important;border-radius:50%!important;}
[data-testid="stChatInput"] button svg{color:#171717!important;fill:#171717!important;}
.chat-status{text-align:center;color:#777!important;font-size:.7rem;margin:1.1rem 0 2rem;}
.section-shell{margin-top:3rem;padding-top:1.5rem;border-top:1px solid #383838;}
.tool-title{font-size:1.45rem;font-weight:720;letter-spacing:-.035em;color:var(--text)!important;}
.tool-caption,[data-testid="stCaptionContainer"]{color:#a1a1a1!important;font-size:.84rem;line-height:1.55;}
input,textarea,[data-baseweb="select"]>div{background:#262626!important;color:var(--text)!important;border-color:#454545!important;border-radius:10px!important;}
[data-testid="stFileUploader"]{background:#242424!important;border:1px dashed #505050!important;border-radius:14px!important;padding:.3rem!important;}
[data-testid="stFileUploaderDropzone"],[data-testid="stFileUploaderDropzone"]>div{background:#242424!important;color:var(--text)!important;}
[data-testid="stFileUploader"] *{color:var(--text)!important;}
[data-testid="stAlert"]{background:#292929!important;border:1px solid #444!important;border-radius:12px!important;color:var(--text)!important;}
[data-testid="stAlert"] *{background:transparent!important;color:var(--text)!important;}
[data-testid="stAlert"] svg,svg{filter:grayscale(1)!important;}
[data-testid="stMetric"]{background:#262626!important;border:1px solid #3b3b3b!important;border-radius:13px!important;padding:1rem!important;box-shadow:none!important;}
[data-testid="stMetricLabel"],[data-testid="stMetricValue"],[data-testid="stMetricDelta"]{color:var(--text)!important;}
[data-testid="stExpander"]{border:1px solid #414141!important;background:#252525!important;border-radius:12px!important;}
[data-testid="stExpander"] summary,[data-testid="stExpander"] p{color:var(--text)!important;}
h1,h2,h3,h4,h5,h6,p,label,.stMarkdown{color:var(--text);}
hr{border-color:#3c3c3c!important;}
a{color:#e5e5e5!important;}
.footer{text-align:center;color:#888!important;padding:2rem 0 .5rem;font-size:.72rem;letter-spacing:.02em;}
[data-testid="stStatusWidget"],[data-testid="stProgressBar"]{filter:grayscale(1)!important;}
.lumyn-wordmark{display:inline-flex;align-items:center;gap:.6rem;animation:wordmark-in .7s ease both;text-transform:uppercase;letter-spacing:.08em!important;}
.lumyn-wordmark .welcome-logo{width:43px;height:43px;display:inline-flex;align-items:center;justify-content:center;background:linear-gradient(145deg,#fafafa,#cfcfcf);border:1px solid #555;border-radius:14px;box-shadow:0 5px 22px rgba(0,0,0,.2);vertical-align:middle;}
.lumyn-wordmark .welcome-logo svg{width:29px;height:29px;}
.lumyn-wordmark .lumyn-dot{display:inline-block;width:6px;height:6px;background:#f5f5f5;border-radius:50%;margin:0 0 2px 1px;animation:dot-pulse 1.8s ease-in-out infinite;}
.animated-tagline{margin:.95rem auto 0!important;letter-spacing:.08em;text-transform:uppercase;font-size:.72rem!important;color:#a8a8a8!important;animation:fade-rise 1s ease both;}
.animated-tagline .tagline-track{display:inline-block;animation:tagline-float 4s ease-in-out infinite;}
@keyframes wordmark-in{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@keyframes dot-pulse{0%,100%{opacity:.45;transform:scale(.85)}50%{opacity:1;transform:scale(1.12)}}
@keyframes fade-rise{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
@keyframes tagline-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-2px)}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;scroll-behavior:auto!important;transition:none!important}}
@media(max-width:800px){.block-container{padding-left:.8rem!important;padding-right:.8rem!important}.chat-welcome{padding:3rem .7rem 1.7rem}.chat-welcome h1{font-size:2rem}.prompt-card{min-height:100px}}

/* Cleaner split between the conversation and the dedicated learning hub. */
[data-testid="stSidebar"] .stButton>button{width:100%;text-align:left!important;justify-content:flex-start!important;background:transparent!important;border-color:transparent!important;padding:.62rem .7rem!important;border-radius:9px!important;font-weight:500!important;}
[data-testid="stSidebar"] .stButton>button:hover{background:#292929!important;border-color:#333!important;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.35rem!important;}
[data-testid="stChatMessage"]{max-width:760px;margin-left:auto!important;margin-right:auto!important;padding:.8rem .2rem!important;}
[data-testid="stChatInput"]{max-width:800px!important;margin-left:auto!important;margin-right:auto!important;}
.chat-welcome{padding:5.1rem 1rem 2.8rem!important;}
.learning-page-head{padding:1.3rem 0 1.6rem;border-bottom:1px solid #3a3a3a;margin-bottom:1.5rem;}
.learning-page-head .learning-eyebrow{font-size:.68rem;letter-spacing:.16em;color:#a0a0a0;font-weight:750;margin-bottom:.55rem;}
.learning-page-head h1{font-size:2rem;letter-spacing:-.045em;margin:0 0 .45rem;color:#f5f5f5!important;}
.learning-page-head p{margin:0;color:#a9a9a9!important;max-width:700px;line-height:1.6;}

</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR — CHATGPT-STYLE WORKSPACE
# ============================================================
with st.sidebar:
    st.markdown('''<div class="lumyn-brand"><span class="lumyn-logo"><svg viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M24 5.5 28.5 18 41 22.5 28.5 27 24 39.5 19.5 27 7 22.5 19.5 18 24 5.5Z" fill="#202020"/><circle cx="24" cy="22.5" r="4.2" fill="#f8f8f8"/><path d="M34.5 8.5c4.8 3.1 7.5 8.2 7.5 14 0 9.9-8.1 18-18 18S6 32.4 6 22.5" stroke="#555" stroke-width="2.2" stroke-linecap="round"/></svg></span><span class="brand-name">LUMYN<span class="brand-separator">_</span>AI</span></div>''', unsafe_allow_html=True)

    if st.button("＋  New chat", use_container_width=True, key="new_chat_button"):
        current = st.session_state.get("chat_messages", [])
        if current:
            first_user = next((m.get("content", "") for m in current if m.get("role") == "user"), "Study conversation")
            title = first_user.strip().replace("\n", " ")[:36] or "Study conversation"
            history = st.session_state.get("chat_history", [])
            history = [h for h in history if h.get("messages") != current]
            history.insert(0, {"title": title, "messages": current.copy()})
            st.session_state.chat_history = history[:15]
        st.session_state.chat_messages = []
        st.session_state.chat_subject = None
        st.session_state.app_page = "chat"
        st.rerun()

    if st.button("▦  You can learn here", use_container_width=True, key="learning_page_button"):
        st.session_state.app_page = "learn"
        st.rerun()

    if st.session_state.get("app_page") == "learn":
        if st.button("←  Back to chat", use_container_width=True, key="back_to_chat_button"):
            st.session_state.app_page = "chat"
            st.rerun()

    st.markdown('<div class="sidebar-label">Recents</div>', unsafe_allow_html=True)
    history = st.session_state.get("chat_history", [])
    if history:
        for idx, conversation in enumerate(history):
            title = conversation.get("title", "Study conversation")
            if st.button("◷  " + title, key=f"recent_chat_{idx}", use_container_width=True):
                st.session_state.chat_messages = conversation.get("messages", []).copy()
                st.session_state.app_page = "chat"
                st.rerun()
    elif not st.session_state.get("chat_messages"):
        st.caption("Your conversations will appear here.")
    else:
        first_user = next((m.get("content", "") for m in st.session_state.chat_messages if m.get("role") == "user"), "Current conversation")
        st.caption(first_user[:42])

    st.markdown('<div class="sidebar-label">Study context</div>', unsafe_allow_html=True)
    if st.session_state.get("document_name"):
        st.caption("📄 " + str(st.session_state.document_name))
    else:
        st.caption("No document loaded")
    st.caption("Lumyn-AI · Groq study assistant")

# ============================================================
# CHAT AGENT — OPTIONAL FRONTEND LAYER
# Existing quiz, flashcard, audio, YouTube and database logic is untouched.
# ============================================================
def _lumyn_chat_response(user_message, study_text):
    """Generate a conversational response without modifying existing generators."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured in the .env file.")

    try:
        from langchain_groq import ChatGroq
    except Exception as error:
        raise RuntimeError(f"Chat model dependency is unavailable: {error}") from error

    context = (study_text or "").strip()
    if len(context) > 14000:
        context = context[:14000] + "\n[Study material truncated for chat context.]"

    system_prompt = """You are Lumyn-AI, a friendly, motivating AI study assistant built to help
students learn consistently through daily practice.

CORE CAPABILITIES AND TONE:
- Explain concepts, summarize uploaded notes, answer study questions, and help students revise.
- Encourage students to use Lumyn-AI's available quizzes, flashcards, and learning resources
  every day. Explain that these tools can help them practise, review topics, and build consistent
  study habits.
- When a student asks whether Lumyn-AI can track their study activity or progress, respond
  positively but accurately: Lumyn-AI can help them review the study activity and results that
  the app actually records, such as completed quizzes, scores, flashcard practice, and resources
  used when those records are available. Encourage them to keep using the app daily to build
  their learning history. Do not say that Lumyn-AI can see their real-world activity, monitor them
  continuously, or track actions that the app does not record. Never claim that a specific activity
  or score has been saved or tracked unless that information is available in the conversation or app.
- Prefer inviting, product-specific wording such as: "Yes! Lumyn-AI helps you build and review your
  study progress right here. Practise daily with quizzes, revise with flashcards, and explore learning
  resources. As you use these tools, you can review the activity and results the app records to see
  how your learning is progressing. Let's keep your learning streak going!"
- Answer clearly and naturally like a modern study chatbot. If study material is provided, use it as
  the primary source and do not invent details that conflict with it. If the material does not contain
  the answer, say so and, when appropriate, give a clearly identified general explanation.
- Keep answers concise unless the student asks for detail. Be encouraging without making promises
  about features or data that are not available."""

    if context:
        system_prompt += f"\n\nUPLOADED STUDY MATERIAL:\n{context}"
    else:
        system_prompt += "\n\nNo study material has been uploaded yet."

    history = []
    for item in st.session_state.chat_messages[-10:]:
        role = item.get("role")
        content = item.get("content", "")
        if role in {"user", "assistant"} and content:
            history.append((role, content))

    model = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.3,
        groq_api_key=api_key,
    )

    messages = [("system", system_prompt)]
    messages.extend(history)
    messages.append(("user", user_message))
    result = model.invoke(messages)
    return getattr(result, "content", str(result)).strip()


# ============================================================
# CHAT PAGE — conversation only
# ============================================================
if st.session_state.get("app_page", "chat") == "chat":
    st.markdown('<div id="study-chat"></div>', unsafe_allow_html=True)

    if not st.session_state.chat_messages:
        st.markdown(
            """<div class="chat-welcome">
            <h1 class="lumyn-wordmark"><span class="welcome-logo"><svg viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M24 5.5 28.5 18 41 22.5 28.5 27 24 39.5 19.5 27 7 22.5 19.5 18 24 5.5Z" fill="#202020"/><circle cx="24" cy="22.5" r="4.2" fill="#f8f8f8"/><path d="M34.5 8.5c4.8 3.1 7.5 8.2 7.5 14 0 9.9-8.1 18-18 18S6 32.4 6 22.5" stroke="#555" stroke-width="2.2" stroke-linecap="round"/></svg></span><span>LUMYN_AI<span class="lumyn-dot"></span></span></h1>
            <p>Meet your personal AI study companion. Learn concepts, explore your notes, and turn study time into progress.</p>
            <p class="animated-tagline"><span class="tagline-track">Learn&nbsp; · &nbsp;Practice&nbsp; · &nbsp;Review&nbsp; · &nbsp;Improve&nbsp; · &nbsp;Master</span></p>
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown('<div class="home-section-label">Start with Lumyn</div>', unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown('<div class="prompt-card"><div class="icon">💡</div><div class="title">Explain a concept</div><div class="desc">Ask for a simple or detailed explanation.</div></div>', unsafe_allow_html=True)
        with p2:
            st.markdown('<div class="prompt-card"><div class="icon">📚</div><div class="title">Summarize my material</div><div class="desc">Turn your uploaded notes into a quick revision guide.</div></div>', unsafe_allow_html=True)
        with p3:
            st.markdown('<div class="prompt-card"><div class="icon">🎯</div><div class="title">Prepare for an exam</div><div class="desc">Ask for key points, examples, or revision help.</div></div>', unsafe_allow_html=True)
    else:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"], avatar=("✦" if message["role"] == "assistant" else "👤")):
                st.markdown(message["content"])

    prompt = st.chat_input("Message Lumyn-AI…")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="✦"):
            with st.spinner("Thinking…"):
                try:
                    response = _lumyn_chat_response(prompt, st.session_state.get("extracted_text", ""))
                except Exception as error:
                    response = f"I couldn't process that request right now.\n\n**Error:** {error}"
            st.markdown(response)

        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        # Redraw from chat history so the welcome cards do not remain above the new turn.
        st.rerun()

    st.markdown('<div class="chat-status">Lumyn-AI can make mistakes. Check important information against your study material.</div>', unsafe_allow_html=True)

    # Streamlit does not consistently scroll to a newly submitted chat turn by itself.
    # Scroll the latest message into view after the transcript has rendered.
    if st.session_state.chat_messages:
        st.components.v1.html("""
        <script>
        (() => {
          const scrollToLatest = () => {
            try {
              const doc = window.parent.document;
              const messages = doc.querySelectorAll('[data-testid="stChatMessage"]');
              if (messages.length) {
                messages[messages.length - 1].scrollIntoView({behavior: 'smooth', block: 'end'});
              }
            } catch (e) {}
          };
          setTimeout(scrollToLatest, 120);
          setTimeout(scrollToLatest, 450);
        })();
        </script>
        """, height=0, scrolling=False)


# ============================================================
# LEARNING HUB — separate page opened from the sidebar
# ============================================================
if st.session_state.get("app_page") == "learn":
    st.markdown('<div class="learning-page-head"><div class="learning-eyebrow">LUMYN-AI WORKSPACE</div><h1>You can learn here</h1><p>Upload your own material, practise with AI, and explore useful resources in one place.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="home-section-label">Your learning space</div>', unsafe_allow_html=True)
    summary_cols = st.columns(2)
    with summary_cols[0]:
        st.markdown('<div class="home-mini-card"><div class="mini-symbol">✦</div><div class="mini-kicker">Personal guidance</div><div class="mini-heading">Smart Study Recommendation</div><div class="mini-copy">Get a study next-step suggestion based on your learning activity, quiz performance, and revision progress.</div></div>', unsafe_allow_html=True)
    with summary_cols[1]:
        st.markdown('<div class="home-mini-card"><div class="mini-symbol">★</div><div class="mini-kicker">Celebrate progress</div><div class="mini-heading">Achievements</div><div class="mini-copy">Build momentum as you complete quizzes, create flashcards, and strengthen your study routine.</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-shell"></div>', unsafe_allow_html=True)
    st.markdown('<div class="tool-title">Study tools</div><div class="tool-caption">Upload a PDF, DOCX, or TXT file to generate quizzes and flashcards, listen to summaries, and discover related learning videos.</div>', unsafe_allow_html=True)

    # ============================================================
    # MEMBER 1 - YOUTUBE EDUCATIONAL CONTENT
    # ============================================================

    f1, f2, f3 = st.columns(3)

    with f1:
        st.markdown("""<div class=\"feature-card\"><div class=\"feature-icon\">📄</div><div class=\"feature-title\">Upload & Learn</div><div class=\"feature-text\">Import PDF, TXT or DOCX content and extract it for AI-powered study.</div></div>""", unsafe_allow_html=True)
    with f2:
        st.markdown("""<div class=\"feature-card\"><div class=\"feature-icon\">🧠</div><div class=\"feature-title\">Practice with AI</div><div class=\"feature-text\">Generate quizzes and flashcards from your own learning material.</div></div>""", unsafe_allow_html=True)
    with f3:
        st.markdown("""<div class=\"feature-card\"><div class=\"feature-icon\">📊</div><div class=\"feature-title\">Track Progress</div><div class=\"feature-text\">Review scores, accuracy, subjects, history and achievements.</div></div>""", unsafe_allow_html=True)

    st.markdown('<div id="educational-content"></div>', unsafe_allow_html=True)
    st.header("📺 Educational Content")

    st.write(
        "Search YouTube for educational videos related to "
        "the topic you are studying."
    )

    if not YOUTUBE_AVAILABLE:

        st.warning(
            "YouTube educational content module is not available. "
            "Check that "
            "modules/educational_content/youtube_api.py exists."
        )

    else:

        youtube_topic = st.text_input(
            "🔎 Search educational videos",
            placeholder=(
                "Example: Python programming, "
                "Machine Learning, Flutter"
            ),
            key="youtube_topic",
        )

        youtube_count = st.slider(
            "Number of videos",
            min_value=1,
            max_value=10,
            value=6,
            key="youtube_count",
        )

        if st.button(
            "🔍 Search Educational Videos",
            use_container_width=True,
        ):

            if not youtube_topic.strip():

                st.warning(
                    "Please enter a topic first."
                )

            else:

                try:

                    with st.spinner(
                        "Searching YouTube educational videos..."
                    ):

                        results = search_educational_videos(
                            youtube_topic.strip(),
                            youtube_count,
                        )

                    st.session_state.youtube_results = results

                    if results:

                        st.success(
                            f"Found {len(results)} educational "
                            f"video(s) for "
                            f"'{youtube_topic.strip()}'."
                        )

                    else:

                        st.info(
                            "No educational videos were found "
                            "for this topic."
                        )

                except Exception as error:

                    st.error(
                        f"❌ YouTube search failed:\n\n{error}"
                    )


        # --------------------------------------------------------
        # DISPLAY YOUTUBE RESULTS
        # --------------------------------------------------------

        if st.session_state.youtube_results:

            st.subheader(
                "🎓 Recommended Educational Videos"
            )

            for video in st.session_state.youtube_results:

                with st.container(border=True):

                    col1, col2 = st.columns([1, 2])


                    # ------------------------------------------------
                    # THUMBNAIL
                    # ------------------------------------------------

                    with col1:

                        if video.get("thumbnail_url"):

                            st.image(
                                video["thumbnail_url"],
                                use_container_width=True,
                            )


                    # ------------------------------------------------
                    # VIDEO DETAILS
                    # ------------------------------------------------

                    with col2:

                        st.markdown(
                            f"### {video.get('title', 'Untitled')}"
                        )

                        st.write(
                            f"**Channel:** "
                            f"{video.get('channel_title', 'Unknown')}"
                        )

                        description = video.get(
                            "description",
                            "",
                        )

                        if description:

                            st.write(
                                description[:400]
                            )

                        video_url = video.get(
                            "url",
                            "",
                        )

                        if video_url:

                            st.markdown(
                                f"[▶ Watch on YouTube]({video_url})"
                            )


    st.divider()


    # ============================================================
    # GET SUBJECTS FROM DATABASE
    # ============================================================

    try:

        subjects = get_subjects()

    except Exception:

        subjects = ["General"]


    if not subjects:

        subjects = ["General"]


    if "General" not in subjects:

        subjects.insert(0, "General")


    # ============================================================
    # DOCUMENT UPLOAD
    # ============================================================

    st.markdown('<div id="study-material"></div>', unsafe_allow_html=True)
    st.header("📤 Upload Your Study Material")

    uploaded_file = st.file_uploader(
        "Upload your document",
        type=[
            "pdf",
            "txt",
            "docx",
        ],
        help="Supported formats: PDF, TXT and DOCX",
    )


    # ============================================================
    # PROCESS UPLOADED DOCUMENT
    # ============================================================

    if uploaded_file is not None:

        st.success(
            f"✅ Uploaded: {uploaded_file.name}"
        )


        # --------------------------------------------------------
        # EMPTY FILE VALIDATION
        # --------------------------------------------------------

        if uploaded_file.size == 0:

            st.error(
                "❌ The uploaded file is empty. "
                "Please choose a file that contains content."
            )

            st.stop()


        file_name = uploaded_file.name.lower()


        # --------------------------------------------------------
        # DETECT FILE TYPE
        # --------------------------------------------------------

        if file_name.endswith(".pdf"):

            file_type = "PDF"

        elif file_name.endswith(".txt"):

            file_type = "TXT"

        elif file_name.endswith(".docx"):

            file_type = "DOCX"

        else:

            file_type = "UNKNOWN"


        st.info(
            f"📄 File type detected: **{file_type}**"
        )


        # --------------------------------------------------------
        # TEMPORARY FILE
        # --------------------------------------------------------

        file_extension = os.path.splitext(
            uploaded_file.name
        )[1].lower()

        temp_file_path = os.path.join(
            BASE_DIR,
            f"uploaded_temp{file_extension}",
        )


        try:

            with open(
                temp_file_path,
                "wb",
            ) as file:

                file.write(
                    uploaded_file.getbuffer()
                )


            extracted_text = ""


            # ----------------------------------------------------
            # EXTRACT TEXT
            # ----------------------------------------------------

            with st.spinner(
                f"📖 Extracting text from {file_type}..."
            ):

                if file_type == "PDF":

                    extracted_text = extract_text_from_pdf(
                        temp_file_path
                    )

                elif file_type == "TXT":

                    extracted_text = extract_text_from_txt(
                        temp_file_path
                    )

                elif file_type == "DOCX":

                    extracted_text = extract_text_from_docx(
                        temp_file_path
                    )

                else:

                    raise ValueError(
                        "Unsupported document format."
                    )


            # ----------------------------------------------------
            # CHECK TEXT
            # ----------------------------------------------------

            if (
                not extracted_text
                or not extracted_text.strip()
            ):

                raise ValueError(
                    "No readable text was found in "
                    "the document."
                )


            st.session_state.extracted_text = (
                extracted_text
            )

            st.session_state.document_name = (
                uploaded_file.name
            )


            st.success(
                f"✅ {file_type} text extracted successfully!"
            )


            # ----------------------------------------------------
            # VIEW TEXT
            # ----------------------------------------------------

            with st.expander(
                "📄 View Extracted Text"
            ):

                st.text_area(
                    "Extracted Text",
                    extracted_text,
                    height=300,
                    key="extracted_text_view",
                )


        except Exception as error:

            st.session_state.extracted_text = ""

            st.error(
                f"❌ {file_type} extraction failed:\n\n"
                f"{error}"
            )


        finally:

            if os.path.exists(temp_file_path):

                try:

                    os.remove(temp_file_path)

                except OSError:

                    pass


    # ============================================================
    # GET EXTRACTED TEXT
    # ============================================================

    extracted_text = st.session_state.extracted_text


    # ============================================================
    # GENERATORS
    # ============================================================

    if extracted_text:

        st.divider()


        # ========================================================
        # STUDY ORGANIZATION
        # ========================================================

        st.header("📚 Study Organization")

        subject_option = st.selectbox(
            "📖 Select Subject",
            subjects,
            key="subject_select",
        )

        custom_subject = st.text_input(
            "Or enter a new subject",
            placeholder=(
                "Example: Python, Java, DBMS, "
                "Machine Learning"
            ),
        )

        if custom_subject.strip():

            selected_subject = (
                custom_subject.strip()
            )

        else:

            selected_subject = subject_option


        st.info(
            f"Current study subject: "
            f"**{selected_subject}**"
        )

        st.divider()


        # ========================================================
        # QUIZ GENERATOR
        # ========================================================

        st.markdown('<div id="quiz-generator"></div>', unsafe_allow_html=True)
        st.header("📝 Quiz Generator")

        col1, col2, col3 = st.columns(3)


        # --------------------------------------------------------
        # NUMBER OF QUESTIONS
        # --------------------------------------------------------

        with col1:

            num_questions = st.slider(
                "📝 Number of questions",
                min_value=1,
                max_value=10,
                value=3,
            )


        # --------------------------------------------------------
        # DIFFICULTY
        # --------------------------------------------------------

        with col2:

            difficulty = st.selectbox(
                "🎯 Select Difficulty",
                [
                    "Easy",
                    "Medium",
                    "Hard",
                ],
                index=1,
            )


        # --------------------------------------------------------
        # QUIZ TYPE
        # --------------------------------------------------------

        with col3:

            quiz_type = st.selectbox(
                "📝 Select Quiz Type",
                [
                    "MCQ",
                    "True/False",
                    "Fill-in-the-Blanks",
                ],
            )


        st.info(
            f"Selected: **{difficulty}** difficulty | "
            f"**{quiz_type}** format | "
            f"**{num_questions}** questions | "
            f"**{selected_subject}** subject"
        )


        # ========================================================
        # GENERATE QUIZ BUTTON
        # ========================================================

        if st.button(
            "🚀 Generate Quiz",
            use_container_width=True,
            key="generate_quiz_button",
        ):

            try:

                with st.spinner(
                    f"🤖 Generating "
                    f"{difficulty} {quiz_type} quiz..."
                ):

                    quiz = generate_quiz(
                        extracted_text,
                        num_questions,
                        difficulty,
                        quiz_type,
                    )


                # ------------------------------------------------
                # CONVERT JSON STRING
                # ------------------------------------------------

                if isinstance(
                    quiz,
                    str,
                ):

                    quiz = quiz.strip()

                    quiz = quiz.replace(
                        "```json",
                        "",
                    )

                    quiz = quiz.replace(
                        "```",
                        "",
                    )

                    quiz = json.loads(
                        quiz.strip()
                    )


                # ------------------------------------------------
                # VALIDATE
                # ------------------------------------------------

                if (
                    not isinstance(
                        quiz,
                        list,
                    )
                    or len(quiz) == 0
                ):

                    raise ValueError(
                        "AI returned an invalid "
                        "or empty quiz."
                    )


                # ------------------------------------------------
                # SAVE QUIZ
                # ------------------------------------------------

                save_quiz(
                    quiz,
                    subject=selected_subject,
                    quiz_type=quiz_type,
                    difficulty=difficulty,
                )


                # ------------------------------------------------
                # SESSION
                # ------------------------------------------------

                st.session_state.quiz = quiz

                st.session_state.submitted = False

                st.session_state.score = 0

                st.session_state.quiz_subject = (
                    selected_subject
                )

                st.session_state.quiz_type = (
                    quiz_type
                )

                st.session_state.quiz_difficulty = (
                    difficulty
                )


                st.success(
                    f"🎉 {difficulty} {quiz_type} "
                    f"quiz generated successfully!"
                )


            except Exception as error:

                st.error(
                    f"❌ Quiz generation failed:\n\n"
                    f"{error}"
                )


        # ========================================================
        # FLASHCARD GENERATOR
        # ========================================================

        st.divider()

        st.markdown('<div id="flashcards"></div>', unsafe_allow_html=True)
        st.header("🧠 Flashcard Generator")

        flashcard_subject = st.text_input(
            "📚 Flashcard Subject",
            value=selected_subject,
            key="flashcard_subject_input",
        )


        if flashcard_subject.strip():

            flashcard_subject = (
                flashcard_subject.strip()
            )

        else:

            flashcard_subject = "General"


        num_flashcards = st.slider(
            "🧠 Number of flashcards",
            min_value=1,
            max_value=20,
            value=5,
        )


        # ========================================================
        # GENERATE FLASHCARDS
        # ========================================================

        if st.button(
            "🧠 Generate Flashcards",
            use_container_width=True,
            key="generate_flashcards_button",
        ):

            try:

                with st.spinner(
                    "🤖 AI is generating "
                    "your flashcards..."
                ):

                    flashcards = generate_flashcards(
                        extracted_text,
                        num_flashcards,
                    )


                # ------------------------------------------------
                # CONVERT JSON STRING
                # ------------------------------------------------

                if isinstance(
                    flashcards,
                    str,
                ):

                    flashcards = flashcards.strip()

                    flashcards = flashcards.replace(
                        "```json",
                        "",
                    )

                    flashcards = flashcards.replace(
                        "```",
                        "",
                    )

                    flashcards = json.loads(
                        flashcards.strip()
                    )


                # ------------------------------------------------
                # VALIDATE
                # ------------------------------------------------

                if (
                    not isinstance(
                        flashcards,
                        list,
                    )
                    or len(flashcards) == 0
                ):

                    raise ValueError(
                        "AI returned invalid "
                        "or empty flashcards."
                    )


                # ------------------------------------------------
                # SAVE FLASHCARDS
                # ------------------------------------------------

                save_flashcards(
                    flashcards,
                    subject=flashcard_subject,
                )


                # ------------------------------------------------
                # SAVE ACTIVITY
                # ------------------------------------------------

                try:

                    save_flashcard_activity(
                        flashcard_subject,
                        len(flashcards),
                    )

                except Exception as error:

                    st.warning(
                        "Flashcards were generated successfully, "
                        "but the activity could not be saved: "
                        f"{error}"
                    )


                # ------------------------------------------------
                # SESSION
                # ------------------------------------------------

                st.session_state.flashcards = (
                    flashcards
                )

                st.session_state.flashcard_subject = (
                    flashcard_subject
                )


                st.success(
                    f"🎉 {len(flashcards)} flashcards "
                    f"generated successfully!"
                )


            except Exception as error:

                st.error(
                    f"❌ Flashcard generation failed:\n\n"
                    f"{error}"
                )


    # ============================================================
    # DISPLAY QUIZ
    # ============================================================

    if st.session_state.quiz is not None:

        st.divider()

        st.header("📝 Your Quiz")

        quiz = st.session_state.quiz

        answers = {}


        # --------------------------------------------------------
        # QUESTIONS
        # --------------------------------------------------------

        for i, question_data in enumerate(
            quiz
        ):

            st.markdown(
                f"### Question {i + 1}"
            )

            st.write(
                question_data.get(
                    "question",
                    "",
                )
            )


            # ----------------------------------------------------
            # DIFFICULTY
            # ----------------------------------------------------

            if "difficulty" in question_data:

                st.caption(
                    f"🎯 Difficulty: "
                    f"{question_data['difficulty']}"
                )


            # ----------------------------------------------------
            # MCQ / TRUE-FALSE
            # ----------------------------------------------------

            if "options" in question_data:

                options = question_data[
                    "options"
                ]

                if isinstance(
                    options,
                    dict,
                ):

                    option_keys = list(
                        options.keys()
                    )

                    selected = st.radio(
                        "Select your answer:",
                        option_keys,
                        format_func=lambda key: (
                            f"{key}. "
                            f"{options[key]}"
                        ),
                        key=f"answer_{i}",
                    )

                    answers[i] = selected


            # ----------------------------------------------------
            # FILL IN THE BLANK
            # ----------------------------------------------------

            else:

                answers[i] = st.text_input(
                    "✏️ Your answer:",
                    key=f"answer_{i}",
                )


            st.divider()


        # ========================================================
        # SUBMIT QUIZ
        # ========================================================

        if st.button(
            "✅ Submit Quiz",
            use_container_width=True,
            key="submit_quiz_button",
        ):

            score = 0


            for i, question_data in enumerate(
                quiz
            ):

                correct_answer = str(
                    question_data.get(
                        "answer",
                        "",
                    )
                ).strip()

                user_answer = str(
                    answers.get(
                        i,
                        "",
                    )
                ).strip()


                # ------------------------------------------------
                # DIRECT ANSWER CHECK
                # ------------------------------------------------

                if (
                    user_answer.lower()
                    == correct_answer.lower()
                ):

                    score += 1


                # ------------------------------------------------
                # ACCEPTED ANSWERS
                # ------------------------------------------------

                elif (
                    "accepted_answers"
                    in question_data
                ):

                    accepted_answers = (
                        question_data.get(
                            "accepted_answers",
                            [],
                        )
                    )

                    accepted_answers = [
                        str(answer)
                        .strip()
                        .lower()
                        for answer
                        in accepted_answers
                    ]

                    if (
                        user_answer.lower()
                        in accepted_answers
                    ):

                        score += 1


            # ----------------------------------------------------
            # SAVE SESSION RESULT
            # ----------------------------------------------------

            st.session_state.score = score

            st.session_state.submitted = True


            # ----------------------------------------------------
            # SAVE RESULT TO SQLITE
            # ----------------------------------------------------

            try:

                save_quiz_result(
                    subject=(
                        st.session_state.quiz_subject
                    ),
                    quiz_type=(
                        st.session_state.quiz_type
                    ),
                    difficulty=(
                        st.session_state.quiz_difficulty
                    ),
                    score=score,
                    total_questions=len(quiz),
                )

            except Exception as error:

                st.warning(
                    "Quiz completed, but result "
                    "could not be saved: "
                    f"{error}"
                )


            st.rerun()


    # ============================================================
    # QUIZ RESULT
    # ============================================================

    if (
        st.session_state.quiz is not None
        and st.session_state.submitted
    ):

        quiz = st.session_state.quiz

        score = st.session_state.score

        total = len(quiz)


        if total > 0:

            percentage = (
                score / total
            ) * 100

        else:

            percentage = 0


        st.divider()

        st.header("🎯 Quiz Result")


        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(
                "🏆 Score",
                f"{score} / {total}",
            )


        with col2:

            st.metric(
                "📊 Accuracy",
                f"{percentage:.1f}%",
            )


        with col3:

            st.metric(
                "📚 Subject",
                st.session_state.quiz_subject,
            )


        st.progress(
            min(
                percentage / 100,
                1.0,
            )
        )


        if percentage >= 80:

            st.success(
                "🏆 Excellent! Great job!"
            )

        elif percentage >= 50:

            st.warning(
                "👍 Good attempt! Keep practicing."
            )

        else:

            st.error(
                "📚 Keep learning and try again."
            )


        # ========================================================
        # ANSWER REVIEW
        # ========================================================

        st.subheader(
            "📖 Answer Review"
        )


        for i, question_data in enumerate(
            quiz
        ):

            correct = question_data.get(
                "answer",
                "",
            )

            st.write(
                f"**Question {i + 1}:** "
                f"Correct Answer → **{correct}**"
            )


    # ============================================================
    # DISPLAY FLASHCARDS
    # ============================================================

    if st.session_state.flashcards is not None:

        st.divider()

        st.header("🧠 Your Flashcards")

        flashcards = (
            st.session_state.flashcards
        )


        st.caption(
            f"Subject: "
            f"{st.session_state.flashcard_subject}"
        )


        for i, card in enumerate(
            flashcards,
            start=1,
        ):

            with st.container(
                border=True
            ):

                st.markdown(
                    f"### 🗂️ Flashcard {i}"
                )

                st.write(
                    f"**Question:** "
                    f"{card.get('question', '')}"
                )

                with st.expander(
                    "👀 Show Answer"
                ):

                    st.write(
                        card.get(
                            "answer",
                            "",
                        )
                    )


    # ============================================================
    # AUDIO SUMMARY
    # ============================================================

    if extracted_text:

        st.divider()

        st.markdown('<div id="audio-summary"></div>', unsafe_allow_html=True)
        st.header("🔊 Audio Study Summary")

        st.write(
            "Listen to an AI-generated audio version "
            "of your study material."
        )


        if not AUDIO_AVAILABLE:

            st.warning(
                "Audio generation is not available. "
                "Make sure pyttsx3 is installed in the "
                "active virtual environment."
            )

        else:

            audio_text = extracted_text.strip()


            # Limit extremely large documents so that
            # text-to-speech does not become unnecessarily long.
            max_audio_characters = 5000

            if len(audio_text) > max_audio_characters:

                audio_text = (
                    audio_text[:max_audio_characters]
                    + "..."
                )

                st.caption(
                    "ℹ️ The audio summary is limited to "
                    "the first 5,000 characters."
                )


            if st.button(
                "🔊 Generate Audio",
                use_container_width=True,
                key="generate_audio_button",
            ):

                try:

                    with st.spinner(
                        "🎙️ Generating audio..."
                    ):

                        audio_file = generate_audio(
                            audio_text,
                            os.path.join(
                                BASE_DIR,
                                "study_summary.wav"
                            ),
                        )


                    st.session_state.audio_file = (
                        audio_file
                    )

                    st.success(
                        "🎉 Audio generated successfully!"
                    )


                except Exception as error:

                    st.session_state.audio_file = None

                    st.error(
                        f"❌ Audio generation failed:\n\n"
                        f"{error}"
                    )


            # ----------------------------------------------------
            # AUDIO PLAYER
            # ----------------------------------------------------

            audio_file = st.session_state.audio_file

            if (
                audio_file
                and os.path.exists(audio_file)
            ):

                try:

                    with open(
                        audio_file,
                        "rb",
                    ) as audio:

                        audio_bytes = audio.read()


                    st.audio(
                        audio_bytes,
                        format="audio/wav",
                    )

                    st.caption(
                        "▶️ Press play to listen to your study material."
                    )


                except Exception as error:

                    st.error(
                        f"❌ Could not load audio file: "
                        f"{error}"
                    )


    # ============================================================
    # MEMBER 1 - PERSISTENT STUDY DASHBOARD
    # ============================================================

    st.divider()

    st.markdown('<div id="learning-dashboard"></div>', unsafe_allow_html=True)
    st.header(
        "📊 Your Learning Dashboard"
    )

    st.write(
        "Your study activity is stored in SQLite "
        "so your quiz scores, subjects, and progress "
        "can be viewed again."
    )


    # ============================================================
    # OVERALL PROGRESS
    # ============================================================

    try:

        overall = get_overall_progress()

    except Exception:

        overall = {
            "quizzes_taken": 0,
            "total_questions": 0,
            "correct_answers": 0,
            "accuracy": 0,
        }


    # ============================================================
    # TOTAL FLASHCARDS
    # ============================================================

    try:

        total_flashcards = (
            get_total_flashcards()
        )

    except Exception:

        total_flashcards = 0


    quizzes_taken = overall.get(
        "quizzes_taken",
        0,
    )

    total_questions = overall.get(
        "total_questions",
        0,
    )

    correct_answers = overall.get(
        "correct_answers",
        0,
    )

    accuracy = overall.get(
        "accuracy",
        0,
    )


    # ============================================================
    # LEARNING METRICS
    # ============================================================

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "📝 Quizzes Taken",
            quizzes_taken,
        )


    with col2:

        st.metric(
            "❓ Questions",
            total_questions,
        )


    with col3:

        st.metric(
            "✅ Correct",
            correct_answers,
        )


    with col4:

        st.metric(
            "🧠 Flashcards",
            total_flashcards,
        )


    # ============================================================
    # OVERALL MASTERY
    # ============================================================

    st.subheader(
        "🧠 Overall Knowledge Mastery"
    )

    st.progress(
        min(
            float(accuracy) / 100,
            1.0,
        )
    )

    st.write(
        f"Current overall accuracy: "
        f"**{float(accuracy):.1f}%**"
    )


    # ============================================================
    # SUBJECT-WISE PROGRESS
    # ============================================================

    st.subheader(
        "📚 Subject-wise Progress"
    )


    try:

        subject_progress = (
            get_subject_progress()
        )

    except Exception:

        subject_progress = []


    if subject_progress:

        for item in subject_progress:

            subject = item.get(
                "subject",
                "General",
            )

            subject_accuracy = float(
                item.get(
                    "accuracy",
                    0,
                )
            )


            st.write(
                f"**{subject}** — "
                f"{subject_accuracy:.1f}% accuracy"
            )


            st.progress(
                min(
                    subject_accuracy / 100,
                    1.0,
                )
            )

    else:

        st.info(
            "Complete a quiz to see "
            "subject-wise progress."
        )


    # ============================================================
    # STUDY HISTORY
    # ============================================================

    st.subheader(
        "🕒 Study History"
    )


    try:

        history = get_study_history(
            limit=20
        )

    except Exception:

        history = []


    if history:

        for item in history:

            subject = item.get(
                "subject",
                "General",
            )

            activity_type = item.get(
                "activity_type",
                "Study",
            )

            score = item.get(
                "score",
                None,
            )

            total = item.get(
                "total_questions",
                None,
            )

            created_at = item.get(
                "created_at",
                "",
            )


            if (
                score is not None
                and total is not None
            ):

                st.write(
                    f"📘 **{subject}** | "
                    f"{activity_type} | "
                    f"Score: {score}/{total} | "
                    f"{created_at}"
                )

            else:

                st.write(
                    f"📘 **{subject}** | "
                    f"{activity_type} | "
                    f"{created_at}"
                )

    else:

        st.info(
            "No study history yet. "
            "Complete a quiz or generate flashcards."
        )


    # ============================================================
    # SMART RECOMMENDATION
    # ============================================================

    st.markdown('<div id="smart-study-recommendation"></div>', unsafe_allow_html=True)
    st.subheader(
        "Smart Study Recommendation"
    )


    if quizzes_taken == 0:

        recommendation = (
            "🚀 Start by uploading a document and "
            "generating your first quiz."
        )

    elif accuracy >= 90:

        recommendation = (
            "🏆 Excellent performance! Try Hard "
            "difficulty questions and use YouTube "
            "resources for advanced topics."
        )

    elif accuracy >= 80:

        recommendation = (
            "🌟 Great work! Continue with Hard quizzes "
            "and revise using flashcards."
        )

    elif accuracy >= 60:

        recommendation = (
            "📚 Good progress. Review incorrect answers "
            "and practice Medium difficulty questions."
        )

    else:

        recommendation = (
            "🌱 Focus on the basics. Use Easy quizzes, "
            "flashcards, and educational videos for revision."
        )


    st.info(
        recommendation
    )


    # ============================================================
    # ACHIEVEMENTS
    # ============================================================

    st.markdown('<div id="achievements"></div>', unsafe_allow_html=True)
    st.subheader(
        "Achievements"
    )

    achievements = []


    if quizzes_taken >= 1:

        achievements.append(
            "🎯 First Quiz Completed"
        )


    if quizzes_taken >= 5:

        achievements.append(
            "🔥 Quiz Explorer"
        )


    if quizzes_taken >= 10:

        achievements.append(
            "🏆 Quiz Master"
        )


    if total_flashcards >= 5:

        achievements.append(
            "🧠 Flashcard Starter"
        )


    if total_flashcards >= 20:

        achievements.append(
            "📚 Revision Champion"
        )


    if accuracy >= 80:

        achievements.append(
            "🌟 80% Accuracy"
        )


    if accuracy >= 90:

        achievements.append(
            "💎 90% Accuracy"
        )


    if achievements:

        for achievement in achievements:

            st.success(
                achievement
            )

    else:

        st.info(
            "🔒 Complete quizzes and create "
            "flashcards to unlock achievements!"
        )


    # ============================================================
    # FOOTER
    # ============================================================

    st.divider()

    st.markdown(
        """<div class=\"footer\">🧠 Lumyn-AI • Learn • Practice • Review • Improve • Master</div>""",
        unsafe_allow_html=True,
    )
