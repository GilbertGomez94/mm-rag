from fastapi import FastAPI, Request
from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableParallel
from langchain.chat_models import ChatOllama

from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
from server.thrid_case import img_prompt_func
from server.final_case import get_documents, retriever

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
    data = await request.json()
    question = data.get("question")
    model = ChatOllama(temperature=0, model="llava", max_tokens=1024)
    
    # RAG pipeline
    chain = (
        {
            "context": retriever | RunnableLambda(get_documents),
            "question": RunnablePassthrough(),
        }
        | RunnableParallel({"response":img_prompt_func| model| StrOutputParser(),
                      "context": itemgetter("context"),})
    )
    result = chain.invoke(question)
    
    return JSONResponse({"response": result})
