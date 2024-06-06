import io
import re
import os
import base64

from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.schema.document import Document
from langchain.schema.messages import HumanMessage
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.storage import InMemoryStore



from PIL import Image

vectorstore = Chroma(
    collection_name="mm_rag_cookbok_three", embedding_function=OpenAIEmbeddings(api_key="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"),
    persist_directory=os.path.join("/home/gilbert/Documentos/experiments/mm-rag/", ".chroma_db_three")
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 10})


def looks_like_base64(sb):
    """Check if the string looks like base64"""
    return re.match("^[A-Za-z0-9+/]+[=]{0,2}$", sb) is not None


def is_image_data(b64data):
    """
    Check if the base64 data is an image by looking at the start of the data
    """
    image_signatures = {
        b"\xff\xd8\xff": "jpg",
        b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a": "png",
        b"\x47\x49\x46\x38": "gif",
        b"\x52\x49\x46\x46": "webp",
    }
    try:
        header = base64.b64decode(b64data)[:8]  # Decode and get the first 8 bytes
        for sig, format in image_signatures.items():
            if header.startswith(sig):
                return True
        return False
    except Exception:
        return False


def resize_base64_image(base64_string, size=(128, 128)):
    """
    Resize an image encoded as a Base64 string
    """
    # Decode the Base64 string
    img_data = base64.b64decode(base64_string)
    img = Image.open(io.BytesIO(img_data))

    # Resize the image
    resized_img = img.resize(size, Image.LANCZOS)

    # Save the resized image to a bytes buffer
    buffered = io.BytesIO()
    resized_img.save(buffered, format=img.format)

    # Encode the resized image to Base64
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def split_image_text_types(docs):
    """
    Split base64-encoded images and texts
    """
    b64_images = []
    texts = []
    for doc in docs:
        # Check if the document is of type Document and extract page_content if so
        if isinstance(doc, Document):
            doc = doc.page_content
        if looks_like_base64(doc) and is_image_data(doc):
            print("una imagen")
            doc = resize_base64_image(doc, size=(1300, 600))
            b64_images.append(doc)
        else:
            texts.append(doc)
    return {"images": b64_images, "texts": texts}


def img_prompt_func(data_dict):
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

    # Adding the text for analysis
    text_message = {
        "type": "text",
        "text": (
            "Eres un experto en cocina de invierno, tu tarea es analizar e interpretar imagenes PERO NUNCA vas a dar respuestas haciendo referencia a una imagen, solo la información util "
            "Además de las imágenes recibirás texto como contexto. Ambos serán retornados desde una base de datos vectorial "
            "basada en el input del usuario. Por favor usa tu extenso conocimiento y habilidades analiticas para prover "
            "una respuesta precisa que contenga lo siguiente:\n"
            "- Una descripción detallada de los elementos en las imágenes que recibas.\n"
            "- En qué consiste la o las recetas.\n\n"
            f"input del usuario: {data_dict['question']}\n\n"
            "Texto y / o tablas:\n"
            f"{formatted_texts}"
        ),
    }
    messages.append(text_message)
    return [HumanMessage(content=messages)]


def retrieve_images(docs):
    print(docs)

    b64_images = []
    for doc in docs:
        if isinstance(doc, Document):
            doc = doc.page_content
        # Check if the document is of type Document and extract page_content if so
        if looks_like_base64(doc) and is_image_data(doc):
            print("una imagen")
            doc = resize_base64_image(doc, size=(1300, 600))
            b64_images.append(f"data:image/jpeg;base64,{doc}")
    return b64_images
