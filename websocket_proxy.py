"""
WebSocket proxy to bridge Twilio connections to our Voice Agent V1 server
"""
import asyncio
import websockets
import json
import logging
from flask import Flask, request, Response
import threading

logger = logging.getLogger(__name__)

class WebSocketProxy:
    def __init__(self):
        self.active_connections = {}
    
    async def proxy_connection(self, client_websocket, path):
        """Proxy WebSocket connection from client to Voice Agent V1 server"""
        voice_agent_websocket = None
        
        try:
            logger.info(f"🔌 New proxy connection: {path}")
            
            # Connect to local Voice Agent V1 server
            voice_agent_url = f"ws://localhost:8767{path}"
            logger.info(f"🔗 Connecting to Voice Agent V1: {voice_agent_url}")
            
            voice_agent_websocket = await websockets.connect(voice_agent_url)
            logger.info(f"✅ Connected to Voice Agent V1")
            
            # Start bidirectional forwarding
            client_to_agent = asyncio.create_task(
                self.forward_messages(client_websocket, voice_agent_websocket, "Client -> Agent")
            )
            agent_to_client = asyncio.create_task(
                self.forward_messages(voice_agent_websocket, client_websocket, "Agent -> Client")
            )
            
            # Wait for either connection to close
            done, pending = await asyncio.wait(
                [client_to_agent, agent_to_client],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                
        except Exception as e:
            logger.error(f"💥 Proxy error: {e}")
        finally:
            if voice_agent_websocket:
                await voice_agent_websocket.close()
            logger.info(f"🧹 Proxy connection closed")
    
    async def forward_messages(self, src_ws, dst_ws, direction):
        """Forward messages from source to destination WebSocket"""
        try:
            async for message in src_ws:
                logger.debug(f"📤 {direction}: {message[:100]}...")
                await dst_ws.send(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 {direction} connection closed")
        except Exception as e:
            logger.error(f"💥 {direction} forwarding error: {e}")

# Global proxy instance
websocket_proxy = WebSocketProxy()

async def start_websocket_proxy_server():
    """Start WebSocket proxy server on port 5002"""
    server = await websockets.serve(
        websocket_proxy.proxy_connection,
        "0.0.0.0", 
        5002
    )
    logger.info("WebSocket proxy server started on port 5002")
    await server.wait_closed()

def start_proxy_thread():
    """Start proxy server in separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_websocket_proxy_server())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_websocket_proxy_server())