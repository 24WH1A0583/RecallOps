import os
import hashlib
import uuid
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from hindsight_client import Hindsight
from groq import Groq


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

HINDSIGHT_BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL"
)

HINDSIGHT_API_KEY = os.getenv(
    "HINDSIGHT_API_KEY"
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

BANK_ID = "recallops"


# =========================================================
# HINDSIGHT CLIENT HELPER
# =========================================================

def _run_hindsight(
    method_name,
    **kwargs
):
    """
    Run Hindsight in a separate thread.

    Streamlit can have an active asyncio event loop.
    Hindsight's synchronous helpers internally use asyncio.

    Running each Hindsight operation in a fresh worker thread
    prevents event-loop conflicts.
    """

    def worker():

        client = Hindsight(
            base_url=HINDSIGHT_BASE_URL,
            api_key=HINDSIGHT_API_KEY
        )

        try:

            method = getattr(
                client,
                method_name
            )

            return method(
                **kwargs
            )

        finally:

            try:

                client.close()

            except Exception:

                pass

    with ThreadPoolExecutor(
        max_workers=1
    ) as executor:

        future = executor.submit(
            worker
        )

        return future.result()


# =========================================================
# GROQ CLIENT
# =========================================================

groq = Groq(
    api_key=GROQ_API_KEY
)


# =========================================================
# INCIDENT KEY
# =========================================================

def incident_key(
    incident
):

    normalized = " ".join(
        incident.strip().lower().split()
    )

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()[:16]


# =========================================================
# SAFE HINDSIGHT RECALL QUERY
# =========================================================

def _safe_recall_query(
    incident,
    max_chars=1600
):
    """
    Hindsight recall has a maximum query size.

    The full incident is still sent to Groq.
    Only the recall query is shortened when necessary.
    """

    text = " ".join(
        incident.strip().split()
    )

    if len(text) <= max_chars:

        return text

    first_part = (
        max_chars * 3
    ) // 4

    last_part = (
        max_chars - first_part
    )

    return (
        text[:first_part]
        + " ... "
        + text[-last_part:]
    )


# =========================================================
# INVESTIGATE INCIDENT
# =========================================================

def investigate_incident(
    incident
):

    # Every click on "Investigate Incident"
    # creates one investigation occurrence.
    investigation_id = uuid.uuid4().hex

    # Only the recall query is shortened.
    recall_query = _safe_recall_query(
        incident
    )

    results = _run_hindsight(
        "recall",
        bank_id=BANK_ID,
        query=recall_query
    )

    recalled_memories = (
        getattr(
            results,
            "results",
            []
        )
        or []
    )[:10]

    if recalled_memories:

        memories = "\n\n".join(
            f"MEMORY {i + 1}:\n{memory.text}"
            for i, memory in enumerate(
                recalled_memories
            )
        )

    else:

        memories = (
            "NO HISTORICAL MEMORY FOUND."
        )


    # =====================================================
    # GROQ PROMPT
    # =====================================================

    prompt = f"""
You are RecallOps, an AI incident response assistant.

Your job is to investigate a new production incident
using historical incident memory.

==================================================
NEW INCIDENT
==================================================

{incident}

==================================================
HISTORICAL MEMORY
==================================================

{memories}

==================================================
INVESTIGATION RULES
==================================================

1. Identify the most relevant historical incidents.

2. Prioritize memories matching:
   - the same service
   - the same error
   - the same failure pattern
   - the same root cause

3. Do NOT treat a memory as relevant simply because
   it mentions a similar word.

4. Prefer exact service + error + failure-pattern matches.

5. Use historical incidents as evidence.

6. Every recommended action MUST be supported by
   the historical evidence provided above.

7. Do NOT invent:
   - configuration values
   - metrics
   - tools
   - infrastructure
   - root causes
   - actions
   - incident IDs

8. Do not recommend an action merely because it
   helped another incident with a similar service.

9. A recommendation must satisfy BOTH conditions:
   - it is supported by a historical incident, AND
   - the current incident contains evidence that makes
     that action applicable.

10. Do not transfer conditions from historical incidents
    into the current incident.

11. Maximum 4 recommended actions.

12. Confidence must reflect the strength of the
    historical evidence:
    - HIGH = strong direct historical match
    - MEDIUM = partially matching historical evidence
    - LOW = weak or insufficient historical evidence

==================================================
OUTPUT FORMAT
==================================================

Return EXACTLY these sections:

LIKELY ROOT CAUSE:
One concise explanation based only on historical evidence.

CONFIDENCE:
HIGH, MEDIUM, or LOW

RECOMMENDED ACTIONS:
1. Action
2. Action
3. Action
4. Action

WHY:
Briefly explain how the historical evidence supports
the root cause and recommended actions.

RELEVANT INCIDENTS:
List only the incident IDs that directly support
the investigation.

==================================================
IMPORTANT
==================================================

If there is not enough evidence, do not guess.

Say:

"Insufficient historical evidence to determine the
root cause confidently."

In that case:
- Confidence should be LOW.
- Do not invent recommendations.
- RELEVANT INCIDENTS should say "None".
"""


    # =====================================================
    # GROQ
    # =====================================================

    response = groq.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = (
        response
        .choices[0]
        .message
        .content
    )


    # =====================================================
    # RETURN
    # =====================================================

    return {
        "answer": answer,
        "memories": recalled_memories,
        "investigation_id": investigation_id
    }


# =========================================================
# RECORD HUMAN DECISION
# =========================================================

def record_human_decision(
    incident,
    recommendation,
    decision,
    investigation_id
):

    key = incident_key(
        incident
    )

    # IMPORTANT:
    # Hindsight metadata values must be strings.
    timestamp = (
        datetime
        .now(timezone.utc)
        .isoformat()
    )


    memory = f"""
RECALLOPS HUMAN DECISION

Incident Key:
{key}

Investigation ID:
{investigation_id}

Incident:
{incident}

AI Recommendation:
{recommendation}

Human Decision:
{decision}

Decision Timestamp:
{timestamp}

This is the current human decision for this
specific investigation occurrence.

If the operator changes the decision, the same
investigation record is updated instead of creating
a duplicate decision.
"""


    # =====================================================
    # IMPORTANT
    # =====================================================
    #
    # document_id makes this investigation occurrence
    # idempotent.
    #
    # If the user clicks:
    #
    # Approve
    # then Override
    #
    # the same document is replaced.
    #
    # Therefore:
    #
    # Approved = 1
    #
    # becomes
    #
    # Overridden = 1
    #
    # instead of:
    #
    # Approved = 1
    # Overridden = 1
    #
    # =====================================================

    _run_hindsight(
        "retain",
        bank_id=BANK_ID,
        content=memory,
        context=(
            "RecallOps human incident decision"
        ),
        document_id=(
            f"decision-{investigation_id}"
        ),
        metadata={
            "record_type": "human_decision",
            "incident_key": str(key),
            "investigation_id": str(
                investigation_id
            ),
            "decision": str(
                decision
            ),
            "decision_timestamp": str(
                timestamp
            )
        },
        update_mode="replace",
        retain_async=False
    )


    return (
        "Human decision recorded in Hindsight."
    )


# =========================================================
# GET MEMORY ITEMS
# =========================================================

def _get_memory_items(
    result
):

    if hasattr(
        result,
        "items"
    ):

        return result.items

    if hasattr(
        result,
        "results"
    ):

        return result.results

    if isinstance(
        result,
        list
    ):

        return result

    return []


# =========================================================
# GET DECISION COUNTS
# =========================================================

def get_decision_counts(
    incident
):

    key = incident_key(
        incident
    )


    counts = {
        "accepted": 0,
        "overridden": 0,
        "escalated": 0
    }


    # =====================================================
    # GET ALL STORED MEMORY ITEMS
    # =====================================================

    result = _run_hindsight(
        "list_memories",
        bank_id=BANK_ID,
        limit=1000,
        offset=0
    )


    # =====================================================
    # ONE FINAL DECISION PER INVESTIGATION
    # =====================================================

    decisions_by_investigation = {}


    for memory in _get_memory_items(
        result
    ):

        metadata = getattr(
            memory,
            "metadata",
            None
        )


        if not isinstance(
            metadata,
            dict
        ):

            continue


        if metadata.get(
            "record_type"
        ) != "human_decision":

            continue


        if metadata.get(
            "incident_key"
        ) != key:

            continue


        investigation_id = (
            metadata.get(
                "investigation_id"
            )
        )

        decision = (
            metadata.get(
                "decision"
            )
        )


        if not investigation_id:

            continue


        if not decision:

            continue


        # Because document_id is based on
        # investigation_id, there should only
        # be one current record.
        #
        # This dictionary also protects against
        # duplicate memory units returned by
        # Hindsight.

        decisions_by_investigation[
            str(
                investigation_id
            )
        ] = str(
            decision
        )


    # =====================================================
    # COUNT FINAL DECISIONS
    # =====================================================

    for decision in (
        decisions_by_investigation.values()
    ):

        if decision == "Approved":

            counts["accepted"] += 1

        elif decision == "Overridden":

            counts["overridden"] += 1

        elif decision == "Escalated":

            counts["escalated"] += 1


    return counts


# =========================================================
# LEARN FROM RESOLVED INCIDENT
# =========================================================

def learn_from_incident(
    incident,
    root_cause,
    resolution,
    outcome
):

    memory = f"""
NEW INCIDENT RESOLUTION

Incident:
{incident}

Root Cause:
{root_cause}

Resolution:
{resolution}

Outcome:
{outcome}

Lesson:
This incident and its resolution should be remembered
for future incident investigations.
"""


    _run_hindsight(
        "retain",
        bank_id=BANK_ID,
        content=memory,
        context=(
            "RecallOps resolved incident"
        ),
        retain_async=False
    )


    return (
        "Incident resolution stored in Hindsight."
    )


# =========================================================
# DIRECT TEST
# =========================================================

if __name__ == "__main__":

    new_incident = """
    Payment API is returning HTTP 500 errors.
    Database connections are failing during high traffic.
    The service is currently unavailable.
    """


    result = investigate_incident(
        new_incident
    )


    print(
        "\n========== RECALL OPS ==========\n"
    )

    print(
        result["answer"]
    )


    print(
        "\n========== RECALLED MEMORY ==========\n"
    )


    for memory in (
        result["memories"][:5]
    ):

        print(
            memory.text
        )

        print(
            "-" * 50
        )