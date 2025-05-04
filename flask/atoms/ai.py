import os, openai
from dotenv import load_dotenv
from faster_whisper import WhisperModel

load_dotenv()

def init_openai():
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def init_whisper():
    return WhisperModel(
        "tiny",
        compute_type="int8",
        download_root="/models/models--Systran--faster-whisper-tiny"
    )

def init_eleven_labs():
    return True

def silence_prob(path, whisper_model, language=None):
    try:
        segments, info = whisper_model.transcribe(path, language=language)
        segments = list(segments)
        return sum(s.no_speech_prob for s in segments) / max(len(segments), 1)
    except Exception as e:
        print(f"❌ Transcription failed for {path}: {e}")
        return 1.0
    
def respond_with_ai(prompt, openai_client, max_tokens=500):
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        response_format={
            "type": "text"
        },
        temperature=0,
        max_tokens=max_tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].message.content

