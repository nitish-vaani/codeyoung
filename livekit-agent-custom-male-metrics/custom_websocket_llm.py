import asyncio
import json
import logging
import uuid
import websockets
from typing import List, Dict, Any, Optional, AsyncIterable
from livekit.agents import llm

logger = logging.getLogger("websocket-llm")


class CustomWebSocketLLM(llm.LLM):
    def __init__(
        self,
        ws_url: str,
        call_id: Optional[str] = None,
        connection_timeout: float = 10.0,
        response_timeout: float = 30.0,
    ):
        """
        Initialize WebSocket LLM client
        
        Args:
            ws_url: Base WebSocket URL (e.g., "wss://domain.com/llm-websocket")
            call_id: Optional call ID, will be generated if not provided
            connection_timeout: WebSocket connection timeout in seconds
            response_timeout: Response timeout in seconds
        """
        super().__init__()
        self.ws_url = ws_url
        self.call_id = call_id or self._generate_call_id()
        self.connection_timeout = connection_timeout
        self.response_timeout = response_timeout
        
        self._ws: Optional[websockets.WebSocketServerProtocol] = None
        self._response_id_counter = 0
        self._connection_lock = asyncio.Lock()
        self._request_lock = asyncio.Lock()  # Add request-level lock
        
        # Build full WebSocket URL
        self.full_ws_url = f"{self.ws_url.rstrip('/')}/{self.call_id}"
        
        logger.info(f"Initialized WebSocket LLM with URL: {self.full_ws_url}")
    
    def _generate_call_id(self) -> str:
        """Generate a unique call ID"""
        call_id = str(uuid.uuid4()).replace('-', '')[:20]
        logger.info(f"Generated call_id: {call_id}")
        return call_id
    
    async def _ensure_connection(self) -> None:
        """Ensure WebSocket connection is established"""
        async with self._connection_lock:
            if self._ws is None or self._ws.close_code is not None:
                try:
                    logger.info(f"Connecting to WebSocket: {self.full_ws_url}")
                    self._ws = await asyncio.wait_for(
                        websockets.connect(self.full_ws_url),
                        timeout=self.connection_timeout
                    )
                    
                    # Read initial messages (config and greeting)
                    config_msg = await self._ws.recv()
                    logger.debug(f"Received config: {config_msg}")
                    
                    greeting_msg = await self._ws.recv()
                    logger.debug(f"Received greeting: {greeting_msg}")
                    
                    logger.info("WebSocket connection established")
                    
                except Exception as e:
                    logger.error(f"Failed to connect to WebSocket: {e}")
                    raise
    
    def _extract_message_content(self, msg: Any) -> str:
        """Extract text content from a ChatMessage"""
        if hasattr(msg, 'content'):
            content = msg.content
            if isinstance(content, list):
                # Content is a list of strings
                return ' '.join(str(item) for item in content)
            else:
                return str(content)
        elif hasattr(msg, 'text'):
            return msg.text
        else:
            return str(msg)
    
    async def _send_request(self, chat_ctx: llm.ChatContext) -> int:
        """Send a chat request to the WebSocket"""
        # Use request lock to prevent concurrent requests
        async with self._request_lock:
            await self._ensure_connection()
            
            # Get only the latest user message (not the full conversation history)
            # Your WebSocket service expects only the new message, not the full transcript
            latest_message = None
            if chat_ctx.items:
                # Get the last user message
                for msg in reversed(chat_ctx.items):
                    if getattr(msg, 'role', '') == 'user':
                        latest_message = msg
                        break
            
            if not latest_message:
                logger.error("No user message found in chat context")
                raise ValueError("No user message found")
            
            # Convert only the latest message to the expected format
            content = self._extract_message_content(latest_message)
            transcript = [{"role": "user", "content": content}]
            
            # Increment response ID
            self._response_id_counter += 1
            current_response_id = self._response_id_counter
            
            # Prepare the request with only the latest message
            request = {
                "interaction_type": "response_required",
                "response_id": current_response_id,
                "transcript": transcript
            }
            
            logger.debug(f"Sending request: {json.dumps(request)}")
            await self._ws.send(json.dumps(request))
            
            return current_response_id
    
    async def _receive_response(self, expected_response_id: int) -> AsyncIterable[str]:
        """Receive streaming response from WebSocket"""
        full_content = ""
        
        try:
            # Use the same request lock for receiving to prevent concurrent recv calls
            async with self._request_lock:
                while True:
                    response_raw = await asyncio.wait_for(
                        self._ws.recv(),
                        timeout=self.response_timeout
                    )
                    
                    try:
                        response = json.loads(response_raw)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse response: {response_raw}")
                        continue
                    
                    # Check if this is the response we're waiting for
                    if (response.get("response_type") == "response" and 
                        response.get("response_id") == expected_response_id):
                        
                        content = response.get("content", "")
                        is_complete = response.get("content_complete", False)
                        
                        # Handle end_call flag
                        if response.get("end_call", False):
                            logger.info("WebSocket LLM requested to end call")
                        
                        # Only yield non-empty content
                        if content:
                            full_content += content
                            yield content
                        
                        # Check if response is complete
                        if is_complete:
                            logger.debug(f"Response {expected_response_id} completed: {full_content}")
                            break
                    
                    else:
                        logger.debug(f"Ignoring message: {response}")
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response {expected_response_id}")
            raise
        except Exception as e:
            logger.error(f"Error receiving response: {e}")
            raise
    
    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tool_ctx: Optional[Any] = None,
        tools: Optional[Any] = None,  # Accept tools parameter for compatibility
        tool_choice: Optional[Any] = None,  # Accept tool_choice parameter for compatibility
        **kwargs  # Accept any other parameters LiveKit might pass
    ):
        """
        Main chat method that LiveKit agents will call
        
        Note: tool_choice and other parameters are accepted for compatibility
        but not used in this WebSocket implementation
        
        Returns an async context manager that yields the LLM stream
        """
        return WebSocketLLMChatContext(self, chat_ctx, tools or tool_ctx)
    
    async def close(self):
        """Close the WebSocket connection"""
        if self._ws and self._ws.close_code is None:
            logger.info("Closing WebSocket connection")
            await self._ws.close()


