#!/usr/bin/env python3
"""
Simple test for Native Chromium Engine
"""
import asyncio
import logging
from pymongo import MongoClient
from native_chromium_engine import initialize_native_chromium_engine
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_native_chromium():
    """Test Native Chromium Engine initialization"""
    try:
        # Database connection
        MONGO_URL = os.getenv("MONGO_URL")
        client = MongoClient(MONGO_URL)
        logger.info("✅ MongoDB connected")
        
        # Test native chromium engine
        logger.info("🔥 Testing Native Chromium Engine initialization...")
        native_engine = await initialize_native_chromium_engine(client)
        
        if native_engine:
            logger.info("✅ Native Chromium Engine initialized successfully")
            logger.info(f"   - Initialized: {native_engine.is_initialized}")
            logger.info(f"   - Active sessions: {len(native_engine.active_sessions)}")
            logger.info("🚀 NATIVE CHROMIUM INTEGRATION TEST PASSED!")
            
            # Clean up
            await native_engine.cleanup()
            logger.info("🧹 Cleanup completed")
            return True
        else:
            logger.error("❌ Native Chromium Engine initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_native_chromium())
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Native Chromium Integration Test")