import requests
import subprocess
import os
import random

#CODE WILL NOT WORK ON CLONE, API KEY MUST BE INSERTED

def read_keywords(file_name):
    with open(file_name, 'r') as f:
        keywords = [line.strip() for line in f if line.strip()]
    return keywords

def download_videos(keywords, per_page=50):
    video_paths = []
    
    for keyword in keywords:
        url = f"https://api.pexels.com/videos/search"
        headers = {
            "Authorization": PEXELS_API_KEY
        }
        params = {
            "query": keyword,
            "per_page": per_page
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            videos_found = False
            checks_remaining = 50  # Number of checks for 16:9 aspect ratio
            
            while checks_remaining > 0:
                random_video = random.choice(data.get('videos', []))
                video_file = random_video['video_files'][0]
                width = video_file['width']
                height = video_file['height']
                
                if width == (height / 9) * 16:
                    video_url = video_file['link']
                    # Download the video
                    r = requests.get(video_url, stream=True)
                    if r.status_code == 200:
                        video_path = f"{keyword}.mp4"  # Save with keyword name
                        with open(video_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=1024):
                                f.write(chunk)
                        
                        video_path = adjust_framerate(video_path)
                        
                        video_paths.append(video_path)
                        videos_found = True
                        break
                    else:
                        print(f"Failed to download video for '{keyword}'")
                else:
                    print(f"Randomly selected video for '{keyword}' does not have a 16:9 aspect ratio.")
                
                checks_remaining -= 1
            
            if not videos_found:
                print(f"No suitable 16:9 videos found for '{keyword}' after checking 50 random videos.")
        else:
            print(f"Error fetching videos for '{keyword}': {response.status_code} - {response.text}")
    
    return video_paths

def adjust_framerate(video_path):
    # Convert to 60 FPS and remove audio using ffmpeg
    output_path = f"{os.path.splitext(video_path)[0]}_60fps.mp4"
    cmd_convert = ['ffmpeg', '-i', video_path, '-r', '60', '-an', '-c:v', 'copy', output_path]
    subprocess.run(cmd_convert, check=True)
    
    # Remove original video after conversion
    os.remove(video_path)
    
    print(f"Converted '{video_path}' to 60 FPS and removed audio.")
    
    return output_path

def overwrite_file(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)
        print(f"Removed existing file: {file_name}")
    else:
        print(f"No existing file found: {file_name}")

def concatenate_videos(video_paths, output_file="output.mp4"):
    overwrite_file(output_file)  # Ensure output file is overwritten if exists
    
    # Prepare the list file for ffmpeg input
    with open('input.txt', 'w') as f:
        for path in video_paths:
            f.write(f"file '{path}'\n")
    
    # Use ffmpeg to concatenate videos, copying only video streams (-an)
    cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'input.txt', '-an', '-c', 'copy', output_file]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during ffmpeg execution: {e}")
    finally:
        # Delete stock footage if specified
        for path in video_paths:
            if os.path.exists(path):
                os.remove(path)
                print(f"Deleted: {path}")
        
        if os.path.exists('input.txt'):
            os.remove('input.txt')
            print("Deleted: input.txt")

# Example usage
keywords_file = "keywords.txt"
keywords = read_keywords(keywords_file)
video_paths = download_videos(keywords)
concatenate_videos(video_paths)