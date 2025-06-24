import asyncio
import base64
import json
import logging
import os
from flask import current_app
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    AgentWebSocketEvents,
    AgentKeepAlive,
)
from deepgram.clients.agent.v1.websocket.options import SettingsOptions

logger = logging.getLogger(__name__)

class DeepgramVoiceAgent:
    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY environment variable not set")

        config = DeepgramClientOptions(options={"keepalive": "true"})
        self.deepgram = DeepgramClient(self.api_key, config)
        self.dg_connection = None
        self.twilio_ws = None

    async def handle_twilio_stream(self, twilio_websocket):
        """Handle the bidirectional stream between Twilio and Deepgram."""
        self.twilio_ws = twilio_websocket
        try:
            self.dg_connection = self.deepgram.agent.websocket.v("1")

            # Set up event listeners
            self.dg_connection.on(AgentWebSocketEvents.Welcome, self.on_welcome)
            self.dg_connection.on(AgentWebSocketEvents.AgentAudioDone, self.on_agent_audio_done)
            self.dg_connection.on(AgentWebSocketEvents.ConversationText, self.on_conversation_text)
            self.dg_connection.on(AgentWebSocketEvents.Error, self.on_error)

            # Configure the agent
            options = SettingsOptions(
                agent=dict(
                    listen=dict(provider=dict(type="deepgram", model="nova-2")),
                    think=dict(
                        provider=dict(type="open_ai", model="gpt-4o-mini"),
                        prompt="You are a friendly and helpful AI assistant named Thalia. Your goal is to assist callers with their needs efficiently and courteously.",
                    ),
                    speak=dict(provider=dict(type="deepgram", model="aura-2-thalia-en")),
                    greeting="Hello! Thank you for calling. My name is Thalia, how can I help you today?",
                ),
                audio=dict(
                    input=dict(encoding="mulaw", sample_rate=8000),
                    output=dict(encoding="mulaw", sample_rate=8000, container="wav"),
                ),
            )

            if not self.dg_connection.start(options):
                logger.error("Failed to start Deepgram connection")
                return

            # Process incoming Twilio messages
            async for message in self.twilio_ws:
                await self.process_twilio_message(message)

        except Exception as e:
            logger.error(f"Error in Deepgram Voice Agent handler: {e}", exc_info=True)
        finally:
            if self.dg_connection:
                self.dg_connection.finish()
            logger.info("Deepgram connection closed.")

    async def process_twilio_message(self, message):
        """Process a single message from the Twilio WebSocket."""
        try:
            data = json.loads(message)
            event = data.get("event")

            if event == "connected":
                logger.info(f"Twilio connected: {data}")
            elif event == "start":
                logger.info(f"Twilio media stream started: {data}")
            elif event == "media":
                # Forward audio from Twilio to Deepgram
                payload = data["media"]["payload"]
                audio_data = base64.b64decode(payload)
                self.dg_connection.send(audio_data)
            elif event == "stop":
                logger.info(f"Twilio media stream stopped: {data}")
                self.dg_connection.finish()

        except Exception as e:
            logger.error(f"Error processing Twilio message: {e}", exc_info=True)

    # Deepgram Event Handlers
    async def on_welcome(self, data, **kwargs):
        logger.info(f"Deepgram Agent Welcome: {data}")

    async def on_agent_audio_done(self, data, **kwargs):
        logger.info(f"Deepgram Agent finished speaking: {data}")

    async def on_conversation_text(self, data, **kwargs):
        # Forward agent's speech back to Twilio
        audio_data = data.get("audio")
        if audio_data:
            # Twilio expects mulaw audio to be base64 encoded
            encoded_audio = base64.b64encode(audio_data).decode('utf-8')

            twilio_message = {
                "event": "media",
                "media": {
                    "payload": encoded_audio
                }
            }
            # The streamSid is not strictly needed for outbound media
            # but can be helpful for logging. We'll omit it for simplicity.
            await self.twilio_ws.send(json.dumps(twilio_message))

    async def on_error(self, data, **kwargs):
        logger.error(f"Deepgram Agent Error: {data}")