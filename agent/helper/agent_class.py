"""
Combined agent classes for both voice and chat modalities.
Contains base agent with shared functionality and specific implementations for each modality.
"""

import json
import asyncio
import time
from datetime import datetime
from typing import Any, Dict, AsyncIterable
from abc import ABC, abstractmethod
from datetime import datetime

from livekit import rtc
from livekit.agents import (Agent, function_tool, RunContext, llm)
from livekit.agents import ModelSettings, FunctionTool
from utils.hungup_idle_call import hangup
from utils.utils import load_prompt
from utils.gpt_inferencer import LLMPromptRunner
from utils.number_to_conversational_string import convert_number_to_conversational
from utils.preprocess_text_before_tts import preprocess_text
from .config_manager import config_manager
from .call_handlers import CallState
from .database_helpers import insert_call_end_async
from .transcript_manager import transcript_manager
from .logging_config import get_logger
from .rag_connector import enrich_with_rag

from .chat_database_helpers import (
    insert_chat_session_start, insert_chat_session_end, 
    insert_chat_message, update_chat_session_activity
)

logger = get_logger(__name__)

class BaseCustomerServiceAgent(ABC):
    """Base class containing shared functionality for voice and chat agents"""
    
    def __init__(
        self,
        *,
        agent_name: str,
        appointment_time: str,
        contact_info: dict[str, Any],
        session_state: CallState,
        prompt_path: str,
        modality: str = "voice",  # "voice" or "chat"
    ):
        # Load and process prompt
        _prompt = load_prompt(prompt_path, full_path=True)
        _prompt = _prompt.replace("{{phone_string}}", convert_number_to_conversational(contact_info.get("phone", "unknown")))
        _prompt = _prompt.replace("{{phone_numeric}}", str(contact_info.get("phone", "unknown")))
        _prompt = _prompt.replace("{{current_time}}", datetime.now().strftime("%Y-%m-%d %H:%M"))
        _prompt = _prompt.replace("{{name}}", str(contact_info.get("name", "N/A")))

        
        self._instructions = _prompt
        self.agent_name = agent_name
        self.appointment_time = appointment_time
        self.contact_info = contact_info
        self.llm_obj = LLMPromptRunner(api_key=config_manager.get_openai_api_key())
        self.session_state = session_state
        self.modality = modality
        self._seen_results = set()
        
        # Config for tool call visibility
        self.config = config_manager.config
        self.show_tool_calls = self.config.get("show_tool_call_in_chat", False)
        
        logger.info(f"Initialized {self.modality} agent: {self.agent_name}")

    @abstractmethod
    async def send_message(self, message: str, message_type: str = "text"):
        """Abstract method to send messages - implemented by subclasses"""
        pass

    @abstractmethod
    async def end_session(self, ctx: RunContext):
        """Abstract method to end session - implemented by subclasses"""
        pass

    async def send_tool_call_message(self, tool_name: str, query: str = "", status: str = "start", 
                                   result: str = "", time_taken: float = 0, error: str = ""):
        """Send tool call progress message if enabled"""
        if not self.show_tool_calls:
            return
            
        if status == "start":
            message = f"🔧 Executing: {tool_name}"
            if query:
                message += f"\n📝 Query: \"{query}\""
            message += "\n⏱️ Processing..."
            await self.send_message(message, "tool_start")
            
        elif status == "success":
            message = f"✅ Completed in {time_taken:.1f}s"
            if result:
                message += f"\n📊 {result}"
            await self.send_message(message, "tool_success")
            
        elif status == "error":
            message = f"❌ Failed in {time_taken:.1f}s"
            if error:
                message += f"\n⚠️ {error}"
            await self.send_message(message, "tool_error")

    @function_tool
    async def search_knowledge_base(self, context: RunContext, query: str):
        """
        Lookup knowledge base if extra information is needed for user's query. 
        This method searches documents related to services, pricing, locations etc.
        """
        start_time = time.time()
        
        # Show tool call start
        await self.send_tool_call_message("search_knowledge_base", query, "start")
        
        # Send a verbal status update to the user after a short delay for voice mode
        async def _speak_status_update(delay: float = 4):
            await asyncio.sleep(delay)
            if self.modality == "voice":
                await context.session.generate_reply(instructions=f"""
                    You are searching the knowledge base for \"{query}\" but it is taking a little while.
                    Update the user on your progress, but be very brief.
                """)
        
        status_update_task = None
        if self.modality == "voice":
            status_update_task = asyncio.create_task(_speak_status_update(4))
        
        try:
            all_results = await enrich_with_rag(query)
            
            # Filter out previously seen results
            new_results = [r for r in all_results if r not in self._seen_results]
            
            if len(new_results) == 0:
                result_msg = "No new context found"
                time_taken = time.time() - start_time
                await self.send_tool_call_message("search_knowledge_base", query, "success", 
                                                result_msg, time_taken)
                return "No new context found. - 'Tell client that you are not aware of this and our team will reach out to you on this.'"
            else:
                new_results = new_results[:2]  # Take top 2 new results

            self._seen_results.update(new_results)

            context_str = ""
            for i, res in enumerate(new_results):
                context_str += f"\n context {i}: {res}\n"

            result_msg = f"Found {len(new_results)} relevant documents"
            time_taken = time.time() - start_time
            await self.send_tool_call_message("search_knowledge_base", query, "success", 
                                            result_msg, time_taken)

            # Cancel status update if search completed before timeout
            if status_update_task:
                status_update_task.cancel()
                
            return new_results
            
        except Exception as e:
            time_taken = time.time() - start_time
            error_msg = f"Search failed: {str(e)}"
            await self.send_tool_call_message("search_knowledge_base", query, "error", 
                                            "", time_taken, error_msg)
            logger.error(f"Knowledge base search error: {e}")
            return "Search temporarily unavailable. Please try again."

    @function_tool
    async def validate_customer_details(self, ctx: RunContext):
        """Validate customer details by extracting entities from conversation"""
        start_time = time.time()
        
        await self.send_tool_call_message("validate_customer_details", "", "start")
        
        if self.modality == "voice":
            await ctx.session.generate_reply(
                instructions="Kindly ask customer to wait for few seconds as you are validating the information required for service booking."
            )
        
        try:
            entities = [
                ('Name', 'What is the name of the user'),
                ('Mobile_Number', "What is contact mobile number used for booking service?"),
                ('Approximate_Mileage', "What is the mileage on the vehicle"),
                ('Location_Area', "what is the area/region where user wants services?"),
                ('Specific_Location', "What is the specific location within area where user wants service"),
            ]
            
            from utils.entity_extractor_dynamic_prompt import generate_prompt_to_get_entities_from_transcript
            prompt = generate_prompt_to_get_entities_from_transcript(
                transcript=transcript_manager.get_transcript(), 
                fields=entities
            )
            content = self.llm_obj.run_prompt(prompt)
            
            # Clean up JSON response
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            try:
                content = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse entity extraction response: {e}")
                time_taken = time.time() - start_time
                await self.send_tool_call_message("validate_customer_details", "", "error", 
                                                "", time_taken, "Failed to parse validation results")
                return "noted"
            
            # Check for missing information
            not_mentioned_keys = [key for key, val in content.items() if val.get('value') == 'Not Mentioned']
            
            time_taken = time.time() - start_time
            
            if not_mentioned_keys:
                ask_about = "\n".join(f"{key}: {value}" for key, value in entities if key in not_mentioned_keys)
                result_msg = f"Missing {len(not_mentioned_keys)} details"
                await self.send_tool_call_message("validate_customer_details", "", "success", 
                                                result_msg, time_taken)
                return f"""Ask user about following missing informations: "{ask_about}". Ask casually and be very crisp."""
            else:
                result_msg = "All details validated successfully"
                await self.send_tool_call_message("validate_customer_details", "", "success", 
                                                result_msg, time_taken)
                return "Noted"
                
        except Exception as e:
            time_taken = time.time() - start_time
            error_msg = f"Validation failed: {str(e)}"
            await self.send_tool_call_message("validate_customer_details", "", "error", 
                                            "", time_taken, error_msg)
            logger.error(f"Validation error: {e}")
            return "Validation temporarily unavailable. Please continue."

    @function_tool
    async def book_service_appointment(self, ctx: RunContext):
        """Book a service appointment for the customer"""
        start_time = time.time()
        await self.send_tool_call_message("book_service_appointment", "", "start")
        
        try:
            # Simulate booking process
            await asyncio.sleep(1)  # Simulate API call
            
            time_taken = time.time() - start_time
            result_msg = "Appointment slot reserved"
            await self.send_tool_call_message("book_service_appointment", "", "success", 
                                            result_msg, time_taken)
            
            logger.info("Booking appointment initiated")
            return "I'll help you book an appointment. Let me get the available slots for you."
            
        except Exception as e:
            time_taken = time.time() - start_time
            error_msg = f"Booking failed: {str(e)}"
            await self.send_tool_call_message("book_service_appointment", "", "error", 
                                            "", time_taken, error_msg)
            logger.error(f"Booking error: {e}")
            return "Booking temporarily unavailable. Our team will contact you to schedule."

    async def record_session_end(self, end_reason: str):
        """Record session end in database asynchronously with optimized queuing"""
        if self.session_state.call_end_recorded or not self.session_state.call_started:
            return
            
        try:
            self.session_state.call_end_recorded = True
            
            # Only update call database for voice modality
            if self.modality == "voice":
                operation_id = await insert_call_end_async(
                    self.session_state.room_name,
                    end_reason
                )
                logger.info(f"Queued session end recording: {operation_id} - {end_reason}")
            else:
                # For chat, the ChatServiceAgent will handle chat-specific DB updates
                logger.info(f"Chat session end recorded separately: {end_reason}")
                
        except Exception as e:
            logger.error(f"Failed to queue session end recording: {e}")