class WebSocketLLMChatContext:
    """Async context manager for WebSocket LLM chat"""
    
    def __init__(self, llm_instance, chat_ctx: llm.ChatContext, tools):
        self.llm_instance = llm_instance
        self.chat_ctx = chat_ctx
        self.tools = tools
        self._stream = None
    
    async def __aenter__(self):
        """Enter the async context and return the stream"""
        try:
            # Send the request
            response_id = await self.llm_instance._send_request(self.chat_ctx)
            
            # Create and return the stream
            self._stream = WebSocketLLMStream(
                self.llm_instance._receive_response(response_id),
                websocket_llm_instance=self.llm_instance,
                chat_ctx=self.chat_ctx,
                tool_ctx=self.tools,
            )
            return self._stream
            
        except Exception as e:
            logger.error(f"Error in chat context enter: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context"""
        if self._stream:
            await self._stream.aclose()
        return False


class WebSocketLLMStream(llm.LLMStream):
    def __init__(
        self,
        response_generator: AsyncIterable[str],
        websocket_llm_instance,
        chat_ctx: llm.ChatContext,
        tool_ctx: Optional[Any] = None,
    ):
        try:
            # Try to import APIConnectOptions
            from livekit.agents.llm.llm import APIConnectOptions
            conn_options = APIConnectOptions()
        except ImportError:
            # If not available, try to create a minimal object or use None
            conn_options = None
        
        try:
            super().__init__(
                llm=websocket_llm_instance, 
                chat_ctx=chat_ctx, 
                tools=tool_ctx or [], 
                conn_options=conn_options
            )
        except TypeError as e:
            # If conn_options is not needed or has a different name, try without it
            logger.debug(f"Failed with conn_options, trying without: {e}")
            super().__init__(
                llm=websocket_llm_instance, 
                chat_ctx=chat_ctx, 
                tools=tool_ctx or []
            )
        
        self._response_generator = response_generator
        self._content = ""
    
    async def _run(self):
        """Required abstract method implementation"""
        # This method should be called automatically by the base class
        # We handle streaming in __anext__ instead
        pass
    
    async def __anext__(self) -> llm.ChatChunk:
        """Return the next chunk in the stream"""
        try:
            content = await self._response_generator.__anext__()
            self._content += content
            
            # Create ChatChunk with ChoiceDelta and required id field
            return llm.ChatChunk(
                id=f"chunk_{uuid.uuid4().hex[:8]}",  # Generate unique ID
                delta=llm.ChoiceDelta(content=content, role="assistant")
            )
        except StopAsyncIteration:
            # End of stream
            raise StopAsyncIteration
    
    async def aclose(self) -> None:
        """Close the stream"""
        pass