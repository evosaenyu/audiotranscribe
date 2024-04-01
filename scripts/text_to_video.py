import time
import requests
import json

url = "https://stablediffusionapi.com/api/v5/text2video"

payload = json.dumps({
  "key": "Pba0M4jbLchATBlioYRZxhnLDxWkhaETKiNHu06qE0hxHq21lEecHclOUPTX",
  "prompt": "A mysterious figure approaching the campfire",
  "negative_prompt": "Low Quality",
  "scheduler": "UniPCMultistepScheduler",
  "seconds": 3
})

headers = {
  'Content-Type': 'application/json'
}

response = requests.post(url, headers=headers, data=payload)
json_response = json.loads(response.text)
final_link = json_response["future_links"][0]
print(final_link)
fetch_result = requests.get(final_link, headers=headers)
while fetch_result.status_code == 404:
    print("unready",fetch_result)
    fetch_result = requests.get(final_link, headers=headers)
    time.sleep(2)
print(response.json()["output"])