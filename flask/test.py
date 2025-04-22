import requests
import uuid
import time

API_BASE = "http://127.0.0.1:5000"
ORG_ID = 1
INTERVIEW_ID = 1
CONTACT = "tester-2@example.com"
UUID = str(uuid.uuid4())

session_payload = {
    "o": ORG_ID,
    "i": INTERVIEW_ID,
    "c": CONTACT,
    "uuid": UUID
}

print("▶️  Sending interview session init...")
res = requests.post(f"{API_BASE}/api/interview-session", json=session_payload)
print("Session response:", res.status_code, res.json())

if res.json().get("completed"):
    print("✅ Interview already completed. No need to proceed.")
    exit(0)



questions_payload = {
    "o": ORG_ID,
    "i": INTERVIEW_ID,
    "uuid": UUID
}

print("▶️  Requesting questions...")
res = requests.post(f"{API_BASE}/api/get-questions", json=questions_payload)
print("Questions response:", res.status_code)
print(res.json())
