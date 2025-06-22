import os, openai, requests
from dotenv import load_dotenv
from faster_whisper import WhisperModel

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DEEPGRAM_LANGS = {"en", "ru", "fr", "de", "es", "it", "pt", "nl"}
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = None

def synthesize_voice(text):
    global ELEVENLABS_VOICE_ID
    if ELEVENLABS_VOICE_ID is None:
        ELEVENLABS_VOICE_ID = get_voice_id_by_name("Rachel")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.3,
            "similarity_boost": 0.65,
            "style": 0.35,
            "use_speaker_boost": True
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"ElevenLabs TTS failed: {response.status_code} - {response.text}")

def list_available_voices():
    url = "https://api.elevenlabs.io/v2/voices"
    headers = { "xi-api-key": os.getenv("ELEVENLABS_API_KEY") }
    response = requests.get(url, headers=headers)
    voices = response.json().get("voices", [])
    for v in voices:
        print(f"- {v['name']} (ID: {v['voice_id']})")

def get_voice_id_by_name(voice_name: str):
    response = requests.get(
        "https://api.elevenlabs.io/v2/voices", 
        headers={ "xi-api-key": ELEVENLABS_API_KEY }
    )
    if response.status_code != 200:
        raise Exception(f"Failed to fetch voices: {response.status_code} - {response.text}")

    voices = response.json().get("voices", [])
    for v in voices:
        if v["name"].lower() == voice_name.lower():
            return v["voice_id"]

    raise ValueError(f"Voice '{voice_name}' not found.")

def init_openai():
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def init_whisper():
    return WhisperModel(
        "tiny",
        compute_type="int8",
        download_root="/models/models--Systran--faster-whisper-tiny"
    )

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

def deepgram_transcribe(wav_path, language="en"):
    # if language not in DEEPGRAM_LANGS:
    #     print(f"⚠️ Language '{language}' not supported by Deepgram")
    #     return None

    url = f"https://api.deepgram.com/v1/listen?model=nova-3&language=multi"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/wav"
    }

    try:
        with open(wav_path, "rb") as f:
            audio = f.read()

        response = requests.post(url, headers=headers, data=audio)
        response.raise_for_status()

        data = response.json()
        return data["results"]["channels"][0]["alternatives"][0]["transcript"]
    except Exception as e:
        print(f"❌ Deepgram STT failed for {wav_path}: {e}")
        return None
