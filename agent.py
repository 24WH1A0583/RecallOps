import os
from dotenv import load_dotenv
from hindsight_client import Hindsight
from groq import Groq

load_dotenv()

# =========================================================
# CLIENTS
# =========================================================

hindsight = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

groq = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# =========================================================
# INVESTIGATE INCIDENT
# =========================================================

def investigate_incident(incident):

    # -----------------------------------------------------
    # 1. Recall historical memories
    # -----------------------------------------------------

    results = hindsight.recall(
        bank_id="recallops",
        query=incident
    )

    # Keep a reasonable number of candidates.
    # We will let the LLM determine which ones actually
    # support the investigation.
    recalled_memories = results.results[:10]

    # -----------------------------------------------------
    # 2. Convert memories into evidence
    # -----------------------------------------------------

    if recalled_memories:

        memories = "\n\n".join(
            f"MEMORY {i + 1}:\n{memory.text}"
            for i, memory in enumerate(recalled_memories)
        )

    else:

        memories = "NO HISTORICAL MEMORY FOUND."

    # -----------------------------------------------------
    # 3. Ask AI to investigate using ONLY evidence
    # -----------------------------------------------------

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

    Example:
    If INC-009 had high database CPU, but the current
    incident does not mention high database CPU, do NOT
    recommend scaling database resources because of INC-009.

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

    # -----------------------------------------------------
    # 4. Generate investigation
    # -----------------------------------------------------

    response = groq.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "memories": recalled_memories
    }


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

    hindsight.retain(
        bank_id="recallops",
        content=memory
    )

    return "Incident resolution stored in Hindsight."


# =========================================================
# TEST AGENT DIRECTLY
# =========================================================

if __name__ == "__main__":

    new_incident = """
    Payment API is returning HTTP 500 errors.
    Database connections are failing during high traffic.
    The service is currently unavailable.
    """

    result = investigate_incident(new_incident)

    print("\n========== RECALL OPS ==========\n")
    print(result["answer"])

    print("\n========== RECALLED MEMORY ==========\n")

    for memory in result["memories"][:5]:
        print(memory.text)
        print("-" * 50)
    hindsight.close()    