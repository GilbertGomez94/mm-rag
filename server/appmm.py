from fastapi import FastAPI, Request
from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableParallel
from langchain.chat_models import ChatOllama

from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from server.final_case import get_documents, retriever, img_prompt_func, image_chain

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)



@app.post("/recipe")
async def get_answer(request: Request):
    """Request to get winter recepies from multimodal"""
    data = await request.json()
    question = data.get("question")
    images = data.get("images")

    # model = ChatOllama(temperature=0, model="llava", max_tokens=1024)
    model = ChatGoogleGenerativeAI(model="gemini-pro-vision", temperature=0, max_tokens=1024)
    
    # RAG pipeline

    chain = (
        {
            "context": RunnablePassthrough().pick("question")
            | retriever
            | RunnableLambda(get_documents),
            "question": RunnablePassthrough().pick("question"),
            "ingredients": RunnablePassthrough().pick("images")
            | RunnableLambda(image_chain)
        }
        | RunnableParallel({"response":img_prompt_func| model| StrOutputParser(),
                      "context": itemgetter("context"),})
    )
    result = chain.invoke({"question": question, "images": images})
    
    return JSONResponse({"response": result})
