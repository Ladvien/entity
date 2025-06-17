from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from entity.entity_agenty import EntityAgent
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Simple Agentic System")
entity_agent = EntityAgent()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await entity_agent.process(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "Simple Agentic System"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
