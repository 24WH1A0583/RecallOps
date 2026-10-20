import textwrap
import streamlit as st

from agent import (
    investigate_incident,
    learn_from_incident,
    record_human_decision,
    get_decision_counts
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="RecallOps",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# SESSION STATE
# =========================================================

DEFAULTS = {
    "dark_mode": True,
    "decision": None,
    "answer": None,
    "memories": [],
    "incident": "",
    "service": "",
    "error": "",
    "severity": "",
    "investigation_id": None,
    "decision_counts": {
        "accepted": 0,
        "overridden": 0,
        "escalated": 0
    },
    "action_message": None,
    "action_type": None
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# THEME
# =========================================================

dark_mode = st.toggle(
    "Dark mode",
    value=st.session_state["dark_mode"],
    key="dark_mode_toggle"
)

st.session_state["dark_mode"] = dark_mode


if dark_mode:
    BG = "#080c14"
    SURFACE = "#101722"
    SURFACE_2 = "#151e2b"
    BORDER = "#273244"
    TEXT = "#f5f7fb"
    MUTED = "#9aa6b5"
    PRIMARY = "#ff4d4d"
    PRIMARY_HOVER = "#ff6666"
    BLUE = "#38bdf8"
    GREEN = "#22c55e"
    YELLOW = "#facc15"
    RED = "#ef4444"
    SHADOW = "rgba(0,0,0,0.28)"
else:
    BG = "#f4f7fb"
    SURFACE = "#ffffff"
    SURFACE_2 = "#f8fafc"
    BORDER = "#dce3ec"
    TEXT = "#111827"
    MUTED = "#667085"
    PRIMARY = "#e53935"
    PRIMARY_HOVER = "#c62828"
    BLUE = "#0284c7"
    GREEN = "#16a34a"
    YELLOW = "#ca8a04"
    RED = "#dc2626"
    SHADOW = "rgba(15,23,42,0.08)"


# =========================================================
# GLOBAL CSS
# =========================================================

st.markdown(
    textwrap.dedent(f"""
    <style>

    html, body, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont,
                     "Segoe UI", sans-serif;
    }}

    [data-testid="stAppViewContainer"] {{
        background: {BG};
    }}

    [data-testid="stHeader"],
    [data-testid="stToolbar"] {{
        background: transparent;
    }}

    .main .block-container {{
        max-width: 1400px;
        padding-top: 1.5rem;
        padding-bottom: 4rem;
    }}

    h1, h2, h3, h4, h5, h6,
    p, label,
    [data-testid="stMarkdownContainer"] {{
        color: {TEXT};
    }}

    [data-testid="stCaptionContainer"] {{
        color: {MUTED} !important;
    }}

    /* TOP NAV */

    .top-nav {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 18px 22px;
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 18px;
        margin-bottom: 24px;
        box-shadow: 0 8px 28px {SHADOW};
    }}

    .brand-wrapper {{
        display: flex;
        align-items: center;
        gap: 14px;
    }}

    .brand-logo {{
        width: 48px;
        height: 48px;
        border-radius: 14px;
        background: {PRIMARY};
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 8px 22px rgba(255,77,77,0.20);
    }}

    .brand-name {{
        font-size: 25px;
        font-weight: 800;
        color: {TEXT};
        line-height: 1.1;
    }}

    .brand-tagline {{
        font-size: 12px;
        color: {MUTED};
        margin-top: 4px;
    }}

    .connection-pill {{
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 9px 13px;
        border-radius: 999px;
        border: 1px solid {BORDER};
        background: {SURFACE_2};
        color: {MUTED};
        font-size: 12px;
        font-weight: 650;
    }}

    .connection-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: {GREEN};
        box-shadow: 0 0 8px rgba(34,197,94,0.5);
    }}

    /* HERO */

    .hero {{
        padding: 34px;
        border-radius: 22px;
        background: linear-gradient(135deg, {SURFACE}, {SURFACE_2});
        border: 1px solid {BORDER};
        margin-bottom: 26px;
        box-shadow: 0 12px 35px {SHADOW};
    }}

    .hero-kicker {{
        color: {PRIMARY};
        font-size: 12px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 10px;
    }}

    .hero-title {{
        font-size: 36px;
        font-weight: 850;
        color: {TEXT};
        margin-bottom: 10px;
    }}

    .hero-text {{
        max-width: 850px;
        color: {MUTED};
        font-size: 15px;
        line-height: 1.65;
    }}

    /* SECTION HEADERS */

    .section {{
        margin-top: 34px;
        margin-bottom: 14px;
    }}

    .section-title {{
        font-size: 22px;
        font-weight: 800;
        color: {TEXT};
    }}

    .section-description {{
        color: {MUTED};
        font-size: 13px;
        margin-top: 5px;
        line-height: 1.5;
    }}

    /* INCIDENT CARD */

    .incident-card {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 8px 28px {SHADOW};
    }}

    /* METRIC CARDS */

    .metric-card {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 20px;
        min-height: 120px;
        box-shadow: 0 6px 20px {SHADOW};
    }}

    .metric-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .metric-label {{
        font-size: 11px;
        color: {MUTED};
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    .metric-icon {{
        font-size: 19px;
    }}

    .metric-value {{
        font-size: 24px;
        font-weight: 850;
        color: {TEXT};
        margin-top: 13px;
        overflow-wrap: anywhere;
    }}

    /* AI CARDS */

    .ai-card {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 23px;
        margin: 12px 0;
        box-shadow: 0 6px 22px {SHADOW};
    }}

    .ai-title {{
        font-size: 16px;
        font-weight: 800;
        color: {TEXT};
        margin-bottom: 12px;
    }}

    .ai-content {{
        color: {TEXT};
        font-size: 14px;
        line-height: 1.7;
        overflow-wrap: anywhere;
    }}

    /* CONFIDENCE */

    .confidence-high {{
        border-left: 4px solid {GREEN};
    }}

    .confidence-medium {{
        border-left: 4px solid {YELLOW};
    }}

    .confidence-low {{
        border-left: 4px solid {RED};
    }}

    .confidence-title {{
        font-size: 18px;
        font-weight: 800;
        color: {TEXT};
    }}

    .confidence-subtitle {{
        color: {MUTED};
        font-size: 13px;
        margin-top: 5px;
    }}

    /* HUMAN CONTROL */

    .human-panel {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 20px;
        padding: 24px;
        margin-top: 12px;
        box-shadow: 0 8px 28px {SHADOW};
    }}

    .decision-status {{
        padding: 13px 16px;
        border-radius: 12px;
        background: {SURFACE_2};
        border: 1px solid {BORDER};
        color: {TEXT};
        font-size: 14px;
        margin-bottom: 18px;
    }}

    /* DECISION COUNTERS */

    .history-card {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 25px 18px;
        text-align: center;
        min-height: 145px;
        box-shadow: 0 7px 24px {SHADOW};
    }}

    .history-number {{
        font-size: 42px;
        font-weight: 900;
        line-height: 1;
        margin-bottom: 12px;
    }}

    .history-number.green {{
        color: {GREEN};
    }}

    .history-number.red {{
        color: {RED};
    }}

    .history-number.yellow {{
        color: {YELLOW};
    }}

    .history-label {{
        font-size: 12px;
        font-weight: 850;
        letter-spacing: 0.08em;
        color: {TEXT};
    }}

    .history-description {{
        color: {MUTED};
        font-size: 12px;
        margin-top: 8px;
    }}

    /* MEMORY */

    [data-testid="stExpander"] {{
        background: {SURFACE} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 14px;
        margin-bottom: 9px;
    }}

    [data-testid="stExpander"] summary {{
        color: {TEXT} !important;
    }}

    /* INPUTS */

    .stTextArea textarea,
    .stTextInput input {{
        background: {SURFACE_2} !important;
        color: {TEXT} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 12px !important;
    }}

    .stTextArea textarea:focus,
    .stTextInput input:focus {{
        border-color: {PRIMARY} !important;
        box-shadow: 0 0 0 1px {PRIMARY} !important;
    }}

    .stTextArea textarea::placeholder,
    .stTextInput input::placeholder {{
        color: {MUTED} !important;
    }}

    /* BUTTONS */

    .stButton > button {{
        border-radius: 11px !important;
        min-height: 44px !important;
        border: 1px solid {BORDER} !important;
        background: {SURFACE} !important;
        color: {TEXT} !important;
        font-weight: 700 !important;
    }}

    .stButton > button:hover {{
        border-color: {PRIMARY} !important;
        color: {PRIMARY} !important;
    }}

    .stButton > button[kind="primary"] {{
        background: {PRIMARY} !important;
        border-color: {PRIMARY} !important;
        color: white !important;
    }}

    .stButton > button[kind="primary"]:hover {{
        background: {PRIMARY_HOVER} !important;
        border-color: {PRIMARY_HOVER} !important;
        color: white !important;
    }}

    /* TOGGLE */

    [data-testid="stToggle"] label {{
        color: {TEXT} !important;
        font-weight: 650 !important;
    }}

    /* ALERTS */

    [data-testid="stAlert"] {{
        border-radius: 13px !important;
    }}

    /* FOOTER */

    .footer {{
        margin-top: 55px;
        padding-top: 20px;
        border-top: 1px solid {BORDER};
        text-align: center;
        color: {MUTED};
        font-size: 11px;
    }}

    /* MOBILE */

    @media (max-width: 800px) {{
        .hero {{
            padding: 24px;
        }}

        .hero-title {{
            font-size: 28px;
        }}

        .brand-name {{
            font-size: 22px;
        }}

        .connection-pill {{
            display: none;
        }}
    }}

    </style>
    """),
    unsafe_allow_html=True
)
# =========================================================
# TOP NAV
# =========================================================

st.markdown(
    """
    <style>
    .top-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 18px 22px;
        border-radius: 18px;
        margin-bottom: 24px;
    }
    .brand-wrapper {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .brand-logo {
        width: 48px;
        height: 48px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    }
    .connection-pill {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 9px 13px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 650;
    }
    .connection-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #22c55e;
    }
    </style>

    <div class="top-nav">
        <div class="brand-wrapper">
            <div class="brand-logo">🚨</div>
            <div>
                <div class="brand-name">RecallOps</div>
                <div class="brand-tagline">
                    AI Incident Response &amp; Hindsight Intelligence
                </div>
            </div>
        </div>
        <div class="connection-pill">
            <span class="connection-dot"></span>
            Hindsight Memory Connected
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# NEW INCIDENT
# =========================================================

st.markdown(
    textwrap.dedent("""
    <div class="section">
        <div class="section-title">
            🚨 New Production Incident
        </div>
        <div class="section-description">
            Describe what is happening and RecallOps will search
            historical memory for relevant evidence.
        </div>
    </div>
    """),
    unsafe_allow_html=True
)


incident = st.text_area(
    "Describe what is happening",
    placeholder=(
        "Example:\n"
        "Payment API is returning HTTP 500 errors.\n"
        "Database connections are failing during high traffic.\n"
        "The service is currently unavailable."
    ),
    height=145,
    label_visibility="visible"
)


if st.button(
    "🔍  Investigate Incident",
    type="primary",
    use_container_width=True,
    key="investigate_incident_button"
):
    if not incident.strip():
        st.warning("Please describe an incident first.")

    else:
        service = "Unknown Service"
        error = "Unknown Error"
        severity = "LOW"
        text = incident.lower()

        # SERVICE
        if "payment" in text:
            service = "Payment API"
        elif "user" in text:
            service = "User Service"
        elif "order" in text:
            service = "Order Service"
        elif "notification" in text:
            service = "Notification Service"
        elif "product" in text:
            service = "Product Service"
        elif "search" in text:
            service = "Search Service"
        elif "authentication" in text:
            service = "Authentication Service"

        # ERROR
        if "500" in text:
            error = "HTTP 500"
        elif "503" in text:
            error = "HTTP 503"
        elif "502" in text:
            error = "HTTP 502"
        elif "401" in text:
            error = "HTTP 401"
        elif "timeout" in text:
            error = "Request Timeout"
        elif "unavailable" in text:
            error = "Service Unavailable"

        # SEVERITY
        if (
            "unavailable" in text
            or "down" in text
            or "payment" in text
        ):
            severity = "CRITICAL"
        elif (
            "500" in text
            or "503" in text
            or "502" in text
        ):
            severity = "HIGH"
        elif "timeout" in text:
            severity = "MEDIUM"

        st.session_state["service"] = service
        st.session_state["error"] = error
        st.session_state["severity"] = severity

        try:
            with st.spinner(
                "🧠 Recalling historical memory and investigating..."
            ):
                result = investigate_incident(incident)

            st.session_state["answer"] = result["answer"]
            st.session_state["memories"] = result.get("memories", [])
            st.session_state["incident"] = incident
            st.session_state["investigation_id"] = result.get(
                "investigation_id"
            )

            # A new investigation starts without a decision.
            st.session_state["decision"] = None

            st.session_state["decision_counts"] = get_decision_counts(
                incident
            )

            st.session_state["action_message"] = None
            st.session_state["action_type"] = None

            st.rerun()

        except Exception as e:
            st.error(f"Investigation failed: {e}")


# =========================================================
# RESULTS
# =========================================================

if st.session_state.get("answer"):

    answer = st.session_state["answer"]

    # INCIDENT OVERVIEW
    st.markdown(
        textwrap.dedent("""
        <div class="section">
            <div class="section-title">📋 Incident Overview</div>
            <div class="section-description">
                Automatically detected characteristics of this incident.
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            textwrap.dedent(f"""
            <div class="metric-card">
                <div class="metric-top">
                    <div class="metric-label">Severity</div>
                    <div class="metric-icon">⚠️</div>
                </div>
                <div class="metric-value">
                    {st.session_state["severity"]}
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            textwrap.dedent(f"""
            <div class="metric-card">
                <div class="metric-top">
                    <div class="metric-label">Service</div>
                    <div class="metric-icon">⚙️</div>
                </div>
                <div class="metric-value">
                    {st.session_state["service"]}
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            textwrap.dedent(f"""
            <div class="metric-card">
                <div class="metric-top">
                    <div class="metric-label">Error</div>
                    <div class="metric-icon">🔴</div>
                </div>
                <div class="metric-value">
                    {st.session_state["error"]}
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )


    # AI INVESTIGATION
    st.markdown(
        textwrap.dedent("""
        <div class="section">
            <div class="section-title">🤖 AI Investigation</div>
            <div class="section-description">
                RecallOps combines the current incident with historical
                evidence before producing its recommendation.
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )


    # ROOT CAUSE
    if "LIKELY ROOT CAUSE:" in answer:
        root_cause = answer.split(
            "LIKELY ROOT CAUSE:", 1
        )[1]

        if "RECOMMENDED ACTIONS:" in root_cause:
            root_cause = root_cause.split(
                "RECOMMENDED ACTIONS:", 1
            )[0]

        st.markdown(
            textwrap.dedent(f"""
            <div class="ai-card">
                <div class="ai-title">🔴 Likely Root Cause</div>
                <div class="ai-content">
                    {root_cause.strip()}
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )


    # CONFIDENCE
    confidence = "LOW"

    if "CONFIDENCE:" in answer:
        confidence_section = answer.split("CONFIDENCE:", 1)[1]

        for marker in (
            "RECOMMENDED ACTIONS:",
            "WHY:",
            "RELEVANT INCIDENTS:"
        ):
            if marker in confidence_section:
                confidence_section = confidence_section.split(
                    marker, 1
                )[0]

        confidence = confidence_section.strip().upper()

    if "HIGH" in confidence:
        st.markdown(
            textwrap.dedent("""
            <div class="ai-card confidence-high">
                <div class="confidence-title">🎯 High Confidence</div>
                <div class="confidence-subtitle">
                    Strong direct historical evidence supports this
                    investigation.
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )
    elif "MEDIUM" in confidence:
        st.markdown(
            textwrap.dedent("""
            <div class="ai-card confidence-medium">
                <div class="confidence-title">🎯 Medium Confidence</div>
                <div class="confidence-subtitle">
                    Historical evidence partially matches the current
                    incident.
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            textwrap.dedent("""
            <div class="ai-card confidence-low">
                <div class="confidence-title">🎯 Low Confidence</div>
                <div class="confidence-subtitle">
                    Historical evidence is insufficient to confidently
                    determine the cause.
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )


    # RECOMMENDED ACTIONS
    recommendation_text = ""

    if "RECOMMENDED ACTIONS:" in answer:
        actions_section = answer.split(
            "RECOMMENDED ACTIONS:", 1
        )[1]

        for marker in ("WHY:", "RELEVANT INCIDENTS:"):
            if marker in actions_section:
                actions_section = actions_section.split(marker, 1)[0]

        recommendation_text = actions_section.strip()

    st.markdown("### 🛠️ Recommended Actions")

    with st.container(border=True):
        if recommendation_text:
            st.markdown(recommendation_text)
        else:
            st.info(
                "No recommendation was made because there is not enough "
                "historical evidence."
            )


    # WHY
    if "WHY:" in answer:
        why_section = answer.split("WHY:", 1)[1]

        if "RELEVANT INCIDENTS:" in why_section:
            why_section = why_section.split(
                "RELEVANT INCIDENTS:", 1
            )[0]

        st.markdown(
            textwrap.dedent(f"""
            <div class="ai-card">
                <div class="ai-title">
                    💡 Why RecallOps Recommends This
                </div>
                <div class="ai-content">
                    {why_section.strip()}
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )


    # RELEVANT INCIDENTS
    if "RELEVANT INCIDENTS:" in answer:
        incidents_section = answer.split(
            "RELEVANT INCIDENTS:", 1
        )[1]

        st.markdown(
            textwrap.dedent(f"""
            <div class="ai-card">
                <div class="ai-title">
                    📌 Relevant Historical Incidents
                </div>
                <div class="ai-content">
                    {incidents_section.strip()}
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )
            # =====================================================
    # HUMAN CONTROL
    # =====================================================

    st.markdown(
        textwrap.dedent("""
        <div class="section">
            <div class="section-title">👤 Human Control</div>
            <div class="section-description">
                The AI recommends. The human decides.
                You can change the decision at any time.
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )

    with st.container(border=True):

        current_decision = st.session_state.get("decision")

        if current_decision:
            st.markdown(
                textwrap.dedent(f"""
                <div class="decision-status">
                    <strong>Current human decision:</strong>
                    {current_decision}
                </div>
                """),
                unsafe_allow_html=True
            )

        control1, control2, control3, control4 = st.columns(4)

        # APPROVE
        with control1:
            if st.button(
                "✓  Approve",
                use_container_width=True,
                key="approve_decision_button"
            ):
                try:
                    with st.spinner("Recording decision..."):
                        record_human_decision(
                            st.session_state["incident"],
                            recommendation_text,
                            "Approved",
                            st.session_state["investigation_id"]
                        )

                    st.session_state["decision"] = "Approved"
                    st.session_state["decision_counts"] = (
                        get_decision_counts(
                            st.session_state["incident"]
                        )
                    )
                    st.session_state["action_message"] = (
                        "AI recommendation approved."
                    )
                    st.session_state["action_type"] = "success"
                    st.rerun()

                except Exception as e:
                    st.error(f"Could not record decision: {e}")

        # OVERRIDE
        with control2:
            if st.button(
                "✕  Override",
                use_container_width=True,
                key="override_decision_button"
            ):
                try:
                    with st.spinner("Recording decision..."):
                        record_human_decision(
                            st.session_state["incident"],
                            recommendation_text,
                            "Overridden",
                            st.session_state["investigation_id"]
                        )

                    st.session_state["decision"] = "Overridden"
                    st.session_state["decision_counts"] = (
                        get_decision_counts(
                            st.session_state["incident"]
                        )
                    )
                    st.session_state["action_message"] = (
                        "AI recommendation overridden."
                    )
                    st.session_state["action_type"] = "warning"
                    st.rerun()

                except Exception as e:
                    st.error(f"Could not record decision: {e}")

        # ASK WHY
        with control3:
            if st.button(
                "?  Ask Why",
                use_container_width=True,
                key="ask_why_button"
            ):
                st.info(
                    "RecallOps based this recommendation on the "
                    "historical incidents shown below. Only directly "
                    "relevant historical evidence was used to support "
                    "the recommendation."
                )

        # ESCALATE
        with control4:
            if st.button(
                "↑  Escalate",
                use_container_width=True,
                key="escalate_decision_button"
            ):
                try:
                    with st.spinner("Recording decision..."):
                        record_human_decision(
                            st.session_state["incident"],
                            recommendation_text,
                            "Escalated",
                            st.session_state["investigation_id"]
                        )

                    st.session_state["decision"] = "Escalated"
                    st.session_state["decision_counts"] = (
                        get_decision_counts(
                            st.session_state["incident"]
                        )
                    )
                    st.session_state["action_message"] = (
                        "Incident escalated for human review."
                    )
                    st.session_state["action_type"] = "warning"
                    st.rerun()

                except Exception as e:
                    st.error(f"Could not record decision: {e}")


    # =====================================================
    # ACTION MESSAGE
    # =====================================================

    if st.session_state.get("action_message"):

        action_type = st.session_state.get("action_type")
        action_message = st.session_state["action_message"]

        if action_type == "success":
            st.success(action_message)
        elif action_type == "warning":
            st.warning(action_message)
        else:
            st.info(action_message)


    # =====================================================
    # HUMAN DECISION HISTORY
    # =====================================================

    st.markdown(
        textwrap.dedent("""
        <div class="section">
            <div class="section-title">
                📊 Human Decision History
            </div>
            <div class="section-description">
                Historical decisions for this incident.
                Each investigation occurrence contributes
                only its latest human decision.
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )

    try:
        st.session_state["decision_counts"] = get_decision_counts(
            st.session_state["incident"]
        )
    except Exception:
        pass

    counts = st.session_state.get(
        "decision_counts",
        {
            "accepted": 0,
            "overridden": 0,
            "escalated": 0
        }
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            textwrap.dedent(f"""
            <div class="history-card">
                <div class="history-number green">
                    {counts.get("accepted", 0)}
                </div>
                <div class="history-label">ACCEPTED</div>
                <div class="history-description">
                    AI recommendation accepted
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            textwrap.dedent(f"""
            <div class="history-card">
                <div class="history-number red">
                    {counts.get("overridden", 0)}
                </div>
                <div class="history-label">OVERRIDDEN</div>
                <div class="history-description">
                    AI recommendation rejected
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            textwrap.dedent(f"""
            <div class="history-card">
                <div class="history-number yellow">
                    {counts.get("escalated", 0)}
                </div>
                <div class="history-label">ESCALATED</div>
                <div class="history-description">
                    Sent for human review
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )


    # =====================================================
    # HINDSIGHT MEMORY
    # =====================================================

    st.markdown(
        textwrap.dedent("""
        <div class="section">
            <div class="section-title">🧠 Hindsight Memory</div>
            <div class="section-description">
                Historical memories retrieved before RecallOps
                generated its investigation.
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )

    memories = st.session_state.get("memories", [])

    if memories:
        for i, memory in enumerate(memories, start=1):
            with st.expander(f"📌  Past Incident Memory {i}"):

                if isinstance(memory, dict):
                    st.write(
                        memory.get("text", str(memory))
                    )
                else:
                    st.write(
                        getattr(memory, "text", str(memory))
                    )
    else:
        st.info("No historical incident memories were found.")


    # =====================================================
    # TEACH RECALLOPS
    # =====================================================

    st.markdown(
        textwrap.dedent("""
        <div class="section">
            <div class="section-title">📚 Teach RecallOps</div>
            <div class="section-description">
                Once the incident is resolved, save what happened
                so RecallOps can use the lesson in future investigations.
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )

    root_cause_input = st.text_input(
        "Root Cause",
        placeholder=(
            "Example: Database connection pool exhausted "
            "during high traffic."
        ),
        key="root_cause_input"
    )

    resolution_input = st.text_area(
        "Resolution",
        placeholder=(
            "Example: Increased the database connection pool "
            "size and restarted the Payment API."
        ),
        key="resolution_input"
    )

    outcome_input = st.text_input(
        "Outcome",
        placeholder="Example: Payment API recovered successfully.",
        key="outcome_input"
    )

    if st.button(
        "🧠  Remember This Resolution",
        use_container_width=True,
        key="remember_resolution_button"
    ):
        if not root_cause_input.strip():
            st.warning("Please enter the root cause.")

        elif not resolution_input.strip():
            st.warning("Please enter the resolution.")

        elif not outcome_input.strip():
            st.warning("Please enter the outcome.")

        else:
            try:
                with st.spinner("🧠 Teaching RecallOps..."):
                    message = learn_from_incident(
                        st.session_state["incident"],
                        root_cause_input,
                        resolution_input,
                        outcome_input
                    )

                st.success(message)
                st.info(
                    "RecallOps has learned from this incident. "
                    "Try a similar incident again to see the memory in action."
                )

            except Exception as e:
                st.error(f"Could not save the resolution: {e}")


# =========================================================
# LEARNING LOOP
# =========================================================

st.markdown(
    textwrap.dedent("""
    <div class="section">
        <div class="section-title">🔄 How RecallOps Learns</div>
        <div class="section-description">
            Every incident contributes to a continuous
            investigation and learning loop.
        </div>
    </div>
    """),
    unsafe_allow_html=True
)

col1, col2, col3, col4, col5 = st.columns(5)

loop_items = [
    ("🚨", "New Incident"),
    ("🧠", "Recall Memory"),
    ("🤖", "Investigate"),
    ("📚", "Remember"),
    ("🔄", "Improve")
]

for column, (icon, title) in zip(
    [col1, col2, col3, col4, col5],
    loop_items
):
    with column:
        st.markdown(
            textwrap.dedent(f"""
            <div class="history-card">
                <div style="
                    font-size:26px;
                    margin-bottom:9px;
                ">
                    {icon}
                </div>
                <div style="
                    color:{TEXT};
                    font-size:13px;
                    font-weight:750;
                ">
                    {title}
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    textwrap.dedent("""
    <div class="footer">
        RecallOps • AI Incident Response with Hindsight Memory
    </div>
    """),
    unsafe_allow_html=True
)