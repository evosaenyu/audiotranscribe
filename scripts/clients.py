from dotenv import load_dotenv
import os 
from openai import OpenAI

load_dotenv(os.path.join(os.getcwd(),'..','.env'),override=True) 

# Initialize the OpenAI client with your API key
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
