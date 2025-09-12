from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from app.routers import generate

app = FastAPI(title="SMB Marketing Agent")
app.include_router(generate.router, prefix="/generate", tags=["generate"])

@app.get("/health")
def health():
    return {"status": "ok"}
