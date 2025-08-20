"""
Minimal Native Chromium Server - Testing Version
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from native_chromium_engine import initialize_native_chromium_engine, get_native_chromium_engine
from native_chromium_endpoints import setup_native_chromium_endpoints
from native_endpoints import add_native_endpoints
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

load_dotenv()

logger = logging.getLogger(__name__)

# Database connection
MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client.aether_browser

# Global native engine
native_chromium_engine_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan handler for startup/shutdown"""
    global native_chromium_engine_instance
    
    # Startup
    try:
        logger.info("🔥 Initializing Native Chromium Engine...")
        native_chromium_engine_instance = await initialize_native_chromium_engine(client)
        
        if native_chromium_engine_instance:
            logger.info("✅ Native Chromium Engine initialized successfully")
            setup_native_chromium_endpoints(app)
            logger.info("✅ Native API endpoints configured")
        else:
            logger.error("❌ Native Chromium Engine initialization failed")
            
    except Exception as e:
        logger.error(f"Startup error: {e}")
    
    yield
    
    # Shutdown
    if native_chromium_engine_instance:
        await native_chromium_engine_instance.cleanup()
        logger.info("🧹 Native Chromium Engine cleaned up")

# Create FastAPI app with lifespan
app = FastAPI(
    title="AETHER Native Browser API", 
    version="6.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Add native endpoints
add_native_endpoints(app)

@app.get("/api/health")
async def health_check():
    """Enhanced health check including native engine status"""
    try:
        # Test database connection
        try:
            db.command("ping")
            db_status = "operational"
        except:
            db_status = "error"
        
        # Check native engine status
        native_status = {
            "available": native_chromium_engine_instance is not None,
            "initialized": native_chromium_engine_instance.is_initialized if native_chromium_engine_instance else False,
            "engine_type": "native_chromium"
        }
        
        return {
            "status": "operational",
            "version": "6.0.0",
            "native_chromium": native_status,
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "AETHER Native Chromium Integration Active"
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)