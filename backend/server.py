#!/usr/bin/env python3
"""
Minimal Test Server - No middleware
"""

from fastapi import FastAPI
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AETHER Test API", version="1.0.0")

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "minimal test server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)