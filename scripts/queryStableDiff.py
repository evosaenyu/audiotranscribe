import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

def send_query(image_prompt, last_image_url=None):
    url = "https://stablediffusionapi.com/api/v3/text2img"
    payload = json.dumps({
    "key": os.getenv('STABLE_DIFF_KEY'),
    "prompt": image_prompt,
    "negative_prompt": None,
    "width": "512",
    "height": "512",
    "samples": "1",
    "num_inference_steps": "30",
    "safety_checker": "no",
    "enhance_prompt": "yes",
    "guidance_scale": 7.5,
    "strength": 0.7,
    "base64": "no",
    "seed": None,
    "webhook": None,
    "track_id": None
    })
    if last_image_url is not None:
        url = "https://stablediffusionapi.com/api/v3/img2img"
        payload["init_image"] = last_image_url

    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.post( url, headers=headers, data=payload)

    print(response.text)

def post_query_result():
    headers = {
    'Content-Type': 'application/json'
    }
    response = requests.post("https://stablediffusionapi.com/api/v3/fetch/86832682",headers=headers)

    print (response.text)
# send_query("a cat in a hat")
post_query_result()