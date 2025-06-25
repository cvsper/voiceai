web: gunicorn app:app
worker: python -c "import asyncio; from voice_agent.websocket_handler import start_websocket_server; start_websocket_server()"