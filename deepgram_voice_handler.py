import asyncio
import websockets
import json
import base64
import logging
from deepgram import DeepgramClient
from voice_agent.functions import book_appointment, get_availability, cancel_appointment, trigger_crm_webhook
from models import db, Call, Transcript
from config import Config
import uuid

logger = logging.getLogger(__name__)

class DeepgramVoiceAgent:
    def __init__(self, call_sid):
        self.call_sid = call_sid
        self.deepgram_client = DeepgramClient(Config.DEEPGRAM_API_KEY)
        self.voice_agent = None
        self.connected = False
        
    async def initialize_voice_agent(self):
        """Initialize Deepgram Voice Agent with aura-2-amalthea-en voice"""
        try:
            # Configure Voice Agent
            agent_config = {
                "type": "voice_agent",
                "agent": {
                    "think": {
                        "provider": {
                            "type": "open_ai_llm",
                            "model": "gpt-4",
                            "system_prompt": """You are a professional AI receptionist for a business. You are friendly, efficient, and helpful. 

You can help with:
- Booking appointments
- Checking availability 
- Answering questions about services
- Taking messages

When booking appointments, always confirm the details with the caller before finalizing. 
Be conversational and natural, but stay focused on helping the caller efficiently.

Available functions:
- book_appointment: To book new appointments
- get_availability: To check available time slots
- cancel_appointment: To cancel existing appointments
- trigger_crm_webhook: To send data to CRM system"""
                        }
                    },
                    "speak": {
                        "provider": {
                            "type": "deepgram",
                            "voice": "aura-2-amalthea-en"
                        }
                    },
                    "listen": {
                        "provider": {
                            "type": "deepgram",
                            "model": "nova-2",
                            "language": "en-US"
                        }
                    }
                },
                "functions": [
                    {
                        "name": "book_appointment",
                        "description": "Book an appointment for a customer",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "customer_name": {"type": "string", "description": "Full name of the customer"},
                                "customer_phone": {"type": "string", "description": "Customer's phone number"},
                                "appointment_date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                                "appointment_time": {"type": "string", "description": "Time in HH:MM format"},
                                "service_type": {"type": "string", "description": "Type of service requested"}
                            },
                            "required": ["customer_name", "customer_phone", "appointment_date", "appointment_time"]
                        }
                    },
                    {
                        "name": "get_availability",
                        "description": "Check available appointment slots",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string", "description": "Date to check in YYYY-MM-DD format"}
                            },
                            "required": ["date"]
                        }
                    },
                    {
                        "name": "cancel_appointment",
                        "description": "Cancel an existing appointment",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "reference_id": {"type": "string", "description": "Appointment reference ID"}
                            },
                            "required": ["reference_id"]
                        }
                    }
                ]
            }
            
            # Initialize Voice Agent
            self.voice_agent = await self.deepgram_client.voice_agents.create(agent_config)
            self.connected = True
            logger.info(f"Deepgram Voice Agent initialized for call {self.call_sid}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Deepgram Voice Agent: {e}")
            return False
    
    async def process_audio(self, audio_data):
        """Send audio to Voice Agent"""
        if self.voice_agent and self.connected:
            try:
                await self.voice_agent.send_audio(audio_data)
            except Exception as e:
                logger.error(f"Error sending audio to Voice Agent: {e}")
    
    async def handle_function_call(self, function_name, parameters):
        """Handle function calls from Voice Agent"""
        try:
            if function_name == "book_appointment":
                result = book_appointment(
                    customer_name=parameters.get('customer_name'),
                    customer_phone=parameters.get('customer_phone'),
                    appointment_date=parameters.get('appointment_date'),
                    appointment_time=parameters.get('appointment_time'),
                    service_type=parameters.get('service_type'),
                    call_id=self.call_sid
                )
            elif function_name == "get_availability":
                result = get_availability(
                    date=parameters.get('date'),
                    call_id=self.call_sid
                )
            elif function_name == "cancel_appointment":
                result = cancel_appointment(
                    reference_id=parameters.get('reference_id'),
                    call_id=self.call_sid
                )
            else:
                result = {"success": False, "message": "Unknown function"}
            
            # Send result back to Voice Agent
            if self.voice_agent:
                await self.voice_agent.send_function_result(function_name, result)
                
        except Exception as e:
            logger.error(f"Error handling function call {function_name}: {e}")
    
    async def close(self):
        """Close Voice Agent connection"""
        if self.voice_agent:
            try:
                await self.voice_agent.close()
                self.connected = False
            except Exception as e:
                logger.error(f"Error closing Voice Agent: {e}")

# WebSocket handler for Deepgram Voice Agent
async def handle_deepgram_voice_websocket(websocket, path):
    """Handle WebSocket connection for Deepgram Voice Agent"""
    call_sid = None
    voice_agent = None
    
    try:
        # Extract call_sid from path
        if 'call_sid=' in path:
            call_sid = path.split('call_sid=')[1].split('&')[0]
        
        if not call_sid:
            logger.error("No call_sid provided in WebSocket connection")
            await websocket.close()
            return
        
        logger.info(f"Deepgram Voice Agent WebSocket connected for call {call_sid}")
        
        # Initialize Voice Agent
        voice_agent = DeepgramVoiceAgent(call_sid)
        success = await voice_agent.initialize_voice_agent()
        
        if not success:
            logger.error(f"Failed to initialize Voice Agent for call {call_sid}")
            await websocket.close()
            return
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                event = data.get('event')
                
                if event == 'connected':
                    logger.info(f"Twilio connected to Deepgram Voice Agent for call {call_sid}")
                    await websocket.send(json.dumps({"event": "connected"}))
                    
                elif event == 'start':
                    logger.info(f"Media stream started for call {call_sid}")
                    # Voice Agent will start speaking automatically
                    
                elif event == 'media':
                    # Forward audio to Voice Agent
                    payload = data.get('media', {}).get('payload')
                    if payload:
                        audio_data = base64.b64decode(payload)
                        await voice_agent.process_audio(audio_data)
                        
                elif event == 'stop':
                    logger.info(f"Media stream stopped for call {call_sid}")
                    break
                    
            except json.JSONDecodeError:
                logger.error("Invalid JSON received from Twilio")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"WebSocket connection closed for call {call_sid}")
    except Exception as e:
        logger.error(f"WebSocket error for call {call_sid}: {e}")
    finally:
        if voice_agent:
            await voice_agent.close()

# Start WebSocket server for Deepgram Voice Agent
async def start_deepgram_voice_server():
    """Start WebSocket server for Deepgram Voice Agent"""
    server = await websockets.serve(
        handle_deepgram_voice_websocket, 
        "0.0.0.0", 
        8766  # Different port from the other WebSocket server
    )
    logger.info("Deepgram Voice Agent WebSocket server started on port 8766")
    await server.wait_closed()

if __name__ == "__main__":
    # Run the server
    asyncio.run(start_deepgram_voice_server())