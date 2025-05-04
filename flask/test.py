# user_id = "825098b6-524d-48da-8c03-ac2c00c705a3"
# user_contact = "long"
# interview_id = 1
# organization_id = 1
# attempt = None

# from services.process_manager import ProcessManager

# process = ProcessManager(organization_id, interview_id, user_id, attempt)
# process.process()

import sys
import os
import subprocess
from faster_whisper import WhisperModel

def convert_webm_to_wav(input_path, output_path=None):
    if not output_path:
        output_path = input_path.replace(".webm", ".wav")
    
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-ac", "1", "-ar", "16000",  # mono, 16kHz
            "-f", "wav", output_path
        ], check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg conversion failed: {e}")
    
def transcribe(path, whisper_model, language=None):
    try:
        segments, info = whisper_model.transcribe(path, language=language)
        segments = list(segments)

        text = "".join([s.text for s in segments]).strip()
        avg_prob = sum(s.no_speech_prob for s in segments) / max(len(segments), 1)
        return text, avg_prob
    except Exception as e:
        print(f"❌ Transcription failed for {path}: {e}")
        return None, 1.0

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test.py path/to/file.webm")
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.isfile(input_path):
        print(f"File not found: {input_path}")
        sys.exit(1)

    print(f"🔁 Converting: {input_path}")
    wav_file = convert_webm_to_wav(input_path)
    print(f"✅ Converted to: {wav_file}")

    print("🎧 Loading model...")
    model = WhisperModel("medium", compute_type="int8", download_root="/models")

    print("🧠 Transcribing...")
    seg, i = transcribe(wav_file, model, language="ru")
    print(seg, i)
    

if __name__ == "__main__":
    main()
