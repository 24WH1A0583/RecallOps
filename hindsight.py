import os
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

client = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

new_incident = """
Payment API is returning HTTP 500 errors.
Database connections are failing during high traffic.
The service is currently unavailable.
"""

results = client.recall(
    bank_id="recallops",
    query=new_incident
)

print("\nSIMILAR PAST INCIDENTS:\n")

for memory in results.results:
    print(memory.text)
    print("-" * 60)