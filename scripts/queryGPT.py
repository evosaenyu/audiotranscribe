from openai import OpenAI
import text_to_speech
from clients import openai_client as client 



def send_query(messages):
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages
    )
    returnMessage = completion.choices[0].message.content
    text_to_speech.say_something(returnMessage)
    print(returnMessage)
    return {"role":completion.choices[0].message.role, "content":returnMessage}