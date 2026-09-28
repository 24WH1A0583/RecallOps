import json
import os

from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

client = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

# Load historical incidents
with open("data/incidents.json", "r") as f:
    incidents = json.load(f)

print(f"Loading {len(incidents)} incidents into Hindsight...")

for incident in incidents:
    memory = f"""
Incident ID: {incident["incident_id"]}

Service: {incident["service"]}

Error: {incident["error"]}

Logs: {incident["logs"]}

Severity: {incident["severity"]}

Root Cause: {incident["root_cause"]}

Resolution: {incident["resolution"]}

Actions Taken:
{", ".join(incident["actions_taken"])}

Outcome: {incident["outcome"]}

Lesson: {incident["lesson"]}
"""

    client.retain(
        bank_id="recallops",
        content=memory
    )

    print(f"Stored {incident['incident_id']}")

client.close()

print("\nAll incidents stored successfully.")
