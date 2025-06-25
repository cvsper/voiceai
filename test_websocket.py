#!/usr/bin/env python3
"""
Test WebSocket connectivity to our Voice Agent V1 server
"""
import asyncio
import websockets
import json
import logging
import ssl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """Test WebSocket connection to our V1 server"""
    try:
        # Test ngrok connection to WebSocket server
        ws_url = "wss://086d-2600-1006-a132-82c-4cec-6a7e-2690-b537.ngrok-free.app?call_sid=test123"
        
        logger.info(f"🧪 Testing WebSocket connection to: {ws_url}")
        
        # Create SSL context for ngrok
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Try to connect through ngrok
        websocket = await websockets.connect(ws_url, ssl=ssl_context)
        logger.info("✅ WebSocket connection successful!")
        
        # Send a test message (simulating Twilio)
        test_message = {
            "event": "connected",
            "protocol": "websocket",
            "version": "1.0"
        }
        
        logger.info("📤 Sending test message...")
        await websocket.send(json.dumps(test_message))
        
        # Wait for response
        logger.info("👂 Waiting for response...")
        try:
            async with asyncio.timeout(5):
                response = await websocket.recv()
                logger.info(f"📨 Received response: {response}")
        except asyncio.TimeoutError:
            logger.warning("⏰ No response received within 5 seconds")
        
        await websocket.close()
        logger.info("✅ WebSocket test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ WebSocket test failed: {e}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_websocket_connection())