class VoiceServiceAgent(Agent, BaseCustomerServiceAgent):
    """Voice agent class extending both Agent and BaseCustomerServiceAgent"""
    
    def __init__(
        self,
        *,
        agent_name: str,
        appointment_time: str,
        contact_info: dict[str, Any],
        session_state: CallState,
        prompt_path: str,
    ):
        # Initialize base agent with voice modality
        BaseCustomerServiceAgent.__init__(
            self,
            agent_name=agent_name,
            appointment_time=appointment_time,
            contact_info=contact_info,
            session_state=session_state,
            prompt_path=prompt_path,
            modality="voice"
        )
        
        # Initialize LiveKit Agent with instructions from base
        Agent.__init__(self, instructions=self._instructions)
        
        self.participant: rtc.RemoteParticipant | None = None
        
        logger.info(f"Voice agent {agent_name} initialized")


    async def send_message(self, message: str, message_type: str = "text"):
        """Send a message through LiveKit data channels"""
        if not hasattr(self, 'room') or not self.room:
            logger.warning("Cannot send message: room not available")
            return
        
        try:
            # Create message payload
            message_data = {
                "type": message_type,
                "content": message,
                "timestamp": datetime.now().isoformat(),
                "sender": "agent"
            }
            
            # Send through LiveKit data channels
            await self.room.local_participant.publish_data(
                json.dumps(message_data).encode(),
                reliable=True,
                topic="chat_message"
            )
            
            logger.debug(f"Sent {message_type} message: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[FunctionTool],
        model_settings: ModelSettings
    ) -> AsyncIterable[llm.ChatChunk]:
        """Custom LLM node implementation"""
        async for chunk in Agent.default.llm_node(self, chat_ctx, tools, model_settings):
            yield chunk

    async def tts_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        """Custom TTS node with text preprocessing"""
        async def cleaned_text():
            async for chunk in text:
                yield preprocess_text(chunk)

        async for frame in Agent.default.tts_node(self, cleaned_text(), model_settings):
            yield frame

    def set_participant(self, participant: rtc.RemoteParticipant):
        """Set the participant for this agent session"""
        self.participant = participant

    async def on_enter(self):
        """Called when agent enters the conversation"""
        welcome_message = "Hi! You've reached our customer service. I am your assistant, how can I help you today?"
        await self.session.say(text=welcome_message)
        
        agent_name = self.__class__.__name__
        
        # Import here to avoid circular imports
        from .data_entities import UserData
        userdata: UserData = self.session.userdata
        
        if userdata.ctx and userdata.ctx.room:
            await userdata.ctx.room.local_participant.set_attributes(
                {"agent": agent_name}
            )

    @function_tool
    async def end_voice_call(self, ctx: RunContext):
        """End the voice call gracefully"""
        participant_id = self.participant.identity if self.participant else 'unknown'
        logger.info(f"Voice agent initiated call end for {participant_id}")

        await self.record_session_end("Call ended")

        # Wait for current speech to finish
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()

        await hangup()
        return "Noted"
    
    async def end_session(self, ctx: RunContext):
        """Implementation of abstract method"""
        return await self.end_voice_call(ctx)

    @function_tool
    async def detected_answering_machine(self, ctx: RunContext):
        """Handle answering machine detection"""
        participant_id = self.participant.identity if self.participant else 'unknown'
        logger.info(f"Detected answering machine for {participant_id}")
        
        await self.record_session_end("Answering machine detected")
        await hangup()
        return "Noted"

