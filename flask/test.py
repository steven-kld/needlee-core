from atoms import (
    init_openai, 
    respond_with_ai,
    synthesize_voice,
    create_org_bucket,
    get_bucket,
    create_empty_blob,
    upload_blob_from_bytes,
    deepgram_transcribe,
    blob_exists
)

from services.process_manager import ProcessManager

# def save_blob_to_file(blob_data, filename="audio.mp3"):
#     with open(filename, 'wb') as f:
#         f.write(blob_data)

# # Usage:
# blob = synthesize_voice("Hello it's me! Wow, haven't seen you for ages! How are you? What's going on?")
# save_blob_to_file(blob, "output.mp3")

# text, deepgram_price = deepgram_transcribe("output.wav")
# print(text)
# print(deepgram_price)

# def _fix_transcription(transcription, question, expected, openai_client):
#     prompt = f"""
# The respondent's answer was transcribed by AI and may contain minor recognition errors.

# Your task is to correct only obvious spelling or grammatical mistakes without changing the original word order or adding new information.

# Use the question and expected answer as context to resolve unclear words, but DO NOT rephrase, reorder, or complete the answer.

# Question: {question}
# Expected answer: {expected}
# Respondent's answer: {transcription}

# Return the fixed version of the respondent's answer as a plain string. No formatting, no extra comments.
# """
#     response, openai_price = respond_with_ai(prompt, openai_client, 1000, "gpt-4.1-mini")
#     return response, openai_price


# transcription = "My day was perfect! We started our jurney an 10 am and wus dricving at least 2 hours to reach the place, but it worthed it"
# question = "How did your day started? How was the journey and road to it?"
# expected = "Name exact time of the drive start"
# openai_client = init_openai()


# response, price = _fix_transcription(transcription, question, expected, openai_client)
# print(response)
# print(price)

# process = ProcessManager(
#     12, 
#     36, 
#     "510bee87-5fdd-452c-8200-bb0e68134e5e", 
#     1, 
#     False)
# process.process()
import json

cost_log ={'deepgram': [{'type': 'translate', 'sec': 14.71, 'price': 0.00135}, {'type': 'translate', 'sec': 12.65, 'price': 0.00117}, {'type': 'translate', 'sec': 8.95, 'price': 0.00081}], 'gpt': [{'type': 'fix', 'token_in_price': 7e-05, 'token_out_price': 3.5e-05, 'total_price': 0.000105}, {'type': 'fix', 'token_in_price': 7.1e-05, 'token_out_price': 5.6e-05, 'total_price': 0.000127}, {'type': 'fix', 'token_in_price': 6.4e-05, 'token_out_price': 2.6e-05, 'total_price': 9e-05}, {'type': 'review', 'token_in_price': 0.000412, 'token_out_price': 0.0004, 'total_price': 0.000812}, {'type': 'review', 'token_in_price': 0.000416, 'token_out_price': 0.000312, 'total_price': 0.000728}, {'type': 'review', 'token_in_price': 0.000386, 'token_out_price': 0.00032, 'total_price': 0.000706}, {'type': 'summarize', 'token_in_price': 0.000668, 'token_out_price': 0.00064, 'total_price': 0.001308}]}
def summarize_cost(cost_log, processing_time_sec):
    deepgram = cost_log.get("deepgram", [])
    gpt = cost_log.get("gpt", [])

    transcribe_cost = round(sum(item["price"] for item in deepgram), 6)
    reasoning_cost = round(sum(item.get("total_price", 0) for item in gpt), 6)
    total_cost = round(transcribe_cost + reasoning_cost, 6)
    duration_sec = round(sum(item["sec"] for item in deepgram), 2)

    cost_log["total_cost"] = total_cost
    cost_log["transcribe_cost"] = transcribe_cost
    cost_log["reasoning_cost"] = reasoning_cost
    cost_log["duration_sec"] = duration_sec
    cost_log["processing_time_sec"] = processing_time_sec


def insert_interview_cost(respondent_id, interview_id, org_id, cost_log, logger):
    try:
        return print(
            """
            INSERT INTO interview_costs (
                respondent_id, interview_id, org_id,
                total_cost, transcribe_cost, reasoning_cost,
                cost_details, duration_sec, processing_time_sec
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                respondent_id,
                interview_id,
                org_id,
                cost_log["total_cost"],
                cost_log["transcribe_cost"],
                cost_log["reasoning_cost"],
                json.dumps(cost_log),
                cost_log["duration_sec"],
                cost_log["processing_time_sec"]
            ),
            # fetch_one=True
        )
    except Exception as e:
        logger.exception(f"❌ Failed to insert interview cost for respondent {respondent_id}: {e}")
        return None
    

summarize_cost(cost_log, 412)
print(cost_log)
insert_interview_cost(181, 36, 12, cost_log, None)