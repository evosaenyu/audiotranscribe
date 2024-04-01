

from clients import openai_client as client 

def generate_image(prompt, n=7):
    response = client.images.generate(
    model="dall-e-2",
    prompt=prompt,
    style="natural",
    size="1024x1024",
    quality="standard",
    n=n,
    )

    image_urls = [r.url for r in response.data]
    return image_urls