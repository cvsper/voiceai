#!/usr/bin/env python3
"""
Test script to verify Deepgram Voice Agent V1 API connectivity
"""
import asyncio
import websockets
import json
import logging
import ssl
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_deepgram_v1():
    """Test connection to Deepgram Voice Agent V1"""
    try:
        logger.info("🧪 Testing Deepgram Voice Agent V1 connection...")
        
        # Connect to Voice Agent V1 endpoint
        agent_url = "wss://agent.deepgram.com/v1/agent/converse"
        headers = {
            "Authorization": f"token {Config.DEEPGRAM_API_KEY}"
        }
        
        logger.info(f"🔗 Connecting to: {agent_url}")
        logger.info(f"🔑 API Key: {Config.DEEPGRAM_API_KEY[:10]}...")
        
        # Create SSL context that doesn't verify certificates (for development)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Try to connect
        connection = await websockets.connect(agent_url, extra_headers=headers, ssl=ssl_context)
        logger.info("✅ Successfully connected to Voice Agent V1!")
        
        # Send configuration - simplified version
        config_message = {
            "type": "Settings",
            "audio": {
                "input": {
                    "encoding": "linear16",
                    "sample_rate": 16000
                },
                "output": {
                    "encoding": "linear16",
                    "sample_rate": 24000
                }
            },
            "agent": {
                "listen": {
                    "provider": {
                        "type": "deepgram",
                        "model": "nova-3"
                    }
                },
                "think": {
                    "provider": {
                        "type": "open_ai",
                        "model": "gpt-4o-mini"
                    },
                    "prompt": "You are a helpful AI assistant."
                },
                "speak": {
                    "provider": {
                        "type": "deepgram",
                        "model": "aura-2-andromeda-en"
                    }
                }
            }
        }
        
        logger.info("📤 Sending configuration...")
        await connection.send(json.dumps(config_message))
        logger.info("✅ Configuration sent successfully!")
        
        # Listen for responses for 10 seconds
        logger.info("👂 Listening for responses...")
        try:
            async with asyncio.timeout(10):
                async for message in connection:
                    data = json.loads(message)
                    msg_type = data.get('type')
                    logger.info(f"📨 Received: {msg_type}")
                    
                    if msg_type == "AgentAudio":
                        logger.info("🎵 Received audio from aura-2-amalthea-en!")
                        break
                    elif msg_type == "Error":
                        logger.error(f"❌ Error: {data.get('description', 'Unknown error')}")
                        break
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout waiting for audio response")
        
        await connection.close()
        logger.info("🧹 Connection closed")
        
    except Exception as e:
        logger.error(f"💥 Test failed: {e}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_deepgram_v1())