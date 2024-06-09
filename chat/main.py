import chainlit as cl
import requests
import json
import base64
import os
from pathlib import Path
from langchain.schema.messages import AIMessage, HumanMessage

BASE_DIR = Path(__file__).resolve().parent.parent
URL = "http://localhost:8000/recipe"
IMAGES_PATH = os.path.join(BASE_DIR, "chat/images")


def call_langchain(question: str, images: list, session: str):
    """
    Sends a POST request to the specified URL with the question, images, and session data.
    
    Args:
        question (str): The question to send to the language model.
        images (list): A list of base64 encoded images.
        session (str): The session ID.
    
    Returns:
        response (requests.Response): The response from the server.
    """
    data = {"question": question, "images": images, "session": session}
    response = requests.post(url=URL, data=json.dumps(data))
    return response


def encode_image(image_path):
    """
    Encodes an image file to a base64 string.
    
    Args:
        image_path (str): The file path to the image.
    
    Returns:
        str: The base64 encoded string of the image.
    """
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')


def save_and_prepare_images(images):
    """
    Decodes base64 encoded images, saves them to disk, and prepares them for display.

    Args:
        images (list): List of base64 encoded images.

    Returns:
        list: A list of chainlit Image objects for display.
    """
    front_images = []
    for idx, value in enumerate(images):
        extension = value.split(";base64")[0].split("/")[1]
        extensionpssible = value.split(";base64,")[1]
        decoded_bytes = base64.b64decode(extensionpssible)
        image_path = os.path.join(IMAGES_PATH, f"{idx}.{extension}")
        with open(image_path, "wb") as image_file:
            image_file.write(decoded_bytes)
        front_images.append(cl.Image(path=image_path, name=f"{idx}.{extension}", display="inline", size="small"))
    return front_images


@cl.on_message
async def on_message(msg: cl.Message):
    """
    Handles incoming messages, processes images, and sends a response.
    
    Args:
        msg (cl.Message): The incoming message object.
    """
    encoded_images = [encode_image(file.path) for file in msg.elements if "image" in file.mime]
    session = cl.user_session.get("id")
    response = call_langchain(msg.content, encoded_images, session)
    
    if response.status_code == 200:
        data = response.json().get("response")
        images = data.get("context").get("images", [])
        front_images = save_and_prepare_images(images)
        
        await cl.Message(
            content=data.get("response"),
            elements=front_images
        ).send()
