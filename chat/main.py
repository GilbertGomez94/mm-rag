import chainlit as cl
import requests
import json
import base64
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

URL = "http://localhost:8000/recipe"


IMAGES_PATH = os.path.join(BASE_DIR, "chat/images")


def call_langchain(question: str, images: list):
    data = {"question": question, "images": images}
    response = requests.post(url=URL, data=json.dumps(data))
    return response


def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

@cl.on_message
async def on_message(msg: cl.Message):
    encoded_images = []
    for file in msg.elements:
        if "image" in file.mime:
            encoded_images.append(encode_image(image_path=file.path))
    response = call_langchain(msg.content, encoded_images)
    if response.status_code == 200:
        data = response.json().get("response")
        for key, value in data.items() :
            print (key)
        images = data.get("context").get("images")
        front_images = []
        images_names = []
        for idx, value in enumerate(images):
            extension = value.split(";base64")[0].split("/")[1]
            extensionpssible = value.split(";base64,")[1]
            decoded_bytes = base64.b64decode(extensionpssible)
            images_names.append(f"./imgs/{idx}.{extension}")
            with open(f"{IMAGES_PATH}/{idx}.{extension}", "wb") as image_file:
                image_file.write(decoded_bytes)
            front_images.append(cl.Image(path=f"{IMAGES_PATH}/{idx}.{extension}", name=f"{idx}.{extension}", display="inline", size="small"))
    
        await cl.Message(
            content=data.get("response"),
            elements=front_images
            ).send()
        return
    
