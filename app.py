import streamlit as st
from agent import investigate_incident, learn_from_incident


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="RecallOps",
    page_icon="🚨",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 18px;
        color: #777777;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 24px;
        font-weight: 600;
        margin-top: 20px;
    }

    .memory-box {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dddddd;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def detect_service(incident):

    text = incident.lower()

    if "payment" in text:
        return "Payment API"

    if "user" in text:
        return "User Service"

    if "order" in text:
        return "Order Service"

    if "notification" in text:
        return "Notification Service"

    if "product" in text:
        return "Product Service"

    if "search" in text:
        return "Search Service"

    return "Unknown Service"


def detect_error(incident):

    text = incident.lower()

    if "500" in text:
        return "HTTP 500"

    if "503" in text:
        return "HTTP 503"

    if "502" in text:
        return "HTTP 502"

    if "401" in text:
        return "HTTP 401"

    if "timeout" in text:
        return "Request Timeout"

    if "unavailable" in text:
        return "Service Unavailable"

    return "Unknown Error"


def detect_severity(incident):

    text = incident.lower()

    if (
        "unavailable" in text
        or "down" in text
        or "payment" in text
    ):
        return "CRITICAL"

    if (
        "500" in text
        or "503" in text
        or "502" in text
    ):
        return "HIGH"

    if "timeout" in text:
        return "MEDIUM"

    return "LOW"


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🚨 RecallOps</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI Incident Response Agent • Remember. Investigate. Learn.'
    '</div>',
    unsafe_allow_html=True
)

st.info(
    "RecallOps uses Hindsight memory to recall previous incidents, "
    "help investigate the current incident, and remember new resolutions."
)


# =========================================================
# NEW INCIDENT
# =========================================================

st.markdown(
    '<div class="section-title">🚨 New Production Incident</div>',
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
    height=160
)


# =========================================================
# INVESTIGATE
# =========================================================

if st.button(
    "🔍 Investigate Incident",
    type="primary",
    use_container_width=True
):

    if not incident.strip():

        st.warning(
            "Please describe an incident first."
        )

    else:

        # Detect incident information
        service = detect_service(incident)
        error = detect_error(incident)
        severity = detect_severity(incident)

        st.session_state["service"] = service
        st.session_state["error"] = error
        st.session_state["severity"] = severity

        with st.spinner(
            "🧠 Recalling memory and investigating..."
        ):

            result = investigate_incident(
                incident
            )

        st.session_state["answer"] = result["answer"]
        st.session_state["memories"] = result["memories"]
        st.session_state["incident"] = incident


# =========================================================
# INCIDENT OVERVIEW
# =========================================================

if "answer" in st.session_state:

    st.divider()

    st.markdown(
        '<div class="section-title">📋 Incident Overview</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Severity",
            st.session_state["severity"]
        )

    with col2:

        st.metric(
            "Service",
            st.session_state["service"]
        )

    with col3:

        st.metric(
            "Error",
            st.session_state["error"]
        )


# =========================================================
# AI INVESTIGATION
# =========================================================

if "answer" in st.session_state:

    st.divider()

    st.markdown(
        '<div class="section-title">🤖 AI Investigation</div>',
        unsafe_allow_html=True
    )

    answer = st.session_state["answer"]


    # -----------------------------------------------------
    # Root Cause
    # -----------------------------------------------------

    if "LIKELY ROOT CAUSE:" in answer:

        root_cause = answer.split(
            "RECOMMENDED ACTIONS:"
        )[0].replace(
            "LIKELY ROOT CAUSE:",
            ""
        ).strip()

        st.markdown("### 🔴 Likely Root Cause")

        st.info(root_cause)


    # -----------------------------------------------------
    # Recommended Actions
    # -----------------------------------------------------

    if "RECOMMENDED ACTIONS:" in answer:

        actions_section = answer.split(
            "RECOMMENDED ACTIONS:"
        )[1]

        if "WHY:" in actions_section:

            actions_section = actions_section.split(
                "WHY:"
            )[0]

        st.markdown(
            "### 🛠️ Recommended Actions"
        )

        st.markdown(
            actions_section.strip()
        )


    # -----------------------------------------------------
    # Why
    # -----------------------------------------------------

    if "WHY:" in answer:

        why_section = answer.split(
            "WHY:"
        )[1]

        if "RELEVANT INCIDENTS:" in why_section:

            why_section = why_section.split(
                "RELEVANT INCIDENTS:"
            )[0]

        st.markdown("### 💡 Why")

        st.write(
            why_section.strip()
        )


    # -----------------------------------------------------
    # Relevant Incidents
    # -----------------------------------------------------

    if "RELEVANT INCIDENTS:" in answer:

        incidents_section = answer.split(
            "RELEVANT INCIDENTS:"
        )[1]

        st.markdown(
            "### 📌 Relevant Incidents"
        )

        st.write(
            incidents_section.strip()
        )


# =========================================================
# HINDSIGHT MEMORY
# =========================================================

if "memories" in st.session_state:

    st.divider()

    st.markdown(
        '<div class="section-title">🧠 Hindsight Memory</div>',
        unsafe_allow_html=True
    )

    st.write(
        "RecallOps retrieved these historical memories "
        "before generating its investigation."
    )

    memories = st.session_state["memories"]

    if memories:

        for i, memory in enumerate(
            memories,
            start=1
        ):

            with st.expander(
                f"📌 Past Incident Memory {i}"
            ):

                st.write(
                    memory.text
                )

    else:

        st.info(
            "No historical incident memories were found."
        )


# =========================================================
# TEACH RECALLOPS
# =========================================================

if "answer" in st.session_state:

    st.divider()

    st.markdown(
        '<div class="section-title">📚 Teach RecallOps</div>',
        unsafe_allow_html=True
    )

    st.write(
        "After resolving the incident, save the resolution "
        "so RecallOps can remember it for future incidents."
    )

    root_cause = st.text_input(
        "Root Cause",
        placeholder=(
            "Example: Database connection pool exhausted "
            "during high traffic."
        )
    )

    resolution = st.text_area(
        "Resolution",
        placeholder=(
            "Example: Increased the database connection pool "
            "size and restarted the Payment API."
        )
    )

    outcome = st.text_input(
        "Outcome",
        placeholder=(
            "Example: Payment API recovered successfully."
        )
    )

    if st.button(
        "🧠 Remember This Resolution",
        use_container_width=True
    ):

        if not root_cause.strip():

            st.warning(
                "Please enter the root cause."
            )

        elif not resolution.strip():

            st.warning(
                "Please enter the resolution."
            )

        elif not outcome.strip():

            st.warning(
                "Please enter the outcome."
            )

        else:

            with st.spinner(
                "🧠 Teaching RecallOps..."
            ):

                message = learn_from_incident(
                    st.session_state["incident"],
                    root_cause,
                    resolution,
                    outcome
                )

            st.success(
                message
            )

            st.info(
                "RecallOps has learned from this incident. "
                "Try a similar incident again to see the memory in action."
            )


# =========================================================
# LEARNING LOOP
# =========================================================

st.divider()

st.markdown(
    '<div class="section-title">🔄 How RecallOps Learns</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("### 🚨")
    st.write("New Incident")

with col2:
    st.markdown("### 🧠")
    st.write("Recall Memory")

with col3:
    st.markdown("### 🤖")
    st.write("Investigate")

with col4:
    st.markdown("### 📚")
    st.write("Remember")

with col5:
    st.markdown("### 🔄")
    st.write("Improve")