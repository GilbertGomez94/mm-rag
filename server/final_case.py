import base64
import binascii
from langchain_experimental.open_clip import OpenCLIPEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOllama

from langchain.schema.messages import HumanMessage

import os

from langchain_google_genai import ChatGoogleGenerativeAI


#TODO: Make this a command on init project using pwd or something else....
SAVE_PATH=os.getenv("PROJECT_PATH", "/home/gilbert/Documentos/experiments/mm-rag/")


embeddings = OpenCLIPEmbeddings()
vectorstore = FAISS.load_local(os.path.join(SAVE_PATH, "vectordb/faiss_index"), embeddings,allow_dangerous_deserialization=True)

retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

def get_documents(docs):
    """Get documents from vectordb retriever"""
    images = []
    image_summaries = []
    texts = []
    for d in docs:
        if d.metadata['type'] == 'text' or d.metadata['type'] == 'table':
            texts.append(d.metadata['original_content'])
        elif d.metadata['type'] == 'image':
            # print(d.metadata.get("original_content"))
            image_summaries.append(d.page_content)
            images.append(f"data:image/jpeg;base64,{d.metadata['original_content']}")
    return {"images": images, "texts": texts, "image_summaries": image_summaries}


def add_ingredients(ingredients: str, question: str) -> str:
    """Create formated string with ingredients and user initial question"""
    return f"Usando los siguientes ingredientes {ingredients}. {question}"


def img_prompt_func(data_dict: dict):
    """
    Join the context into a single string
    """
    formatted_texts = "\n".join(data_dict["context"]["texts"])
    messages = []

    # Adding image(s) to the messages if present
    if data_dict["context"]["images"]:
        for image in data_dict["context"]["images"]:
            image_message = {
                "type": "image_url",
                "image_url": {"url": image},
            }
            messages.append(image_message)
    final_question = ""
    if data_dict.get("ingredients"):
        add_ingredients(data_dict["ingredients"]["images"], data_dict["question"])
    else:
        final_question = data_dict["question"]
    text_message = {
        "type": "text",
        "text": (
            "Eres un experto en cocina de invierno, tu tarea es analizar e interpretar imagenes PERO NUNCA vas a dar respuestas haciendo referencia a una imagen, solo la información util "
            "Además de las imágenes recibirás texto como contexto. Ambos serán retornados desde una base de datos vectorial "
            "basada en el input del usuario. Por favor usa tu extenso conocimiento y habilidades analiticas para prover "
            "una respuesta precisa que contenga lo siguiente:\n"
            "- En qué consiste la o las recetas.\n\n"
            f"input del usuario: {final_question}\n\n"
            "Texto y / o tablas:\n"
            f"{formatted_texts}"
        ),
    }
    messages.append(text_message)
    return [HumanMessage(content=messages)]


def is_valid_base64(b64_string: str) -> bool:
    """Check if a string is a valid base64 encoded string."""
    try:
        base64.b64decode(b64_string, validate=True)
        return True
    except binascii.Error:
        return False



def input_image_prompt(images: list):
    """
    Join the context into a single string
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro-vision", temperature=0, max_tokens=1024)
    # model = ChatOllama(temperature=0, model="llava", max_tokens=1024)

    response = ""
    for image in images:
        if not is_valid_base64(image):
            print(f"Invalid base64 string: {image}")
            continue
        padded_image = image + '=' * (-len(image) % 4)
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": """Eres un asistente encargado de decir nombres de ingredientes en imágenes.
                
                    Debes indicar explícitamente que ingrediente o ingredientes hay en la imagen. En caso de no detectar algún ingrediente debes responder lo siguiente:
                    'NEGATIVO'""",
                },  # You can optionally provide text parts
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{padded_image}"},
            ]
        )
        
        model_response = model.invoke([message])
        response += f",{model_response.content}"
    return response


def image_chain(images: list):
    return {"images": input_image_prompt(images) if images else None}
    