import requests
import subprocess
import os
import random
import json
from datetime import datetime, timedelta

#CODE WILL NOT WORK ON CLONE, API KEY MUST BE INSERTED

def read_json(file_name):
    with open(file_name, 'r') as f:
        return json.load(f)

def get_video_duration(video_path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path], stdout=subprocess.PIPE, text=True)
    return float(result.stdout.strip())

def download_videos(keyword, required_duration):
    video_paths = []
    url = f"https://api.pexels.com/videos/search"
    headers = {
        "Authorization": PEXELS_API_KEY
    }
    params = {
        "query": keyword,
        "per_page": 50
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        total_duration = 0
        checks_remaining = 50
        while checks_remaining > 0:
            random_video = random.choice(data.get('videos', []))
            video_file = random_video['video_files'][0]
            width = video_file['width']
            height = video_file['height']
            if width == (height / 9) * 16:
                video_url = video_file['link']
                r = requests.get(video_url, stream=True)
                if r.status_code == 200:
                    video_path = f"{keyword}_{random.randint(1, 10000)}.mp4"
                    with open(video_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024):
                            f.write(chunk)
                    video_path = adjust_framerate(video_path)
                    video_duration = get_video_duration(video_path)
                    if total_duration + video_duration >= required_duration:
                        if total_duration < required_duration:
                            remaining_duration = required_duration - total_duration
                            trimmed_path = trim_video(video_path, remaining_duration)
                            video_paths.append(trimmed_path)
                        else:
                            video_paths.append(video_path)
                        break
                    else:
                        video_paths.append(video_path)
                        total_duration += video_duration
                else:
                    print(f"Failed to download video for '{keyword}'")
            else:
                print(f"Randomly selected video for '{keyword}' does not have a 16:9 aspect ratio.")
            checks_remaining -= 1
    else:
        print(f"Error fetching videos for '{keyword}': {response.status_code} - {response.text}")
    
    return video_paths

def adjust_framerate(video_path):
    output_path = f"{os.path.splitext(video_path)[0]}_60fps.mp4"
    cmd_convert = ['ffmpeg', '-i', video_path, '-r', '60', '-an', '-c:v', 'copy', output_path]
    subprocess.run(cmd_convert, check=True)
    os.remove(video_path)
    return output_path

def trim_video(video_path, duration):
    output_path = f"{os.path.splitext(video_path)[0]}_trimmed.mp4"
    cmd_trim = ['ffmpeg', '-i', video_path, '-t', str(duration), '-c', 'copy', output_path]
    subprocess.run(cmd_trim, check=True)
    os.remove(video_path)
    return output_path

def create_black_segment(start_time, end_time, output_file):
    duration = (end_time - start_time).total_seconds()
    cmd_black = ['ffmpeg', '-f', 'lavfi', '-t', str(duration), '-i', 'color=c=black:s=1280x720:r=60', '-vf', 'fps=60', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-an', '-y', output_file]
    subprocess.run(cmd_black, check=True)

def concatenate_videos(video_paths, output_file="output.mp4"):
    overwrite_file(output_file)
    
    with open('input.txt', 'w') as f:
        for path in video_paths:
            f.write(f"file '{path}'\n")
    
    cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'input.txt', '-c', 'copy', output_file]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during ffmpeg execution: {e}")
    finally:
        for path in video_paths:
            if os.path.exists(path):
                os.remove(path)
                print(f"Deleted: {path}")
        if os.path.exists('input.txt'):
            os.remove('input.txt')
            print("Deleted: input.txt")

def overwrite_file(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)
        print(f"Removed existing file: {file_name}")
    else:
        print(f"No existing file found: {file_name}")

def extract_audio(video_file, audio_file):
    cmd_extract = [
        'ffmpeg', '-i', video_file, '-q:a', '0', '-map', 'a', audio_file, '-y'
    ]
    subprocess.run(cmd_extract, check=True)

def add_audio_to_video(video_file, audio_file, output_file):
    cmd_overlay = [
        'ffmpeg', '-i', video_file, '-i', audio_file, '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental', output_file, '-y'
    ]
    subprocess.run(cmd_overlay, check=True)

# Working Usage
json_file = "highlighted_words.json"
captions = read_json(json_file)
video_file = "Test.mp4"
total_duration = get_video_duration(video_file)
video_start_time = datetime.strptime("00:00:00", "%H:%M:%S")
video_end_time = video_start_time + timedelta(seconds=total_duration)
all_video_paths = []
last_end_time = video_start_time

for segment in captions:
    start_time = datetime.strptime(segment['start_timestamp'], "%H:%M:%S.%f")
    end_time = datetime.strptime(segment['end_timestamp'], "%H:%M:%S.%f")
    duration = (end_time - start_time).total_seconds()

    if start_time > last_end_time:
        black_segment_path = f"black_{last_end_time.strftime('%H-%M-%S')}_{start_time.strftime('%H-%M-%S')}.mp4"
        create_black_segment(last_end_time, start_time, black_segment_path)
        all_video_paths.append(black_segment_path)
    
    pexels_videos = download_videos(segment['start'], duration)
    if pexels_videos:
        all_video_paths.extend(pexels_videos)

    last_end_time = end_time

if last_end_time < video_end_time:
    black_segment_path = "black_end.mp4"
    create_black_segment(last_end_time, video_end_time, black_segment_path)
    all_video_paths.append(black_segment_path)

concatenate_videos(all_video_paths, "output.mp4")
extract_audio('Test.mp4', 'test_audio.aac')
add_audio_to_video('output.mp4', 'test_audio.aac', 'final_output.mp4')

# done running
os.remove('test_audio.aac')
os.remove('output.mp4')