import concurrent.futures
from mutagen.mp3 import MP3 
import tempfile 
import os 
import json 
import requests 

import shutil 

from dotenv import load_dotenv
from math import ceil

load_dotenv(os.path.join(os.getcwd(),'..','..','.env'),override=True)


def chunk_into_n(lst, n):
  size = ceil(len(lst) / n)
  return list(
    map(lambda x: lst[x * size:x * size + size],
    list(range(n)))
  )

def await_video_status(vid):

    url = f"{os.getenv('CDN_API_URL')}/videos/{vid}"
    headers = {
        'Content-Type': 'application/json',
        'AccessKey': os.getenv('CDN_API_KEY')
    }
    status = -1 
    while status < 4:
        response = requests.get(url,headers=headers)
        status = response.json()["status"] # Created = 0, Uploaded = 1, Processing = 2, Transcoding = 3, Finished = 4, Error = 5, UploadFailed = 6, Transcribing = 7
    return status


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
        status = await_video_status(vid_id)
        return f"{os.getenv('CDN_STATIC_URL')}/{vid_id}/play_720p.mp4"
    raise Exception("error uploading video to CDN") 
    return ""

def delete_tmpfile(filepath):
    tmpdir = '/'.join(filepath.split('/')[:-1])
    shutil.rmtree(tmpdir)


def generate_filepath(file,dir=os.getenv('TEMP_DIR','./tmpdir')):
    if not os.path.exists(dir): os.mkdir(dir)
    return os.path.join(tempfile.mkdtemp(dir=dir),file)


def multithreaded_func_call(f,inputs): # takes in a function to be run in parallel over list of args and return results in an arry 
    results = [None]*len(inputs) 
    input_idx_map = {str(a):i for i,a in enumerate(inputs)}
    print('input idx map',input_idx_map)
    with concurrent.futures.ThreadPoolExecutor() as executor: 
        future_to_input = {executor.submit(f,i):i for i in inputs}
        for future in concurrent.futures.as_completed(future_to_input):
            arg = future_to_input[future]
            try: 
                print('for input: ',arg)
                data = future.result()
                print('the results ',data)
                idx = input_idx_map[str(arg)]
                results[idx] = data
            except Exception as e: 
                print(e)
    
    return results 

def audio_file_duration(audio_file):
    return int(MP3(audio_file).info.length)

def get_video_clip_size(clip): # assuming bit depth of 24 and fps of 24
    return 24*clip.duration*clip.w*clip.h*3/1e6
