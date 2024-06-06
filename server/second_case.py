from langchain.schema.messages import HumanMessage

import os

from langchain_community.vectorstores import Chroma
from langchain_experimental.open_clip import OpenCLIPEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_experimental.open_clip import OpenCLIPEmbeddings


vectorstore = Chroma(
    collection_name="mm_rag_cookbook",
    embedding_function=OpenCLIPEmbeddings(),
    persist_directory=os.path.join("/home/gilbert/Documentos/experiments/mm-rag/", ".chroma_db")
)

retriever = vectorstore.as_retriever(search_kwargs={"k":20})


def prompt_func(data_dict):
    # Joining the context texts into a single string
    formatted_texts = "\n".join(data_dict["context"]["texts"])
    messages = []

    # Adding image(s) to the messages if present
    if data_dict["context"]["images"]:
        image_message = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{data_dict['context']['images'][0]}"
            },
        }
        messages.append(image_message)

    # Adding the text message for analysis
    text_message = {
        "type": "text",
        "text": (
            "Eres un experto en cocina de invierno, tu tarea es analizar e interpretar imagenes "
            "Además de las imágenes recibirás texto como contexto. Ambos serán retornados desde una base de datos vectorial "
            "basada en el input del usuario. Por favor usa tu extenso conocimiento y habilidades analiticas para prover "
            "una respuesta precisa que contenga lo siguiente:\n"
            "- Una descripción detallada de los elementos en las imágenes que recibas.\n"
            "- La o las imágenes que hayan sido retornadas que se encontrarán en los mensajes de tipo 'image_url'.\n"
            "- En qué consiste la o las recetas.\n\n"
            f"input del usuario: {data_dict['question']}\n\n"
            "Texto y / o tablas:\n"
            f"{formatted_texts}"
        ),
    }
    messages.append(text_message)
    content = [HumanMessage(content=messages)]
    return content

from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List


class MyModel(BaseModel):
    response: str = Field(description="The response from the model")
    images: List[str] = Field(description="The images from the model")
