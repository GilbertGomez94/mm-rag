from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableParallel
from langchain.memory import ConversationBufferWindowMemory
from langchain_google_genai import ChatGoogleGenerativeAI

from server.final_case import PROMPT, get_documents, retriever, prepare_prompt_data, image_chain


# Initialize FastAPI app
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
    """
    Endpoint to get winter recipes based on multimodal input.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        JSONResponse: The response containing the recipe or an error message.
    """
    data = await request.json()
    question = data.get("question")
    images = data.get("images")
    session = data.get("session")

    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, max_tokens=1024)
    conversational_memory = ConversationBufferWindowMemory(memory_key=session, k=3)

    # RAG pipeline
    chain = (
        {
            "context": RunnablePassthrough().pick("question")
                       | retriever
                       | RunnableLambda(get_documents),
            "question": RunnablePassthrough().pick("question"),
            "ingredients": RunnablePassthrough().pick("images")
                          | RunnableLambda(image_chain),
            "chat_history": RunnablePassthrough().pick("chat_history"),
        }
        | RunnableParallel({
            "response": prepare_prompt_data | PROMPT | model | StrOutputParser(),
            "context": itemgetter("context"),
        })
    )

    result = chain.invoke({"question": question, "images": images, "chat_history": conversational_memory})
    conversational_memory.save_context({"input": question}, {"output": result.get("response")})

    if "No tengo información" in result.get("response") or "Lo siento" in result.get("response"):
        del result["context"]["images"]

    return JSONResponse({"response": result})

