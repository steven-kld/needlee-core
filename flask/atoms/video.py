from dotenv import load_dotenv

load_dotenv()

import os, subprocess, re, json

def get_real_duration(path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except:
        return 0.0

def has_frames(path):
    def get_nb_read_frames(stream_type):
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error",
                "-count_frames",
                "-select_streams", stream_type,
                "-show_entries", "stream=nb_read_frames",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path
            ], capture_output=True, text=True)
            return int(result.stdout.strip())
        except:
            return 0

    return get_nb_read_frames("v:0") > 0 or get_nb_read_frames("a:0") > 0

def needs_fixing(path, VALID_VIDEO={"vp8", "vp9", "av1"}, VALID_AUDIO={"opus", "vorbis"}, CHUNK_DURATION=15):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path
    ], capture_output=True, text=True)

    info = json.loads(result.stdout)
    video_codec = None
    audio_codec = None
    duration = 0
    fps_valid = True

    for stream in info.get("streams", []):
        if stream["codec_type"] == "video":
            video_codec = stream.get("codec_name")
            try:
                fps = eval(stream.get("r_frame_rate", "0/1"))
                if fps < 10 or fps > 60:
                    fps_valid = False
            except:
                fps_valid = False
        elif stream["codec_type"] == "audio":
            audio_codec = stream.get("codec_name")

        try:
            stream_duration = float(stream.get("duration", 0))
            duration = max(duration, stream_duration)
        except:
            pass

    try:
        format_duration = float(info.get("format", {}).get("duration", 0))
        duration = max(duration, format_duration)
    except:
        pass

    if duration < 0.2:
        if has_frames(path):
            print(f"⚠️  Zero-duration but has frames - reencoding: {path}")
            return True
        elif video_codec in VALID_VIDEO and audio_codec in VALID_AUDIO:
            print(f"⚠️  Skipping: {path} has ~0-second duration with valid codecs and no frames")
            return None
        else:
            print(f"⚠️  Forcing re-encode of {path} despite 0s duration (non-WebM codec)")
            return True

    if video_codec not in VALID_VIDEO or audio_codec not in VALID_AUDIO:
        print(f"❗ Re-encoding required (invalid codec)")
        return True
    if not fps_valid:
        print(f"❗ Re-encoding required (bad FPS)")
        return True
    if duration < CHUNK_DURATION * 0.9:
        print(f"❗ Re-encoding required (too short)")
        return True

    return False

def reencode_webm(src, dst):
    subprocess.run([
        "ffmpeg", "-y", "-i", src,
        "-c:v", "libvpx", "-b:v", "1M",
        "-c:a", "libopus",
        dst
    ], check=True)

def sort_webm_files(user_id):
    directory = f"temp/{user_id}"
    webm_files = [f for f in os.listdir(directory) if f.endswith(".webm")]
    return sorted(webm_files, key=sorting_key)

def sorting_key(filename):
    match = re.match(r"(\d+)_(\d+)\.webm", filename)
    if match:
        first, second = map(int, match.groups())
        return (first, second)
    return (float('inf'), float('inf'))
