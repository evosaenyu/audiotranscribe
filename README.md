Prerequisites
- portaudio
- ffmpeg
- pyaudio

 - duplicate template.env to .env file and populate the necessary environment variables

Installation
- OLLAMA (install from here: https://ollama.com/download)
- pip3 install -r requirements.txt

How to Run

BACKEND WEBSOCKET STREAM: 
    - cd api && fastapi app.py 
WEB UI: 
    - streamlit run Home.py

Feature List
- cut off command 
- Q&A on story 
- roleplay story 
- user influence on story
- improve image presentation (slideshow, opencv mp4 etc)
- modes: instruct, story, game etc, presentation reviewer

TODO
- create a new file called StreamLitDemo.py ✓
- host hello world✓
- host textarea with mic input ✓
- print whats being said ✓
- host output text area with chatgpt responses ✓
- deploy ✓
- speak text to audio ✓
- langchain-ize to feed inputs to DALL-e
- image area 
- sidebar
- show chat history
- different system prompts
- email newsletter sign-up
- design Blender of product
- pose and lighting
- add to site in a nice way