from atoms import run_query, get_bucket, list_blobs, blob_exists, get_signed_url
import time

def get_questions(interview_id):
    return run_query(
        """
        SELECT question_num, question FROM questions
        WHERE interview_id = %s
        ORDER BY question_num ASC
        """,
        (interview_id,),
        fetch_all=True
    )

def get_question_audio_url(org_id, interview_id, question_num, expiration=3600):
    bucket = get_bucket(org_id)
    path = f"{interview_id}/questions/{question_num}.mp3"
    return get_signed_url(bucket, path, expiration)

def get_latest_attempt_number(org_id, interview_id, respondent_uuid):
    bucket = get_bucket(org_id)
    prefix = f"{interview_id}/respondents/{respondent_uuid}/"
    seen = set()
    for blob in list_blobs(bucket, prefix=prefix):
        parts = blob.name[len(prefix):].split('/')
        if parts and parts[0].startswith("attempt_"):
            try:
                seen.add(int(parts[0].split("_")[1]))
            except Exception:
                continue
    return max(seen, default=1)

def wait_for_attempt_ready(org_id, interview_id, respondent_uuid, attempt_num, timeout=10):
    bucket = get_bucket(org_id)
    path = f"{interview_id}/respondents/{respondent_uuid}/attempt_{attempt_num}/.ready"
    for _ in range(timeout * 10):
        if blob_exists(bucket, path):
            return True
        time.sleep(0.1)
    return False
