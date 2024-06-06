from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OllamaEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema.messages import HumanMessage, SystemMessage
from langchain.schema.document import Document
from langchain.vectorstores import FAISS
from langchain.retrievers.multi_vector import MultiVectorRetriever
import os
import uuid
import base64
from fastapi import FastAPI, Request, Form, Response, File, UploadFile
from langserve import APIHandler, add_routes

from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
import json
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

openai_api_key = os.getenv("OPENAI_API_KEY")
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

db = FAISS.load_local("faiss_index", embeddings,allow_dangerous_deserialization=True)

prompt_template = """Eres chef y experto en recetas de invierno.
Responda la pregunta basándose únicamente en el siguiente contexto, que puede incluir texto, imágenes y tablas:
{context}
Pregunta: {question}
No responda si no está seguro y rechace responder y diga "Lo siento, no tengo mucha información al respecto".
Simplemente devuelva la respuesta útil con el mayor detalle posible.
Respuesta:
"""

qa_chain = LLMChain(llm=ChatOpenAI(model="gpt-4", openai_api_key = openai_api_key, max_tokens=1024),
                    prompt=PromptTemplate.from_template(prompt_template))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/recipe")
async def get_answer(question: str = Form(...)):
    relevant_docs = db.similarity_search(question, k=7)
    print(relevant_docs)
    context = ""
    relevant_images = []
    for d in relevant_docs:
        if d.metadata['type'] == 'text':
            context += '[text]' + d.metadata['original_content']
        elif d.metadata['type'] == 'table':
            context += '[table]' + d.metadata['original_content']
        elif d.metadata['type'] == 'image':
            print("hubo una imagen")
            context += '[image]' + d.page_content
            relevant_images.append(d.metadata['original_content'])
    result = qa_chain.run({'context': context, 'question': question})
    return JSONResponse({"relevant_images": relevant_images if relevant_images else None, "result": result})


@app.post("/recipe-body")
async def get_answer(request: Request):
    data = await request.json()
    question = data.get("question")
    relevant_docs = db.similarity_search(question, k=7)
    print(relevant_docs)
    context = ""
    relevant_images = []
    for d in relevant_docs:
        if d.metadata['type'] == 'text':
            context += '[text]' + d.metadata['original_content']
        elif d.metadata['type'] == 'table':
            context += '[table]' + d.metadata['original_content']
        elif d.metadata['type'] == 'image':
            print("hubo una imagen")
            context += '[image]' + d.page_content
            relevant_images.append(d.metadata['original_content'])
    result = qa_chain.run({'context': context, 'question': question})
    return JSONResponse({"relevant_images": relevant_images if relevant_images else None, "result": result})