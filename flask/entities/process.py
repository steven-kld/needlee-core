import os, re, subprocess, json
from collections import defaultdict
from .respondents import update_respondent_status
from atoms import (
    get_bucket, 
    list_blobs, 
    get_last_attempt, 
    init_whisper, 
    transcribe, 
    init_openai, 
    respond_with_ai, 
    get_real_duration,
    needs_fixing,
    reencode_webm,
    sort_webm_files,
    run_query,
    upload_file_to_path
)

def download_attempt_files(org_id, interview_id, user_id, attempt, logger):
    try:
        bucket = get_bucket(org_id, logger)
        if bucket is None:
            logger.error("🚫 Aborting: GCS bucket not available.")
            return []

        if not attempt:
            attempt = get_last_attempt(org_id, interview_id, user_id)
            logger.info(f"🔁 No attempt provided, using last found attempt: {attempt}")
            if attempt == 0:
                logger.error("❌ No attempts found for respondent.")
                return []
        
        prefix = f"{interview_id}/respondents/{user_id}/attempt_{attempt}"
        blobs = list_blobs(bucket, prefix)

        if not blobs:
            logger.error(f"❌ No records for attempt {attempt} found for respondent {user_id}.")
            return []

        downloaded_files = []
        local_dir = f"temp/{user_id}"
        logger.log_time(f"Ready for files downloading")
        for blob in blobs:
            if not blob.name.endswith(".webm"): continue
            filename = blob.name.split("/")[-1]
            local_path = os.path.join(local_dir, filename)
            blob.download_to_filename(local_path)
            logger.log_time(f"✅ File {filename} has been downloaded to {local_dir}")
            downloaded_files.append(filename)

        return downloaded_files
    
    except Exception as e:
        logger.exception(f"❌ Error during download_attempt_files: {e}")
        return []

def generate_transcription(user_id, questions, logger, language_code):
    whisper = None
    try:
        whisper = init_whisper()
        logger.log_time(f"✅ Whisper is ready")
    except Exception as e:
        logger.exception(f"❌ Failed to initialize Whisper: {e}")
        return None

    grouped = _group_chunks(user_id, logger)
    if grouped == {}:
        logger.exception(f"❌ Failed to group chunks")
        return None
    logger.log_time(f"✅ Chunks grouped")

    data = []

    for question_num, chunks in grouped.items():
        question = questions[question_num]["question"]
        expected = questions[question_num]["expected"]
        transcription = ""
        for chunk_idx in chunks:
            file = f"temp/{user_id}/{question_num}_{chunk_idx}.webm"
            try:
                text, prob = transcribe(file, whisper, language_code)
                if text is None:
                    logger.exception(f"⚠️ Skipped corrupt or unreadable chunk: {file}")
                    continue
                if len(text.strip()) > 1:
                    transcription += str(text) + " "
            except Exception as e:
                logger.exception(f"❌ Transcription failed for {file}: {e}")

        if transcription == "":
            transcription = "No answer provided"
        
        data.append({
            "question": question,
            "expected": expected,
            "answer": transcription
        })
        logger.log_time(f"✅ Question {question_num} transcribed")
        
    return data
    

def _group_chunks(user_id, logger=None):
    folder = f"temp/{user_id}"
    if not os.path.exists(folder):
        if logger: logger.error(f"❌ Folder {folder} does not exist.")
        return {}

    try:
        files = sorted([
            f for f in os.listdir(folder) if re.match(r"\d+_\d+\.webm", f)
        ], key=lambda f: tuple(map(int, f[:-5].split("_"))))
    except Exception as e:
        if logger: logger.exception(f"❌ Failed to sort chunk filenames in {folder}: {e}")
        return {}

    grouped = defaultdict(list)

    for f in files:
        try:
            q, c = map(int, f[:-5].split("_"))
            grouped[q].append(c)
        except Exception as e:
            if logger: logger.info(f"⚠️ Skipping malformed filename '{f}': {e}")
            continue

    if not grouped and logger:
        logger.info(f"⚠️ No valid chunk files found in {folder}.")

    return dict(grouped)

def rate_answer_set(data, logger, language_name):
    openai_client = None
    try:
        openai_client = init_openai()
        logger.log_time(f"✅ OpenAI client is ready")
    except Exception as e:
        logger.exception(f"❌ Failed to initialize OpenAI client: {e}")
        return None
    
    rated = []

    for item in data:
        prompt = f"""
You are evaluating an interview fragment. The input is in {language_name}. The review must also be in {language_name}.

Question: {item["question"]}
Expected answer: {item["expected"]}
Respondent's answer: {item["answer"]}

Rate the respondent's answer on a scale from 1 to 5:
5 - fully matches expectations
4 - mostly matches
3 - partially matches
2 - off-topic
1 - missing or inappropriate

Respond strictly in JSON in {language_name}:
{{
  "rate": <number from 1 to 5>,
  "review": "<short explanation, max 255 characters, in {language_name}>"
}}

Do not include any formatting like ```json. Return plain valid JSON only.
"""
        response = respond_with_ai(prompt, openai_client)
        
        try:
            parsed = json.loads(
                extract_json_block(response)
            )
            item["rate"] = parsed.get("rate")
            item["review"] = parsed.get("review")
        except Exception as e:
            logger.exception("❌ Failed to parse GPT response:", e)
            item["rate"] = 1
            item["review"] = "Failed to review."

        rated.append(item)
        logger.log_time(f"✅ Question successfully rated | Question: {item['question']} | Rate {item['rate']}")
    
    summary = summarize_interview(rated, openai_client, logger, language_name)
    logger.log_time(f"✅ Summary success | Rate {summary['rate']}")
    return {
        "interview": rated,
        "summary": summary
    }

