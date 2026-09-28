import os
from dotenv import load_dotenv
from hindsight_client import Hindsight
from groq import Groq

load_dotenv()

# -----------------------------
# Hindsight
# -----------------------------
hindsight = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

# -----------------------------
# Groq
# -----------------------------
groq = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# -----------------------------
# Investigate Incident
# -----------------------------
def investigate_incident(incident):

    # 1. Recall similar past incidents
    results = hindsight.recall(
        bank_id="recallops",
        query=incident
    )

    # 2. Keep only the top 5 memories
    recalled_memories = results.results[:5]

    # 3. Convert memories into text
    memories = "\n\n".join(
        memory.text
        for memory in recalled_memories
    )

    # 4. Ask AI to analyze the incident
    prompt = f"""
You are RecallOps, an AI incident response assistant.

Your job is to investigate a new production incident
using historical incident memory.

NEW INCIDENT:
{incident}

HISTORICAL INCIDENT MEMORY:
{memories}

IMPORTANT RULES:

1. Prioritize memories that match:
   - the same service
   - the same error
   - the same failure pattern
   - the same root cause

2. Prefer directly relevant incidents over unrelated incidents.

3. Use historical incidents as evidence.

4. Do not invent configuration values, numbers,
   tools, or facts.

5. Do not recommend actions unsupported
   by the historical memory.

6. If there is not enough evidence, say so.

7. Keep the response concise.

8. Give a maximum of 4 recommended actions.

9. Mention only incident IDs that directly
   support the investigation.

Return exactly these sections:

LIKELY ROOT CAUSE:
One concise explanation.

RECOMMENDED ACTIONS:
1. Action
2. Action
3. Action
4. Action

WHY:
Briefly explain how the historical incidents
support the recommendations.

RELEVANT INCIDENTS:
List the relevant incident IDs.
"""

    response = groq.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return {
        "answer": response.choices[0].message.content,
        "memories": recalled_memories
    }


# -----------------------------
# Learn From Resolved Incident
# -----------------------------
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


# -----------------------------
# Test Agent Directly
# -----------------------------
if __name__ == "__main__":

    new_incident = """
    Payment API is returning HTTP 500 errors.
    Database connections are failing during high traffic.
    The service is currently unavailable.
    """

    try:
        result = investigate_incident(new_incident)

        print("\n========== RECALL OPS ==========\n")
        print(result["answer"])

        print("\n========== RECALLED MEMORY ==========\n")

        for memory in result["memories"]:
            print(memory.text)
            print("-" * 50)

    finally:
        hindsight.close()