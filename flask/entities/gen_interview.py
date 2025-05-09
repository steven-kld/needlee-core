import json, re
from atoms import (
    init_openai, 
    respond_with_ai,
    synthesize_voice,
    get_bucket,
    create_empty_blob,
    upload_blob_from_bytes,
    blob_exists
)

def generate_interview_from_text(raw_text):
    openai_client = init_openai()
    lang = detect_language(raw_text, openai_client)

    prompt = f"""
You are an expert at designing structured interviews.

Given the following raw text in {lang}, do the following:
1. Summarize the topic with a short title (max 3-4 words).
2. Write a short second-person description to show the respondent what the interview will cover (1-2 sentences).
3. Write a short thank-you message in a respectful tone. Thank the respondent for their time and focus on the questions. Avoid flattery. Keep it under 20 words.
4. Write 7 deep, thoughtful interview questions that comprehensively cover the core ideas, events, and implications of the text.
5. For each question, write a multilayered expected answer - a short paragraph (max 330 characters) that touches on the key facts, reasoning, and context a well-informed respondent should mention.

Return the result as JSON in this format:

{{
  "language": "{lang}",
  "display_name": "...",
  "description": "...",
  "thank_you_text": "...",
  "questions": [
    {{
      "question": "...",
      "expected": "..."
    }},
    ...
  ]
}}

Raw text:
\"\"\"
{raw_text}
\"\"\"
"""

    estimated_tokens = len(prompt) // 4
    max_tokens = min(int(estimated_tokens * 1.25), 6000)

    response = respond_with_ai(prompt, openai_client=openai_client, max_tokens=max_tokens)

    try:
        block = extract_json_block(response)
        res = json.loads(block)
        return res
    except Exception as e:
        print(f"❌ GPT response parsing failed: {e}")
        print("Raw GPT response:", response)
        return None

def generate_interview_from_questions(questions):
    pass

def detect_language(text, openai_client):
    short_sample = text.strip()[:50]
    prompt = f"What language is this text written in? Respond only with the ISO-639-1 code like 'en', 'es', 'fr'.\n\n{short_sample}"
    lang = respond_with_ai(prompt, openai_client)
    return lang.strip().lower()

def extract_json_block(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    raise ValueError("No JSON block found in GPT response")

def record_interview_questions(questions):
    audio_blobs = []

    for i, q in enumerate(questions):
        try:
            audio = synthesize_voice(q["question"])
            audio_blobs.append((i, audio))  # use index, not id
        except Exception as e:
            print(f"❌ Failed to synthesize question {i}: {e}")

    return audio_blobs

def prepare_interview_folder(org_id, interview_id):
    bucket = get_bucket(org_id)
    create_empty_blob(bucket, f"{interview_id}/questions/.ready")
    create_empty_blob(bucket, f"{interview_id}/respondents/.ready")

def upload_interview_audio(org_id, interview_id, blobs):
    bucket = get_bucket(org_id)
    ready_marker = f"{interview_id}/questions/.ready"

    if not blob_exists(bucket, ready_marker):
        raise RuntimeError(f"❌ Cannot upload audio: {ready_marker} marker not found.")

    for idx, blob in blobs:
        path = f"{interview_id}/questions/{idx}.mp3"
        upload_blob_from_bytes(bucket, path, blob, content_type="audio/mpeg")
        print(f"✅ Uploaded question {idx}")


