import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

def send_query(image_prompt):
    url = "https://api.mymidjourney.ai/api/v1/midjourney/imagine"
    payload = json.dumps({
    "prompt": image_prompt
    })

    headers = {
    'Content-Type': 'application/json',
    "Authorization": f'Bearer {os.getenv('MIDJOURNEY_KEY')}',
    }

    response = requests.post( url, headers=headers, data=payload)

    print(response.text)

send_query("a cat in a hat")
# post_query_result()