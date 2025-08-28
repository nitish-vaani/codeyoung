# import os
# from dotenv import load_dotenv
# from livekit.plugins import openai

# load_dotenv()

# class CustomLLM:
#     def __init__(self, model="gpt-4o", temperature=0.7, max_tokens=1000):
#         """
#         Initialize OpenAI LLM with custom parameters
        
#         Args:
#             model (str): OpenAI model to use
#             temperature (float): Sampling temperature
#             max_tokens (int): Maximum tokens to generate
#         """
#         self.model = model
#         self.temperature = temperature
#         # self.max_tokens = max_tokens
        
#         # Verify API key is set
#         if not os.getenv("OPENAI_API_KEY"):
#             raise ValueError("OPENAI_API_KEY environment variable is required")
    
#     def get_llm(self):
#         """
#         Returns configured OpenAI LLM instance
#         """
#         return openai.LLM(
#             model=self.model,
#             temperature=self.temperature,
#             # max_tokens=self.max_tokens
#         )
    
#     def update_config(self, **kwargs):
#         """
#         Update LLM configuration parameters
#         """
#         for key, value in kwargs.items():
#             if hasattr(self, key):
#                 setattr(self, key, value)
#         return self.get_llm()


import os
from dotenv import load_dotenv
from livekit.plugins import openai
from custom_websocket_llm import CustomWebSocketLLM

load_dotenv()

class CustomLLM:
    def __init__(self, llm_type="openai", **kwargs):
        """
        Initialize LLM with support for multiple backends
        
        Args:
            llm_type (str): Type of LLM to use ("openai" or "websocket")
            **kwargs: Configuration parameters for the selected LLM
        """
        self.llm_type = llm_type.lower()
        
        if self.llm_type == "openai":
            self._init_openai_llm(**kwargs)
        elif self.llm_type == "websocket":
            self._init_websocket_llm(**kwargs)
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}")
    
    def _init_openai_llm(self, model="gpt-4o", temperature=0.7, max_tokens=1000, **kwargs):
        """Initialize OpenAI LLM"""
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._llm = None
    
    def _init_websocket_llm(self, ws_url=None, call_id=None, connection_timeout=10.0, response_timeout=30.0, **kwargs):
        """Initialize WebSocket LLM"""
        if not ws_url:
            ws_url = os.getenv("WEBSOCKET_LLM_URL")
            if not ws_url:
                raise ValueError("WebSocket URL must be provided via ws_url parameter or WEBSOCKET_LLM_URL environment variable")
        
        self.ws_url = ws_url
        self.call_id = call_id
        self.connection_timeout = connection_timeout
        self.response_timeout = response_timeout
        self._llm = None
    
    def get_llm(self):
        """Returns configured LLM instance"""
        if self._llm is None:
            if self.llm_type == "openai":
                self._llm = openai.LLM(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            elif self.llm_type == "websocket":
                self._llm = CustomWebSocketLLM(
                    ws_url=self.ws_url,
                    call_id=self.call_id,
                    connection_timeout=self.connection_timeout,
                    response_timeout=self.response_timeout
                )
        
        return self._llm
    
    def update_config(self, **kwargs):
        """Update LLM configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Reset the LLM instance to pick up new config
        self._llm = None
        return self.get_llm()
    
    async def close(self):
        """Close the LLM connection (if applicable)"""
        if self._llm and hasattr(self._llm, 'close'):
            await self._llm.close()