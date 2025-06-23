import os, openai, requests, json
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from decimal import Decimal, ROUND_HALF_UP

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
    
def respond_with_ai(prompt, openai_client, max_tokens=500, model="gpt-4.1", role="user"):
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{
            "role": role,
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

    input_tokens = response.usage.prompt_tokens       # ← number of input tokens
    output_tokens = response.usage.completion_tokens   # ← number of output tokens
    in_cost, out_cost = gpt_cost(model, input_tokens, output_tokens)
    print(in_cost, out_cost)
    return response.choices[0].message.content, in_cost, out_cost

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
        duration = data["metadata"]["duration"]
        text = data["results"]["channels"][0]["alternatives"][0]["transcript"]

        return text, deepgram_cost(duration), duration
    except Exception as e:
        print(f"❌ Deepgram STT failed for {wav_path}: {e}")
        return None, 0.0, 0.0

def deepgram_cost(duration):
    price_minute = 0.0054 # Multi Nova-3 price Pay As You Go
    price_second = price_minute / 60
    return round(
        round(float(duration)) * price_second, 6
    )

def gpt_cost(model: str, input_tokens: int, output_tokens: int):
    PRICING = {
        "gpt-4.1": {
            "input": Decimal("0.00000200"),
            "output": Decimal("0.00000800")
        },
        "gpt-4.1-mini": {
            "input": Decimal("0.00000040"),
            "output": Decimal("0.00000160")
        },
        "gpt-4.1-nano": {
            "input": Decimal("0.00000010"),
            "output": Decimal("0.00000040")
        }
    }

    p = PRICING[model]
    in_cost = (Decimal(input_tokens) * p["input"]).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    out_cost = (Decimal(output_tokens) * p["output"]).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    return float(in_cost), float(out_cost)


def log_cost(component, cost_usd, metadata=None):
    log = {
        "component": component,
        "cost_usd": round(cost_usd, 6),
        "metadata": metadata or {},
    }
    print("💰 COST LOG:", json.dumps(log))  # Replace with file/DB write if needed
