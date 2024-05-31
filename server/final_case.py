from langchain_experimental.open_clip import OpenCLIPEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema.messages import HumanMessage

import os

SAVE_PATH=os.getenv("PROJECT_PATH")


embeddings = OpenCLIPEmbeddings()
vectorstore = FAISS.load_local(os.path.join(SAVE_PATH, "vectordb/faiss_index"), embeddings,allow_dangerous_deserialization=True)

retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

def get_documents(docs):
    images = []
    image_summaries = []
    texts = []
    for d in docs:
        if d.metadata['type'] == 'text' or d.metadata['type'] == 'table':
            texts.append(d.metadata['original_content'])
        elif d.metadata['type'] == 'image':
            print(d.metadata.get("original_content"))
            image_summaries.append(d.page_content)
            images.append(f"data:image/jpeg;base64,{d.metadata['original_content']}")
    return {"images": images, "texts": texts, "image_summaries": image_summaries}


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
