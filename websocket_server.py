import asyncio
import websockets
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
import jwt  # For token validation
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# In-memory storage for active WebSocket connections
active_connections = {}

# Helper function to validate JWT token
def validate_token(token):
    """
    Validate the JWT token and return the decoded payload if valid.
    """
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired.")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token.")
        return None

# Decorator to authenticate WebSocket connections
def authenticate_websocket(func):
    """
    Decorator to validate the JWT token before allowing WebSocket communication.
    """
    @wraps(func)
    async def wrapper(websocket, path):
        try:
            # Get the token from the WebSocket headers
            token = websocket.request_headers.get("Authorization")
            if not token:
                logger.warning("No token provided. Closing connection.")
                await websocket.close(code=4001, reason="Unauthorized: No token provided.")
                return

            # Validate the token
            payload = validate_token(token)
            if not payload:
                logger.warning("Invalid token. Closing connection.")
                await websocket.close(code=4001, reason="Unauthorized: Invalid token.")
                return

            # Attach user information to the WebSocket connection
            websocket.user_id = payload.get("user_id")
            websocket.username = payload.get("username")

            logger.info(f"User {websocket.username} connected with WebSocket.")
            await func(websocket, path)
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            await websocket.close(code=4001, reason="Internal server error.")

    return wrapper

# WebSocket connection handler
@authenticate_websocket
async def handle_connection(websocket, path):
    """
    Handle WebSocket connections and messages.
    """
    try:
        # Add the connection to the active connections list
        active_connections[websocket.user_id] = websocket
        logger.info(f"Active connections: {len(active_connections)}")

        async for message in websocket:
            logger.info(f"Received message from {websocket.username}: {message}")

            # Broadcast the message to all active connections
            await broadcast_message(websocket.user_id, message)
    except websockets.ConnectionClosed:
        logger.info(f"User {websocket.username} disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Remove the connection from the active connections list
        if websocket.user_id in active_connections:
            del active_connections[websocket.user_id]
            logger.info(f"User {websocket.username} removed from active connections.")

# Function to broadcast messages to all active connections
async def broadcast_message(sender_id, message):
    """
    Broadcast a message to all active WebSocket connections except the sender.
    """
    try:
        for user_id, connection in active_connections.items():
            if user_id != sender_id:
                await connection.send(json.dumps({
                    "type": "message",
                    "sender": sender_id,
                    "content": message,
                    "timestamp": datetime.utcnow().isoformat()
                }))
                logger.info(f"Broadcasted message to user {user_id}.")
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")

# Start the WebSocket server
async def start_ws_server():
    """
    Start the WebSocket server and handle connections.
    """
    try:
        server = await websockets.serve(handle_connection, "localhost", 5003)
        logger.info("WebSocket server started on ws://localhost:5003")
        await server.wait_closed()
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {e}")

# Run the WebSocket server
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start_ws_server())
    asyncio.get_event_loop().run_forever()