class ChatServiceAgent(BaseCustomerServiceAgent):
    """Chat agent class extending BaseCustomerServiceAgent for text-based conversations"""
    
    def __init__(
        self,
        *,
        agent_name: str,
        appointment_time: str,
        contact_info: dict[str, Any],
        session_state: CallState,
        prompt_path: str,
    ):
        super().__init__(
            agent_name=agent_name,
            appointment_time=appointment_time,
            contact_info=contact_info,
            session_state=session_state,
            prompt_path=prompt_path,
            modality="chat"
        )
        self.participant: rtc.RemoteParticipant | None = None
        self.session = None  # Will be set by session manager
        self.room = None     # Will be set when room is available
        self.chat_session_id = None  # Will be set when registering with session manager
        
        logger.info(f"Chat agent {agent_name} initialized")

    def set_participant(self, participant: rtc.RemoteParticipant):
        """Set the participant for this chat session"""
        self.participant = participant

    def set_session(self, session):
        """Set the session for this chat agent"""
        self.session = session
        
    def set_room(self, room):
        """Set the room for this chat agent"""
        self.room = room

    def register_with_session_manager(self, session_id: str, user_id: str):
        """Register this agent with the chat session manager and start database session"""
        self.chat_session_id = session_id
        
        # Create database session record
        asyncio.create_task(self._create_chat_session_record(session_id, user_id))
        
        logger.info(f"Registered chat agent with session manager: {session_id}")
    
    async def _create_chat_session_record(self, session_id: str, user_id: str):
        """Create the initial database record for this chat session"""
        try:
            from .chat_database_helpers import insert_chat_session_start
            
            # Extract metadata from contact_info and other sources
            session_metadata = {
                "contact_info": self.contact_info,
                "agent_name": self.agent_name,
                "appointment_time": self.appointment_time,
                "modality": self.modality
            }
            
            await insert_chat_session_start(
                session_id=session_id,
                user_id=int(user_id) if user_id.isdigit() else 0,
                room_id=session_id,  # Using session_id as room_id for simplicity
                participant_id=f"chat_user_{user_id}",
                agent_id="chat_agent_1",  # Default agent ID
                agent_name=self.agent_name,
                customer_name=self.contact_info.get("name", "Chat User"),
                session_metadata=session_metadata
            )
            logger.info(f"Created database record for chat session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to create chat session database record: {e}")

    def update_activity(self):
        """Update activity in session manager and database when user sends message"""
        if self.chat_session_id:
            from .chat_session_manager import update_chat_activity
            update_chat_activity(self.chat_session_id)
            
            # Also update database
            asyncio.create_task(self._update_db_activity())
    
    async def _update_db_activity(self):
        """Update database activity timestamp"""
        try:
            from .chat_database_helpers import update_chat_session_activity
            await update_chat_session_activity(self.chat_session_id)
        except Exception as e:
            logger.error(f"Failed to update database activity: {e}")

    async def send_message(self, message: str, message_type: str = "text"):
        """Send a message through LiveKit data channels and save to database"""
        if not self.room:
            logger.warning("Cannot send message: room not available")
            return
        
        try:
            # Create message payload
            message_data = {
                "type": message_type,
                "content": message,
                "timestamp": datetime.now().isoformat(),
                "sender": "agent"
            }
            
            # Send through LiveKit data channels using the room's local participant
            await self.room.local_participant.publish_data(
                json.dumps(message_data).encode(),
                reliable=True,
                topic="chat_message"
            )
            
            # Save agent message to database
            if self.chat_session_id and message_type in ["text", "text_chunk"]:
                await self._save_message_to_db(message, message_type, "agent", message_data["timestamp"])
            
            logger.debug(f"Sent {message_type} message: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def _save_message_to_db(self, content: str, message_type: str, sender: str, timestamp: str):
        """Save message to database"""
        try:
            from .chat_database_helpers import insert_chat_message
            import uuid
            
            message_id = f"msg_{uuid.uuid4().hex[:12]}"
            await insert_chat_message(
                session_id=self.chat_session_id,
                message_id=message_id,
                message_type=message_type,
                content=content,
                sender=sender,
                message_metadata={"timestamp": timestamp}
            )
        except Exception as e:
            logger.error(f"Failed to save message to database: {e}")

    async def stream_response(self, response_text: str):
        """Stream response text in chunks"""
        logger.info("Printing from streaming response")
        if not response_text:
            return
            
        # Clean the response text
        cleaned_text = preprocess_text(response_text)
        
        # Split into chunks (by sentences or fixed length)
        chunks = self._split_into_chunks(cleaned_text)
        
        for chunk in chunks:
            await self.send_message(chunk, "text_chunk")
            await asyncio.sleep(0.1)  # Small delay for streaming effect
            
        # Send end marker
        await self.send_message("", "text_complete")

    def _split_into_chunks(self, text: str, max_chunk_size: int = 50) -> list[str]:
        """Split text into streamable chunks"""
        # First try to split by sentences
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_chunk_size:
                current_chunk += sentence + ". " if sentence != sentences[-1] else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". " if sentence != sentences[-1] else sentence
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks if chunks else [text]

    async def handle_user_message(self, message: str):
        """Process incoming user message and generate response"""
        try:
            print(f"🔄 Processing user message: {message}")
            logger.info(f"Processing user message: {message}")
            
            # Update activity in session manager
            self.update_activity()
            
            # Add user message to transcript
            timestamp = datetime.now().strftime('%H:%M:%S')
            transcript_manager.conversation_transcript += f"\n[{timestamp}] USER: {message}\n"
            
            # Generate response using conversation history for context
            conversation_history = transcript_manager.get_transcript()
            if conversation_history.strip():
                # Include full conversation history for context
                prompt = f"{self._instructions}\n\n{conversation_history}\nUser: {message}\nAssistant:"
            else:
                # First message in conversation
                prompt = f"{self._instructions}\n\nUser: {message}\nAssistant:"
            
            print(f"🧠 Sending prompt to LLM with {len(conversation_history)} chars of history")
            response = self.llm_obj.run_prompt(prompt)
            
            # Add agent response to transcript  
            timestamp = datetime.now().strftime('%H:%M:%S')
            transcript_manager.conversation_transcript += f"\n[{timestamp}] AGENT: {response}\n"
            
            # Stream the response
            print(f"📤 Sending response: {response[:100]}...")
            await self.stream_response(response)
            
        except Exception as e:
            print(f"❌ Error in handle_user_message: {e}")
            logger.error(f"Error handling user message: {e}")
            # Fallback
            await self.send_message("I'm sorry, I encountered an error. Please try again.", "text")
    
    # async def end_session(self, ctx: RunContext):
    #     """Implementation of abstract method to end chat session"""
    #     participant_id = self.participant.identity if self.participant else 'unknown'
    #     logger.info(f"Chat agent initiated session end for {participant_id}")

    #     # Unregister from session manager
    #     if self.chat_session_id:
    #         from .chat_session_manager import chat_timeout_manager
    #         chat_timeout_manager.unregister_session(self.chat_session_id)

    #     await self.record_session_end("Chat ended")
        
    #     # Send goodbye message
    #     await self.send_message("Thank you for chatting with our customer service. Have a great day!", "text")
    #     await asyncio.sleep(1)  # Give time for message to send
        
    #     await hangup()
    #     return "Noted"

    # In agent_class.py - ChatServiceAgent
    async def end_session(self, ctx: RunContext):
        """Implementation of abstract method to end chat session"""
        participant_id = self.participant.identity if self.participant else 'unknown'
        logger.info(f"Chat agent initiated session end for {participant_id}")

        # Unregister from session manager
        if self.chat_session_id:
            from .chat_session_manager import chat_timeout_manager
            chat_timeout_manager.unregister_session(self.chat_session_id)

        await self.record_session_end("Chat ended")
        
        # Send goodbye message
        await self.send_message("Thank you for chatting with our customer service. Have a great day!", "text")
        await asyncio.sleep(1)  # Give time for message to send
        
        # PROPERLY DISCONNECT THE ROOM
        if self.room:
            await self.room.disconnect()
        
        return "Noted"


    @function_tool
    async def end_chat_session(self, ctx: RunContext):
        """End the chat session gracefully - this is the function tool version"""
        return await self.end_session(ctx)

    @function_tool
    async def detected_answering_machine(self, ctx: RunContext):
        """Handle answering machine detection (not applicable for chat)"""
        participant_id = self.participant.identity if self.participant else 'unknown'
        logger.info(f"Detected answering machine for {participant_id} (chat mode)")
        
        await self.record_session_end("Answering machine detected")
        await hangup()
        return "Noted"

    async def on_enter(self):
        """Called when agent enters the chat conversation"""
        welcome_message = "Hi! You've reached our customer service. I am your assistant, how can I help you today?"
        await self.send_message(welcome_message, "text")
        
        # Set agent attribute in room if available
        if self.room:
            await self.room.local_participant.set_attributes(
                {"agent": "ChatServiceAgent"}
            )

    async def on_data_received(self, data_packet: rtc.DataPacket):
        """Handle incoming data from user"""
        try:
            # Decode the data
            message_data = json.loads(data_packet.data.decode())
            
            print(f"📨 Received data: {message_data}")  # Debug logging
            
            if message_data.get("type") == "user_message":
                user_message = message_data.get("content", "")
                print(f"👤 Processing user message: {user_message}")  # Debug logging
                
                # Save user message to database
                if self.chat_session_id:
                    await self._save_message_to_db(
                        user_message, 
                        "user_message", 
                        "user", 
                        message_data.get("timestamp", datetime.now().isoformat())
                    )
                
                await self.handle_user_message(user_message)
            else:
                print(f"🔍 Unknown message type: {message_data.get('type')}")  # Debug logging
                
        except Exception as e:
            logger.error(f"Error processing data packet: {e}")
            print(f"❌ Error processing data packet: {e}")  # Debug logging

    # async def record_session_end(self, end_reason: str):
    #     """Record session end in database - use chat tables for chat sessions"""
    #     if self.session_state.call_end_recorded or not self.session_state.call_started:
    #         return
            
    #     try:
    #         self.session_state.call_end_recorded = True
            
    #         if self.modality == "chat" and self.chat_session_id:
    #             # Use chat-specific database table
    #             from .chat_database_helpers import insert_chat_session_end
    #             success = await insert_chat_session_end(self.chat_session_id, end_reason)
    #             if success:
    #                 logger.info(f"Recorded chat session end: {self.chat_session_id} - {end_reason}")
    #             else:
    #                 logger.error(f"Failed to record chat session end: {self.chat_session_id}")
    #         else:
    #             # Use call database for voice sessions
    #             operation_id = await insert_call_end_async(
    #                 self.session_state.room_name,
    #                 end_reason
    #             )
    #             logger.info(f"Queued session end recording: {operation_id} - {end_reason}")
    #     except Exception as e:
    #         logger.error(f"Failed to record session end: {e}")


    # In agent/helper/agent_class.py - ChatServiceAgent class

    async def record_session_end(self, end_reason: str):
        """Record session end in database - use chat tables for chat sessions"""
        if self.session_state.call_end_recorded or not self.session_state.call_started:
            return
            
        try:
            self.session_state.call_end_recorded = True
            
            if self.modality == "chat" and self.chat_session_id:
                # Use chat-specific database table ONLY
                from .chat_database_helpers import insert_chat_session_end
                success = await insert_chat_session_end(self.chat_session_id, end_reason)
                if success:
                    logger.info(f"Recorded chat session end: {self.chat_session_id} - {end_reason}")
                else:
                    logger.error(f"Failed to record chat session end: {self.chat_session_id}")
            else:
                # Use call database for voice sessions ONLY
                operation_id = await insert_call_end_async(
                    self.session_state.room_name,
                    end_reason
                )
                logger.info(f"Queued session end recording: {operation_id} - {end_reason}")
        except Exception as e:
            logger.error(f"Failed to record session end: {e}")



# Factory Functions
def create_voice_service_agent(agent_name: str, appointment_time: str, contact_info: dict[str, Any], 
                              session_state: CallState, prompt_path: str) -> VoiceServiceAgent:
    """Factory function to create a VoiceServiceAgent instance"""
    return VoiceServiceAgent(
        agent_name=agent_name,
        appointment_time=appointment_time,
        contact_info=contact_info,
        session_state=session_state,
        prompt_path=prompt_path
    )

def create_chat_service_agent(agent_name: str, appointment_time: str, contact_info: dict[str, Any], 
                             session_state: CallState, prompt_path: str) -> ChatServiceAgent:
    """Factory function to create a ChatServiceAgent instance"""
    return ChatServiceAgent(
        agent_name=agent_name,
        appointment_time=appointment_time,
        contact_info=contact_info,
        session_state=session_state,
        prompt_path=prompt_path
    )

# Backward compatibility aliases (optional - you can remove these)
def create_mysyara_agent(*args, **kwargs):
    """Backward compatibility wrapper"""
    return create_voice_service_agent(*args, **kwargs)

def create_mysyara_chat_agent(*args, **kwargs):
    """Backward compatibility wrapper"""
    return create_chat_service_agent(*args, **kwargs)



