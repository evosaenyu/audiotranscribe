import concurrent.futures
from mutagen.mp3 import MP3 
import tempfile 
import os 
import json 
import requests 
import ffmpeg 
import shutil 

import numpy as np 


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


def multithreaded_func_call(f,inputs,workers=8): # takes in a function to be run in parallel over list of args and return results in an arry 
    results = [None]*len(inputs) 
    input_idx_map = {str(a):i for i,a in enumerate(inputs)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor: #todo make max_workers a 
        future_to_input = {executor.submit(f,i):i for i in inputs}
        for future in concurrent.futures.as_completed(future_to_input):
            a = future_to_input[future]
            data = future.result()
            idx = input_idx_map[str(a)]
            results[idx] = data    
    
    return results 

def audio_file_info(audio_file):
    mp3 =MP3(audio_file)
    return int(mp3.info.length),int(mp3.info.sample_rate)

def get_video_clip_size(clip): # assuming bit depth of 24 and fps of 24
    return 24*clip.duration*clip.w*clip.h*3/1e6


def compress_video(video_full_path,target_size):
    # Reference: https://en.wikipedia.org/wiki/Bit_rate#Encoding_bit_rate
    min_audio_bitrate = 32000
    max_audio_bitrate = 256000
    output_file_path = "/".join(video_full_path.split("/")[:-1] + ['compressed.mp4'])
    probe = ffmpeg.probe(video_full_path)
    # Video duration, in s.
    duration = float(probe['format']['duration'])
    # Audio bitrate, in bps.
    audio_bitrate = float(next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)['bit_rate'])
    # Target total bitrate, in bps.
    target_total_bitrate = (target_size * 1024 * 8) / (1.073741824 * duration)

    # Target audio bitrate, in bps
    if 10 * audio_bitrate > target_total_bitrate:
        audio_bitrate = target_total_bitrate / 10
        if audio_bitrate < min_audio_bitrate < target_total_bitrate:
            audio_bitrate = min_audio_bitrate
        elif audio_bitrate > max_audio_bitrate:
            audio_bitrate = max_audio_bitrate
    # Target video bitrate, in bps.
    video_bitrate = target_total_bitrate - audio_bitrate

    i = ffmpeg.input(video_full_path)
    ffmpeg.output(i, os.devnull,
                  **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 1, 'f': 'mp4'}
                  ).overwrite_output().run()
    ffmpeg.output(i, output_file_path,
                  **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 2, 'c:a': 'aac', 'b:a': audio_bitrate}
                  ).overwrite_output().run()

    return output_file_path

def vidwrite(fn, images, audio,framerate=60, vcodec='libx264'):
    if not isinstance(images, np.ndarray):
        images = np.asarray(images)
    n,height,width,channels = images.shape
    process = (
        ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='rgb24', s='{}x{}'.format(width, height),r=f'{framerate}')
            .output(fn, vcodec=vcodec,pix_fmt='yuv420p',**{'c:v': 'libx264','pass': 1,'f': 'mp4'}) #'b:v': video_bitrate,
            # .output(fn, pix_fmt='yuv420p', vcodec=vcodec, r=framerate)
            .overwrite_output()
            .run_async(pipe_stdin=True)
    )

    for frame in images:
        process.stdin.write(
            frame
                .astype(np.uint8)
                .tobytes()
        )
    process.stdin.close()
    process.wait()
    input_video = ffmpeg.input(fn)

    input_audio = ffmpeg.input(audio)
    output_file_path = "/".join(fn.split("/")[:-1] + ['compressed.mp4'])
    ffmpeg.concat(input_video, input_audio, v=1, a=1).output(output_file_path).run() 
    delete_tmpfile(fn)
    return output_file_path