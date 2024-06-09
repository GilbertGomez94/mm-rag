import base64
import binascii
import os
from pathlib import Path

from langchain_experimental.open_clip import OpenCLIPEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema.messages import HumanMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Constants
SAVE_PATH = Path(__file__).resolve().parent.parent

# Initialize embeddings and vector store
embeddings = OpenCLIPEmbeddings()
vectorstore = FAISS.load_local(
    os.path.join(SAVE_PATH, "vectordb/faiss_index"), 
    embeddings,
    allow_dangerous_deserialization=True
)
retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 10})

# Prompt template
template = """Eres un experto en recetas de invierno. Tu tarea es proporcionar una receta detallada basada en el siguiente contexto y la información proporcionada. Responde 'Lo siento, solo puedo responder preguntas asociadas a las recetas de invierno.' si te hacen una pregunta que no está relacionada con recetas de cocina.

Se te proporcionará un ingrediente y una imagen relacionada. Debes combinar esta información para ofrecer una receta que incluya el ingrediente mencionado. Utiliza tu extenso conocimiento y habilidades analíticas para proporcionar una respuesta precisa que contenga lo siguiente:
- Descripción detallada de la receta.
- Ingredientes necesarios.
- Instrucciones paso a paso.

Contexto:
{context}
{chat_history}

Humano: {final_question}
AI:"""

PROMPT = PromptTemplate(
    input_variables=["context", "chat_history", "final_question"], 
    template=template
)


def get_documents(docs):
    """
    Extract documents from the vector database retriever.
    
    Args:
        docs (list): List of documents retrieved from the vector store.

    Returns:
        dict: Dictionary containing lists of images, texts, and image summaries.
    """
    images = []
    image_summaries = []
    texts = []
    for d in docs:
        if d.metadata['type'] == 'text' or d.metadata['type'] == 'table':
            texts.append(d.metadata['original_content'])
        elif d.metadata['type'] == 'image':
            image_summaries.append(d.page_content)
            images.append(f"data:image/jpeg;base64,{d.metadata['original_content']}")
    return {"images": images, "texts": texts, "image_summaries": image_summaries}


def add_ingredients(ingredients: str, question: str) -> str:
    """
    Create a formatted string with ingredients and the user's initial question.
    
    Args:
        ingredients (str): Ingredients to include in the response.
        question (str): User's initial question.
    
    Returns:
        str: Formatted string combining ingredients and question.
    """
    return f"Usando los siguientes ingredientes {ingredients}. {question}"


def prepare_prompt_data(data_dict: dict):
    """
    Prepare data for the prompt by joining context into a single string.
    
    Args:
        data_dict (dict): Dictionary containing context, chat history, and question.

    Returns:
        dict: Dictionary formatted for the prompt with context, chat history, and final question.
    """
    formatted_texts = "\n".join(data_dict["context"]["texts"])
    context = f"{formatted_texts}\n{data_dict['context']['image_summaries']}"
    memory: ConversationBufferWindowMemory = data_dict.get("chat_history")
    final_question = ""
    if data_dict.get("ingredients"):
        final_question = add_ingredients(data_dict["ingredients"]["images"], data_dict["question"])
    else:
        final_question = data_dict["question"]
    return {"context": context, "chat_history": memory.buffer_as_str, "final_question": final_question}

def is_valid_base64(b64_string: str) -> bool:
    """
    Check if a string is a valid base64 encoded string.
    
    Args:
        b64_string (str): Base64 encoded string to validate.

    Returns:
        bool: True if the string is valid base64, False otherwise.
    """
    try:
        base64.b64decode(b64_string, validate=True)
        return True
    except binascii.Error:
        return False


def input_image_prompt(images: list):
    """
    Generate a prompt for each image and get the model's response.
    
    Args:
        images (list): List of base64 encoded images.

    Returns:
        str: Combined response from the model for all images.
    """
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, max_tokens=1024)
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
                    
                    Debes indicar explícitamente qué ingrediente o ingredientes hay en la imagen. En caso de no detectar algún ingrediente debes responder lo siguiente:
                    'NEGATIVO'""",
                },
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{padded_image}"},
            ]
        )
        model_response = model.invoke([message])
        response += f",{model_response.content}"
    return response


def image_chain(images: list):
    """
    Process a list of images and return their ingredients.
    
    Args:
        images (list): List of base64 encoded images.

    Returns:
        dict: Dictionary containing the images and their corresponding ingredients.
    """
    return {"images": input_image_prompt(images) if images else None}
