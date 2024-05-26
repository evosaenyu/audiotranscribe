import concurrent.futures
import librosa 
import tempfile 
import os 
import json 
import requests 

import shutil 

from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(),'..','..','.env'))

def generate_video_id(title):
    url = f"{os.getenv('CDN_API_URL')}/videos"
    payload = json.dumps({"title": str(title)})
    headers = {
        'Content-Type': 'application/json',
        'AccessKey': os.getenv('CDN_API_KEY')
    }
    response = requests.post(url,headers=headers,data=payload)
    return response.json()["guid"]


def upload_video(filepath,title): 
    """ take in a videofile uploads it to CDN and returns the link it's served at"""
    vid_id = generate_video_id(title)
    url = f"{os.getenv('CDN_API_URL')}/videos/{vid_id}"
    headers = {
        'Content-Type': 'application/json',
        'AccessKey': os.getenv('CDN_API_KEY')
    }
    with open(filepath, 'rb') as f:
        data = f.read()
    response = requests.put(url,headers=headers,data=data)
    if response.json()["success"]: 
        return f"{os.getenv('CDN_STATIC_URL')}/{vid_id}"
    raise Exception("error uploading video to CDN") 
    return ""

def delete_tmpfile(filepath):
    tmpdir = '/'.join(filepath.split('/')[:-1])
    shutil.rmtree(tmpdir)


def generate_filepath(file):
    return os.path.join(tempfile.mkdtemp(),file)


def multithreaded_func_call(f,inputs): # takes in a function to be run in parallel over list of args and return results in an arry 
    results = [] 
    with concurrent.futures.ThreadPoolExecutor() as executor: 
        future_to_url = {executor.submit(f,i):i for i in inputs}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try: 
                data = future.result()
                results.append(data)
            except Exception as e: 
                print(e)
    
    return results 

def audio_file_duration(audio_arr):
    return int(librosa.get_duration(y=audio_arr,sr=44100))

def get_video_clip_size(clip): # assuming bit depth of 24 and fps of 24
    return 24*clip.duration*clip.w*clip.h*3/1e6
