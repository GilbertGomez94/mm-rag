import chainlit as cl
import requests
import json
import base64
import os


URL = "http://localhost:8000/recipe"

IMAGES_PATH = os.path.join("/home/gilbert/Documentos/experiments/mm-rag/", "chat/images")

def call_langchain(question: str, images: list):
    data = {"question": question, "images": images}
    response = requests.post(url=URL, data=json.dumps(data))
    return response


def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

@cl.on_message
async def on_message(msg: cl.Message):
    # if not msg.elements:
    #     await cl.Message(content="No file attached").send()
    #     return

    # Processing images exclusively


    encoded_images = []
    for file in msg.elements:
        if "image" in file.mime:
            encoded_images.append(encode_image(image_path=file.path))
    print(encoded_images[0])
    response = call_langchain(msg.content, encoded_images)
    images = response.json().get("response").get("context").get("images")
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
    if response.status_code == 200:
        await cl.Message(
            content=response.json().get("response").get("response"),
            elements=front_images
            ).send()
        return
    
    # print(encoded_images)
        
    # images = [file for file in msg.elements if "image" in file.mime]

    # Read the first image
    # with open(images[0].path, "r") as f:
    #     pass

    # await cl.Message(content=f"Received {len(images)} image(s)").send()