def summarize_interview(rated, openai_client, logger, language_name):
    prompt = f"Below are interview answers in {language_name}:\n\n"

    for item in rated:
        prompt += (
            f"Question: {item['question']}\n"
            f"Answer: {item['answer']}\n"
            f"Rate: {item['rate']}\n"
            f"Comment: {item['review']}\n\n"
        )

    prompt += f"""
1. Give an overall interview score from 1 to 5.
2. Write a short summary (max 500 characters) analyzing the respondent’s behavior and answers.

Respond strictly in JSON in {language_name}:
{{
  "rate": <number from 1 to 5>,
  "review": "<summary in {language_name}, max 500 characters>"
}}

Do not include markdown or ```json - return only valid JSON.
"""
    response = respond_with_ai(prompt, openai_client, max_tokens=4000)

    try:
        result = json.loads(
            extract_json_block(response)
        )
        return result
    except Exception as e:
        logger.exception("❌ Failed to parse interview summary:", e)
        return {
            "rate": 1,
            "review": "Failed to rate the interview."
        }

def extract_json_block(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    raise ValueError("No JSON block found in GPT response")

def build_video(user_id, total_question_count, logger):
    logger.info(f"Building video...")
    directory = f"temp/{user_id}"
    fixed_dir = os.path.join(directory, "fixed")
    os.makedirs(fixed_dir, exist_ok=True)

    webm_files = sort_webm_files(user_id)
    inputs = []
    filters = []
    timecodes = {f"q{i}": None for i in range(total_question_count)}
    current_time = 0.0
    previous_part = None
    first_timestamp_written = False

    stream_index = 0  # use this instead of enumerate
    for webm in webm_files:
        part_number = int(webm.split("_")[0])
        src_path = os.path.join(directory, webm)
        fixed_path = os.path.join(fixed_dir, f"fixed_{webm}")

        fix_required = needs_fixing(src_path)
        if fix_required is None:
            logger.info(f"⚠️ Skipping unreadable file: {webm}")
            continue
        try:
            if fix_required:
                reencode_webm(src_path, fixed_path)
            else:
                subprocess.run(["cp", src_path, fixed_path], check=True)
        except subprocess.CalledProcessError:
            logger.exception(f"❌ Failed to prepare {webm}, skipping.")
            continue

        inputs.extend(["-i", fixed_path])
        filters.append(f"[{stream_index}:v:0][{stream_index}:a:0]")
        stream_index += 1

        # Timecode logic
        part_number = int(webm.split("_")[0])
        if previous_part is not None and part_number != previous_part:
            minutes = int(current_time // 60)
            seconds = int(current_time % 60)
            timecodes[f"q{part_number}"] = f"{minutes}:{seconds:02}"
            
        previous_part = part_number

        duration = get_real_duration(fixed_path)
        if not first_timestamp_written:
            timecodes[f"q{part_number}"] = "0:00"
            first_timestamp_written = True
        elif previous_part is not None and part_number != previous_part:
            minutes = int(current_time // 60)
            seconds = int(current_time % 60)
            timecodes[f"q{part_number}"] = f"{minutes}:{seconds:02}"

        current_time += duration
        previous_part = part_number
        logger.log_time(f"✅ {webm} fixed")

    if not filters:
        logger.exception(f"❌ No valid chunks found for user {user_id}. Skipping concat.")
        return []

    # Prepare filter_complex
    filter_concat = ''.join(filters) + f"concat=n={len(filters)}:v=1:a=1[outv][outa]"

    output_path = os.path.join(directory, "interview.webm")

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_concat,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libvpx", "-b:v", "1M", "-c:a", "libopus",
        output_path
    ]

    subprocess.run(cmd, check=True)
    logger.log_time(f"✅ Video built & timecodes ready")
    return timecodes

def upload_interview(user_id, respondent_id, interview_id, org_id, data, logger):
    try:
        if not isinstance(data, dict):
            logger.exception(f"❌ Review data invalid")
            raise TypeError("review data must be a Python dict")

        if insert_review(respondent_id, interview_id, json.dumps(data), logger) == None: 
            upload_file_to_path(
                get_bucket(org_id), 
                f"{interview_id}/respondents/{user_id}/process.log", 
                f"temp/{user_id}/process.log"
            )
            update_respondent_status(respondent_id, "error")
            return
        
        upload_file_to_path(
            get_bucket(org_id), 
            f"{interview_id}/respondents/{user_id}/interview.webm", 
            f"temp/{user_id}/interview.webm"
        )

        upload_file_to_path(
            get_bucket(org_id), 
            f"{interview_id}/respondents/{user_id}/process.log", 
            f"temp/{user_id}/process.log"
        )

        update_respondent_status(respondent_id, "processed")

    except:
        update_respondent_status(respondent_id, "error")

        upload_file_to_path(
            get_bucket(org_id), 
            f"{interview_id}/respondents/{user_id}/process.log", 
            f"temp/{user_id}/process.log"
        )

def insert_review(respondent_id, interview_id, data_json, logger):
    try:
        return run_query(
            """
            INSERT INTO reviews (
                respondent_id, interview_id, review_data
            ) VALUES (%s, %s, %s)
            RETURNING *
            """,
            (respondent_id, interview_id, data_json),
            fetch_one=True
        )
    except Exception as e:
        logger.exception(f"Failed to insert review for respondent {respondent_id}: {e}")
        return None
