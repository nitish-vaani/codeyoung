##################################################################################################
# IMPORTS AND CONFIGURATION
##################################################################################################

from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import uvicorn
from sqlalchemy import create_engine, text, event, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, DisconnectionError
from database.db_test.db import SessionLocal, engine, Base, get_db
from database.db_test import models
import os
from .openai_eval import *
from database.connectors.s3 import S3Connector
from utils.utility import get_month_year_from_datetime, get_call_duration, current_time, strip_data_func
from datetime import datetime, timedelta
from urllib.parse import unquote
from .extractor_config import *
from database.db_test.db import get_call_by_room
from database.db_test.database_config import get_db_type
from utils.plivo_outbound_dispatch import main as plivo_outbound
from .prompts_for_eval.prompt import prompt, prompt2
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response
from io import BytesIO
from dotenv import load_dotenv
import httpx
import asyncio
import json
import logging
import random
from livekit import api
from agent.helper.config_manager import config_manager

# Load configuration
config = config_manager.config

# Load environment variables
load_dotenv(dotenv_path="/app/.env.local")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./backend/test.db")
EARKART_CALLING_NUMBER = os.getenv("EARKART_CALLING_NUMBER", "+918035315360")
EARKART_INCOMING_ID = int(os.getenv("EARKART_INCOMING_ID", 2))
PLIVO_AUTH_ID = os.environ.get("PLIVO_AUTH_ID")
PLIVO_AUTH_TOKEN = os.environ.get("PLIVO_AUTH_TOKEN")
PLIVO_FROM_NUMBER = os.environ.get("PLIVO_FROM_NUMBER", "+918035315890")
BASE_URL = os.environ.get("BASE_URL", "https://if-bk.vaaniresearch.com")

# Database setup
Base.metadata.create_all(bind=engine)
DB_TYPE = get_db_type()

# Logging setup
logger = logging.getLogger("api")

# FastAPI app setup
app = FastAPI(title="LiveKit Dispatch API with Dashboard")
open_ai_api = os.getenv("OPENAI_API_KEY")
client_name = os.getenv("CLIENT_NAME")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

##################################################################################################
# DATABASE DEPENDENCY
##################################################################################################

def get_database():
    """Enhanced database dependency with error handling"""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        print("Database connection established successfully.")
        yield db
    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in get_database: {e}")
        db.rollback()
        db.close()
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            yield db
        except Exception as retry_error:
            logger.error(f"Failed to establish database connection: {retry_error}")
            db.rollback()
            db.close()
            raise HTTPException(status_code=503, detail="Database unavailable")
    except Exception as e:
        logger.error(f"Database error in get_database: {e}")
        db.rollback()
        db.close()
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        db.close()

##################################################################################################
# PYDANTIC MODELS
##################################################################################################

# User Models
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# Call/Dispatch Models
class DispatchRequest(BaseModel):
    user_id: str
    name: str = Field(..., description="Customer name")
    contact_number: str = Field(..., description="Contact number with country code")
    agent_name: str = Field(..., description="Agent Name")
    
    @validator('contact_number')
    def validate_contact_number(cls, v):
        if not v.startswith('+'):
            v = '+' + v
        return v

class DispatchResponse(BaseModel):
    success: bool
    message: Optional[str] = "Command processed"
    output: Optional[str] = None
    error: Optional[str] = None

# Model Management
class ModelCreate(BaseModel):
    model_id: str
    model_name: str
    client_name: str

class ModelUpdate(BaseModel):
    model_name: str | None = None
    client_name: str | None = None

    class Config:
        orm_mode = True

# Call Update
class CallUpdate(BaseModel):
    call_id: str
    name: Optional[str] = None
    call_from: Optional[str] = None
    call_to: Optional[str] = None
    call_type: Optional[str] = None
    call_started_at: Optional[datetime] = None
    call_duration: Optional[float] = None
    call_summary: Optional[str] = None
    call_transcription: Optional[str] = None
    call_recording_url: Optional[str] = None
    call_conversation_quality: Optional[dict] = None
    model_id: Optional[str] = None
    call_completed: Optional[bool] = False
    user_id: Optional[int] = None
    call_entity: Optional[dict] = None

# Feedback
class FeedbackCreate(BaseModel):
    user_id: int
    feedback_text: str
    felt_natural: Optional[int] = None
    response_speed: Optional[int] = None
    interruptions: Optional[int] = None

# Dashboard Models
class DashboardMetrics(BaseModel):
    total_calls: int
    total_leads: int
    conversion_rate: float
    avg_call_duration: float

class TrendData(BaseModel):
    date: str
    calls: int
    leads: int
    duration: float

class DashboardResponse(BaseModel):
    metrics: DashboardMetrics
    call_trends: List[TrendData]
    lead_trends: List[TrendData]
    period: str

# Chat Models
class ChatRequest(BaseModel):
    user_id: str
    name: str = Field(..., description="Customer name")
    agent_name: str = Field(..., description="Agent Name")
    session_id: Optional[str] = Field(None, description="Optional session ID for continuing chat")

class ChatResponse(BaseModel):
    success: bool
    message: Optional[str] = "Chat session processed"
    output: Optional[str] = None
    error: Optional[str] = None
    room_id: Optional[str] = None
    chat_db_id: Optional[int] = None

##################################################################################################
# CORE BUSINESS APIS (Used by Frontend)
##################################################################################################

# ============================================================================
# USER AUTHENTICATION APIS
# ============================================================================

@app.post("/api/users/")
def create_user(user: UserCreate, db: Session = Depends(get_database)):
    try:
        new_user = models.User(**user.dict())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in create_user: {e}")
        db.rollback()
        raise HTTPException(status_code=503, detail="Database connection issue, please try again")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.post("/api/login/")
def login(user: UserLogin, db: Session = Depends(get_database)):
    try:
        user_data = db.query(models.User).filter(
            models.User.username == user.username, 
            models.User.password == user.password
        ).first()
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"message": "Login successful", "user_id": user_data.id, "user_name": user_data.username}
    except HTTPException:
        raise
    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in login: {e}")
        db.rollback()
        raise HTTPException(status_code=503, detail="Database connection issue, please try again")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# CALL MANAGEMENT APIS
# ============================================================================

@app.post("/api/trigger-call/", response_model=DispatchResponse)
async def create_dispatch(fastapi_request: Request, db: Session = Depends(get_database)):
    """
    Create an outbound call using either Plivo or Twilio/LiveKit based on configuration.
    """
    try:
        request_body = await fastapi_request.json()
        print(f"request_body: {request_body}")

        if request_body['id'] == "":
            pass
        else:
            return "Not a valid user_id"

        # Get agent model from DB
        model = db.query(models.Model).filter(models.Model.model_id == request_body['agent_id']).first()
        if not model:
            raise HTTPException(status_code=404, detail=f"Model with ID {request_body['agent_id']} not found")

        # Create metadata (common for both services)
        metadata_ = {
            "name": request_body['name'],
            "phone": request_body['contact_number'],
            "agent_name": model.model_name,
            "voice": request_body.get('voice', 'default')
        }

        # Check telephony configuration and route accordingly
        if config['telephony'] == 'plivo':
            # ========== PLIVO IMPLEMENTATION ==========
            import requests, time, uuid
            
            # Validate phone number
            phone = request_body['contact_number'].strip()
            if not phone.startswith("+"):
                raise HTTPException(status_code=400, detail="Phone number must include country code")

            # Generate unique call/room ID
            room_id = f"outbound-{int(time.time())}-{uuid.uuid4().hex[:8]}"

            # Build Plivo Answer URL
            answer_url = (
                f"https://pacewisdom-ws.vaaniresearch.com/plivo-app/plivo.xml"
                f"?agent={model.model_name}"
                f"&bg_noise=true&noise_type=call-center&noise_volume=1"
            )
            print(f"Answer URL: {answer_url}")

            # Make Plivo API request
            url = f"https://api.plivo.com/v1/Account/{PLIVO_AUTH_ID}/Call/"
            params = {
                "from": PLIVO_FROM_NUMBER,
                "to": phone,
                "answer_url": answer_url,
                "hangup_url": "https://pacewisdom-ws.vaaniresearch.com/plivo-app/hangup",
                "answer_method": "GET",
                "hangup_method": "POST",
                "time_limit": 3600,
                "timeout": 30,
            }

            response = requests.post(
                url,
                json=params,
                auth=(PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN),
                timeout=10
            )

            if response.status_code != 201:
                error_data = response.json() if response.content else {}
                logger.error(f"Plivo API error ({response.status_code}): {error_data}")
                raise HTTPException(status_code=500, detail=f"Plivo API error: {error_data}")

            call_data = response.json()
            call_uuid = call_data.get("request_uuid")
            print(f"Plivo Call Data: {call_data}, UUID: {call_uuid}")

            # Prepare result object
            result = {
                "success": True,
                "output": f'room:"{call_uuid}"',
                "metadata": metadata_,
                "agent_name": model.model_name
            }

            # Create database record with Plivo-specific data
            new_call = models.Call(
                user_id=int(request_body['user_id']),
                call_id=room_id,
                name=request_body['name'],
                call_to=request_body['contact_number'],
                call_from=PLIVO_FROM_NUMBER,
                call_type="Outbound",
                model_id=model.model_id,
                call_transcription=f"{BASE_URL}/api/transcript/{call_uuid}",
                call_recording_url=f"{BASE_URL}/api/stream/{call_uuid}",
                call_duration=0,
                call_metadata={
                    "plivo": True,
                    "plivo_uuid": call_uuid,
                    **metadata_
                }
            )

        else:
            # ========== TWILIO/LIVEKIT IMPLEMENTATION ==========
            from utils.call import run_livekit_dispatch
            
            result = run_livekit_dispatch(
                metadata=metadata_,
                contact_number=request_body['contact_number'],
                agent_name=model.model_name,
            )
            if not result["success"]:
                raise HTTPException(status_code=500, detail=result["error"])
            
            # Parse the result output to extract the room ID
            import re
            room_match = re.search(r'room:"(.*?)"', result["output"])
            room_id = room_match.group(1) if room_match else None
            
            # Create database record with Twilio/LiveKit-specific data
            new_call = models.Call(
                user_id=int(request_body['user_id']),
                call_id=room_id,
                name=request_body['name'],
                call_to=request_body['contact_number'],
                call_from="+12512202179",
                call_type="Outbound",
                model_id=model.model_id,
                call_transcription=f"{BASE_URL}/api/transcript/{room_id}",
                call_recording_url=f"{BASE_URL}/api/stream/{room_id}",
                call_duration=0,
                call_metadata={
                    "twilio": True,
                    **metadata_
                }
            )

        # Common database operations (for both Plivo and Twilio)
        db.add(new_call)
        db.commit()
        db.refresh(new_call)
        
        # Add call ID to the response
        result["call_db_id"] = new_call.id
        
        return result
        
    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in create_dispatch: {e}")
        db.rollback()
        raise HTTPException(status_code=503, detail="Database connection issue, please try again")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating dispatch: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating dispatch: {str(e)}")

@app.get("/api/call-history/{user_id}/{client_name}")
async def get_call_history(user_id: int, client_name: str, db: Session = Depends(get_database)):
    try:
        import time
        from datetime import datetime
        
        start_time_total = time.time()
        call_history = db.query(models.Call).filter(models.Call.user_id.in_([EARKART_INCOMING_ID, user_id])).all()

        curated_response = []
        for call in call_history:
            updated_call = {}
            conversation_id = call.call_id
            
            call_data_row = call
            
            if call_data_row is None:
                if call.call_status == "ended":
                    call_status = "ended"
                else:
                    call_status = "Ongoing"
                
                updated_call['Name'] = {'name': call.name}
                updated_call['Start_time'] = call.call_started_at
                updated_call['End_time'] = call.call_ended_at if call.call_ended_at else call.call_started_at
                updated_call['recording_api'] = f"{BASE_URL}/api/stream/{call.call_id}"
                updated_call['call_details'] = f"{BASE_URL}/api/call_details/{client_name}/{user_id}/{call.call_id}"
                updated_call['call_type'] = call.call_type
                updated_call['call_status'] = call_status
                updated_call['from_number'] = call.call_from
                updated_call['to_number'] = call.call_to
                updated_call['direction'] = call.call_type
                updated_call['duration_ms'] = call.call_duration

            else:
                # Get the duration of the call in ms
                if call_data_row.call_ended_at is None and call_data_row.call_status in ["started", "Call rejected", "Not picked"]:
                    duration = 0
                else:
                    started_at_str = call_data_row.call_started_at
                    ended_at_str = call_data_row.call_ended_at

                    def safe_parse_datetime(dt_value):
                        if dt_value is None:
                            return None
                        
                        if isinstance(dt_value, datetime):
                            return dt_value
                        
                        if isinstance(dt_value, str):
                            try:
                                return datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                            except ValueError:
                                try:
                                    return datetime.strptime(dt_value, '%Y-%m-%d %H:%M:%S')
                                except ValueError:
                                    print(f"Warning: Could not parse datetime string: {dt_value}")
                                    return None
                        
                        print(f"Warning: Unexpected datetime type: {type(dt_value)} with value: {dt_value}")
                        return None

                    if started_at_str and ended_at_str:
                        started_at = safe_parse_datetime(started_at_str)
                        ended_at = safe_parse_datetime(ended_at_str)
                        
                        if started_at and ended_at:
                            duration = (ended_at - started_at).total_seconds() * 1000
                        else:
                            duration = 0
                    else:
                        duration = 0

                updated_call['Name'] = {'name': call.name}
                updated_call['Start_time'] = call_data_row.call_started_at
                updated_call['End_time'] = call_data_row.call_ended_at if call_data_row.call_ended_at else call.call_started_at
                updated_call['recording_api'] = f"{BASE_URL}/api/stream/{call.call_id}"
                updated_call['call_details'] = f"{BASE_URL}/api/call_details/{client_name}/{user_id}/{call.call_id}"
                updated_call['call_type'] = call.call_type
                updated_call['call_status'] = call_data_row.call_status if call_data_row.call_status else "NA"
                updated_call['from_number'] = call.call_from
                updated_call['to_number'] = call.call_to
                updated_call['direction'] = call.call_type
                updated_call['duration_ms'] = duration
            
            curated_response.append(updated_call)

        reversed_list = curated_response[::-1]
        return reversed_list
        
    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in get_call_history: {e}")
        raise HTTPException(status_code=503, detail="Database connection issue, please try again")
    except Exception as e:
        logger.error(f"Error fetching call history: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching call history: {str(e)}")

@app.get("/api/transcript/{call_id}")
async def get_transcript(call_id: str, db: Session = Depends(get_database)):
    """Retrieve the transcript for a call"""
    try:
        call = db.query(models.Call).filter(models.Call.call_id == call_id).first()
        if not call:
            raise HTTPException(status_code=404, detail=f"Call with ID {call_id} not found")
        
        status_code = 200
        
        s3_bucket = os.getenv("AWS_BUCKET")
        s3_connector = S3Connector(s3_bucket)
        year, month = get_month_year_from_datetime(str(call.call_started_at))
        transcript_path = f"transcripts/{client_name}/{year}/{month}/{call_id}.txt"
            
        try:
            result_transcript = await s3_connector.fetch_file_async(transcript_path)
            transcript_bytes = result_transcript if result_transcript is not None else None
            
            if transcript_bytes is None:
                transcript_content = "Transcript not found in S3"
                status_code = 404
                call_duration = 0
            else:
                transcript_cont_ = transcript_bytes.decode('utf-8')
                if transcript_cont_ == "":
                    transcript_content = "Transcript is empty"
                    call_duration = 0
                else:
                    call_data_row = get_call_by_room(call_id)
                    if call_data_row is None:
                        call_duration = get_call_duration(transcript_cont_)
                    else:
                        if call_data_row.get('ended_at') is None and call_data_row.get('status') in ["started", "Call rejected", "Not picked"]:
                            duration = 0
                        else:
                            started_at_str = call_data_row.get('started_at')
                            ended_at_str = call_data_row.get('ended_at')

                            if started_at_str and ended_at_str:
                                started_at = datetime.fromisoformat(started_at_str)
                                ended_at = datetime.fromisoformat(ended_at_str)
                                duration = (ended_at - started_at).total_seconds() * 1000
                            else:
                                duration = 0

                    call_duration = duration
                    transcript_content = strip_data_func(transcript_cont_)
            
            # Update the call record with the transcript
            call.call_transcription = transcript_content
            call.call_duration = call_duration
            db.commit()
            db.refresh(call)

            return {"transcript": transcript_content, "status_code": status_code, "function": "get_transcript"}
    
        except Exception as e:
            return {"transcript": "Error fetching transcript", "status_code": 500, "function": "get_transcript", "error": str(e)}

    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in get_transcript: {e}")
        return {"transcript": "Database connection issue", "status_code": 503, "function": "get_transcript", "error": str(e)}
    except Exception as e:
        return {"transcript": "Error retrieving transcript", "status_code": 500, "function": "get_transcript(exception)", "error": str(e)}

@app.get("/api/stream/{call_id}")
async def stream_audio(call_id: str):
    """Stream audio file from S3"""
    try:
        s3_bucket = os.getenv("AWS_BUCKET")
        if not s3_bucket:
            raise HTTPException(status_code=404, detail="Audio storage not configured")
            
        s3_connector = S3Connector(s3_bucket)
        path_of_recording = f"mp3/{call_id}.mp3"
        audio_bytes = await s3_connector.fetch_file_async(path_of_recording)

        if audio_bytes is None:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        async def stream_audio_content():
            yield audio_bytes
        
        return StreamingResponse(
            stream_audio_content(),
            media_type="audio/mpeg"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error streaming audio: {str(e)}")

@app.get("/api/call_details/{client}/{user_id}/{call_id}")
async def get_call_details(client: str, user_id: str, call_id: str, db: Session = Depends(get_database)):
    try:
        # Verify Call ownership
        call_records = (
            db.query(models.Call)
            .join(models.Model, models.Model.model_id.in_([models.Call.model_id, "Earkart Inbound Agent"]) )
            .filter(
                models.Call.user_id.in_([user_id, EARKART_INCOMING_ID]),
            )
            .all()
        )
        
        call_record = None
        for call_ in call_records:
            if call_.call_id == call_id:
                call_record = call_
                break

        if not call_record:
            raise HTTPException(status_code=403, detail="Call does not belong to the user")

        transcription_val = await get_transcript(call_id, db)
        if transcription_val is None:
            return JSONResponse({
                "transcription": "Waiting for Transcription to be available. Please try again after the call is over.",
                'entity': "Waiting for Transcription to be available. Please try again after the call is over.",
                "conversation_eval": "Waiting for Transcription to be available. Please try again after the call is over.",
                "summary": "Waiting for Transcription to be available. Please try again after the call is over."
            })
        
        elif transcription_val['transcript'] in ['Error fetching transcript', 'Transcript not found in S3', "Transcript is empty"]:
            return JSONResponse({
                "transcription": "Transcript is not available for further evaluations.",
                'entity': "Transcript is not available for further evaluations.",
                "conversation_eval": "Transcript is not available for further evaluations.",
                "summary": "Transcript is not available for further evaluations."
            })

        transcription_ = transcription_val['transcript']

        # Check if summary exists in db, else generate it
        if client in regenerate_summaries:
            summary_ = await call_summary(transcription_)
            if summary_.get("status_code") == 200:
                summary = summary_.get("summary")
                call_record.call_summary = summary
                db.commit()
            else:
                summary = "Error generating summary"
        else:
            if call_record.call_summary:
                summary = call_record.call_summary
            else:
                summary_ = await call_summary(transcription_)
                if summary_.get("status_code") == 200:
                    summary = summary_.get("summary")
                    call_record.call_summary = summary
                    db.commit()
                else:
                    summary = "Error generating summary"

        # Entity Extraction and conversation evaluation
        extractor_func = None
        field_list = None
        extractors_data = (extractors.get(client))
        if extractors_data:
            extractor_func = extractors_data.get("function")
            field_list = extractors_data.get("entities") if extractors_data.get("entities") is not None else None
        else:
            entity_extraction = "No extractor defined for this client"
            if client in need_conversation_eval:
                conversation_eva = call_record.call_conversation_quality if call_record.call_conversation_quality else {}
            else:
                conversation_eva = {}

            return JSONResponse({
                "transcription": transcription_,
                'entity': entity_extraction,
                "conversation_eval": conversation_eva,
                "summary": summary
            })
        
        if extractor_func is None:
            raise HTTPException(status_code=400, detail=f"No extractor defined for client: {client}")

        conversation_eva = None
        if client in skip_db_search:
            entity_extraction = await extractor_func(
                transcript=transcription_,
                fields=field_list
            )
            if client in need_conversation_eval:
                conversation_eva = await conversation_eval(transcript=transcription_)
            else:
                conversation_eva = {}

            call_record.call_conversation_quality = conversation_eva
            call_record.call_entity = entity_extraction
            db.commit()
        else:
            if call_record.call_conversation_quality and call_record.call_entity:
                if client in need_conversation_eval:
                    conversation_eva = call_record.call_conversation_quality
                else:
                    conversation_eva = {}
                entity_extraction = call_record.call_entity
            else:
                if client in need_conversation_eval:
                    conversation_eva = await conversation_eval(transcript=transcription_)
                else:
                   conversation_eva = {} 
                   
                entity_extraction = await extractor_func(
                    transcript=transcription_,
                    fields=field_list
                )
                
                call_record.call_conversation_quality = conversation_eva
                call_record.call_entity = entity_extraction
                db.commit()

        return JSONResponse({
            "transcription": transcription_,
            'entity': entity_extraction,
            "conversation_eval": conversation_eva,
            "summary": summary
        })

    except HTTPException:
        raise
    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in get_call_details: {e}")
        raise HTTPException(status_code=503, detail="Database connection issue, please try again")
    except Exception as e:
        logger.error(f"Error getting call details: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting call details: {str(e)}")

# ============================================================================
# MODEL MANAGEMENT APIS
# ============================================================================

@app.get("/api/models/{client}")
def get_models(client: str, request: Request, db: Session = Depends(get_database)):
    try:
        models_list = db.query(models.Model).filter(models.Model.client_name == client.upper()).all()
        return models_list
    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in get_models: {e}")
        raise HTTPException(status_code=503, detail="Database connection issue, please try again")
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting models: {str(e)}")

# ============================================================================
# FEEDBACK APIS
# ============================================================================

@app.post("/api/submit-feedback/")
def submit_feedback(feedback: FeedbackCreate, db: Session = Depends(get_database)):
    try:
        # Map felt_natural to felt_neutral in the database
        feedback_data = feedback.dict()
        if 'felt_natural' in feedback_data:
            feedback_data['felt_neutral'] = feedback_data.pop('felt_natural')
        
        new_feedback = models.Feedback(**feedback_data)
        db.add(new_feedback)
        db.commit()
        return {"message": "Feedback submitted successfully"}
    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in submit_feedback: {e}")
        db.rollback()
        raise HTTPException(status_code=503, detail="Database connection issue, please try again")
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

# ============================================================================
# DASHBOARD APIS
# ============================================================================

@app.get("/api/dashboard", response_model=DashboardResponse)
async def get_dashboard_data(
    user_id: int,
    client: str = "sbi",
    period: str = "7_days",
    db: Session = Depends(get_database)
):
    """Get dashboard data for a specific user and client with real database metrics"""
    
    if period not in ["7_days", "1_day"]:
        raise HTTPException(status_code=400, detail="Period must be '7_days' or '1_day'")
    
    try:
        dashboard_data = get_real_dashboard_metrics(db, user_id, client, period)
        return dashboard_data
        
    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in get_dashboard_data: {e}")
        return generate_fallback_dashboard_data(period)
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return generate_fallback_dashboard_data(period)

@app.get("/api/dashboard/summary")
async def get_dashboard_summary(
    user_id: int, 
    client: str = "sbi", 
    db: Session = Depends(get_database)
):
    """Get a quick summary of dashboard metrics with real database data"""
    
    try:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        today_calls_query = db.query(models.Call).filter(
            models.Call.user_id == user_id,
            models.Call.call_started_at >= today
        )
        
        yesterday_calls_query = db.query(models.Call).filter(
            models.Call.user_id == user_id,
            models.Call.call_started_at >= yesterday,
            models.Call.call_started_at < today
        )
        
        if client.upper() != "ALL":
            today_calls_query = today_calls_query.join(models.Model).filter(
                models.Model.client_name == client.upper()
            )
            yesterday_calls_query = yesterday_calls_query.join(models.Model).filter(
                models.Model.client_name == client.upper()
            )
        
        today_calls_count = today_calls_query.count()
        yesterday_calls_count = yesterday_calls_query.count()
        
        if yesterday_calls_count > 0:
            growth_rate = round(((today_calls_count - yesterday_calls_count) / yesterday_calls_count * 100), 1)
        else:
            growth_rate = 100 if today_calls_count > 0 else 0
        
        today_calls = today_calls_query.all()
        hourly_counts = {}
        total_response_times = []
        
        for call in today_calls:
            hour = call.call_started_at.hour
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
            
            if call.call_duration and call.call_duration > 0:
                response_time = min(call.call_duration * 0.1, 10)
                total_response_times.append(response_time)
        
        peak_hour = max(hourly_counts.keys()) if hourly_counts else 12
        avg_response_time = round(sum(total_response_times) / len(total_response_times), 1) if total_response_times else 3.0
        
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        most_active_day = days_of_week[datetime.now().weekday()]
        
        return {
            "today_calls": today_calls_count,
            "yesterday_calls": yesterday_calls_count,
            "growth_rate": growth_rate,
            "peak_hour": f"{peak_hour:02d}:00",
            "most_active_day": most_active_day,
            "avg_response_time": f"{avg_response_time} seconds"
        }
        
    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in get_dashboard_summary: {e}")
        today_calls = random.randint(25, 60)
        yesterday_calls = random.randint(20, 55)
        growth_rate = round(((today_calls - yesterday_calls) / yesterday_calls * 100), 1) if yesterday_calls > 0 else 0
        
        return {
            "today_calls": today_calls,
            "yesterday_calls": yesterday_calls,
            "growth_rate": growth_rate,
            "peak_hour": f"{random.randint(9, 17)}:00",
            "most_active_day": "Tuesday",
            "avg_response_time": f"{random.randint(2, 8)} seconds"
        }
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        return {
            "today_calls": 45,
            "yesterday_calls": 38,
            "growth_rate": 18.4,
            "peak_hour": "14:00",
            "most_active_day": "Tuesday",
            "avg_response_time": "4.2 seconds"
        }

# ============================================================================
# CHAT APIS (For Floating Widget)
# ============================================================================

@app.post("/api/trigger-chat/", response_model=ChatResponse)
async def create_chat_session(fastapi_request: Request, db: Session = Depends(get_database)):
    """Create a LiveKit chat session with the provided customer details"""
    try:
        request_body = await fastapi_request.json()
        print(f"Chat request body: {request_body}")

        from utils.call import run_livekit_dispatch
        
        agent_id = request_body.get('agent_id', 'chat_agent_1')
        
        model = db.query(models.Model).filter(models.Model.model_id == agent_id).first()
        if not model:
            model = models.Model(
                model_id="chat_agent_1",
                model_name="Chat Assistant",
                client_name=client_name.upper()
            )
            db.add(model)
            db.commit()
            db.refresh(model)
            
        metadata_ = {
            "name": request_body['name'],
            "modality": "chat",
            "agent_name": model.model_name,
            "user_id": request_body.get('user_id'),
            "session_id": request_body.get('session_id', f"chat_{request_body['user_id']}_{datetime.now().timestamp()}")
        }
        
        result = run_livekit_dispatch(
            metadata=metadata_,
            contact_number="chat_session",
            agent_name=model.model_name,
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        import re
        room_match = re.search(r'room:"(.*?)"', result["output"])
        room_id = room_match.group(1) if room_match else None
        
        new_chat = models.Call(
            user_id=int(request_body['user_id']),
            call_id=room_id,
            name=request_body['name'],
            call_to="chat_session",
            call_from="chat_user",
            call_type="Chat",
            model_id=model.model_id,
            call_transcription=f"{BASE_URL}/api/transcript/{room_id}",
            call_recording_url=f"{BASE_URL}/api/chat-log/{room_id}",
            call_duration=0,
        )
        
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        
        response_data = ChatResponse(
            success=result["success"],
            message="Chat session created successfully",
            output=result.get("output"),
            room_id=room_id,
            chat_db_id=new_chat.id
        )
        
        return response_data
        
    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in create_chat_session: {e}")
        db.rollback()
        raise HTTPException(status_code=503, detail="Database connection issue, please try again")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating chat session: {str(e)}")

@app.post("/api/get-chat-token/")
async def get_chat_token(fastapi_request: Request):
    """Generate LiveKit access token for chat sessions"""
    try:
        request_body = await fastapi_request.json()
        room_id = request_body.get('room_id')
        user_name = request_body.get('user_name', 'Chat User')
        
        if not room_id:
            raise HTTPException(status_code=400, detail="room_id is required")
        
        token = api.AccessToken(
            api_key=os.getenv("LIVEKIT_API_KEY", "APIoLr2sRCRJWY5"),
            api_secret=os.getenv("LIVEKIT_API_SECRET", "yE3wUkoQxjWjhteMAed9ubm5mYg3iOfPT6qBQfffzgJC")
        )
        
        token.with_identity(f"chat_user_{user_name}")
        token.with_name(user_name)
        
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_id,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        ))
        
        token.with_ttl(timedelta(hours=1))
        
        jwt_token = token.to_jwt()
        
        return {
            "success": True,
            "token": jwt_token,
            "room_id": room_id
        }
        
    except Exception as e:
        logger.error(f"Error generating chat token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")

@app.get("/api/chat-history/{user_id}/{client_name}")
async def get_chat_history(user_id: int, client_name: str, db: Session = Depends(get_database)):
    """Get chat history for a user (filter for Chat type calls)"""
    try:
        chat_history = db.query(models.Call).filter(
            models.Call.user_id == user_id,
            models.Call.call_type == "Chat"
        ).all()
        
        curated_response = []
        for chat in chat_history:
            updated_chat = {}
            
            updated_chat['Name'] = {'name': chat.name}
            updated_chat['Start_time'] = chat.call_started_at
            updated_chat['End_time'] = chat.call_ended_at if chat.call_ended_at else chat.call_started_at
            updated_chat['chat_log_api'] = f"{BASE_URL}/api/chat-log/{chat.call_id}"
            updated_chat['chat_details'] = f"{BASE_URL}/api/call_details/{client_name}/{user_id}/{chat.call_id}"
            updated_chat['session_type'] = "Chat"
            updated_chat['chat_status'] = chat.call_status if hasattr(chat, 'call_status') else "completed"
            updated_chat['duration_ms'] = chat.call_duration if chat.call_duration else 0
            
            curated_response.append(updated_chat)

        reversed_list = curated_response[::-1]
        return reversed_list
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@app.get("/api/sessions/{user_id}/{client_name}")
async def get_all_sessions(user_id: int, client_name: str, db: Session = Depends(get_database)):
    """Get both call history and chat history combined"""
    try:
        all_sessions = db.query(models.Call).filter(models.Call.user_id == user_id).all()
        
        curated_response = []
        for session in all_sessions:
            updated_session = {}
            
            updated_session['Name'] = {'name': session.name}
            updated_session['Start_time'] = session.call_started_at
            updated_session['End_time'] = session.call_ended_at if session.call_ended_at else session.call_started_at
            updated_session['session_type'] = session.call_type
            updated_session['status'] = getattr(session, 'call_status', 'completed')
            updated_session['duration_ms'] = session.call_duration if session.call_duration else 0
            
            if session.call_type == "Chat":
                updated_session['log_api'] = f"{BASE_URL}/api/chat-log/{session.call_id}"
            else:
                updated_session['log_api'] = f"{BASE_URL}/api/transcript/{session.call_id}"
                
            updated_session['details'] = f"{BASE_URL}/api/call_details/{client_name}/{user_id}/{session.call_id}"
            
            curated_response.append(updated_session)

        reversed_list = curated_response[::-1]
        return reversed_list
        
    except Exception as e:
        logger.error(f"Error fetching session history: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching session history: {str(e)}")

# ============================================================================
# HEALTH CHECK APIS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "online", "service": "LiveKit Dispatch API with Dashboard"}

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint that shows database configuration"""
    try:
        db = next(get_database())
        db.execute(text("SELECT 1"))
        db_status = "connected"
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "online", 
        "service": "LiveKit Dispatch API with Dashboard",
        "database_type": DB_TYPE,
        "database_status": db_status,
        "database_url_host": os.getenv("POSTGRES_URL", SQLITE_DB_PATH).split('@')[1].split('/')[0] if DB_TYPE == "postgresql" and os.getenv("POSTGRES_URL") else "SQLite"
    }

##################################################################################################
# HELPER FUNCTIONS
##################################################################################################

def get_real_dashboard_metrics(db: Session, user_id: int, client: str, period: str) -> DashboardResponse:
    """Generate real dashboard metrics from database"""
    try:
        end_date = datetime.now()
        if period == "1_day":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_format = "%H:%M"
        else:  # 7_days
            start_date = end_date - timedelta(days=7)
            date_format = "%Y-%m-%d"

        calls_query = db.query(models.Call).filter(
            models.Call.user_id == user_id,
            models.Call.call_started_at >= start_date,
            models.Call.call_started_at <= end_date
        )

        if client.upper() != "ALL":
            calls_query = calls_query.join(models.Model).filter(
                models.Model.client_name == client.upper()
            )

        calls = calls_query.all()

        total_calls = len(calls)
        total_leads = len([call for call in calls if call.call_entity and call.call_entity != {}])
        conversion_rate = round((total_leads / total_calls * 100) if total_calls > 0 else 0, 2)
        
        valid_durations = [call.call_duration for call in calls if call.call_duration and call.call_duration > 0]
        avg_call_duration = round(sum(valid_durations) / len(valid_durations), 1) if valid_durations else 0

        trends = []
        if period == "1_day":
            for hour in range(24):
                hour_start = start_date + timedelta(hours=hour)
                hour_end = hour_start + timedelta(hours=1)
                
                hour_calls = [call for call in calls if hour_start <= call.call_started_at < hour_end]
                hour_leads = [call for call in hour_calls if call.call_entity and call.call_entity != {}]
                hour_durations = [call.call_duration for call in hour_calls if call.call_duration and call.call_duration > 0]
                
                trends.append(TrendData(
                    date=hour_start.strftime(date_format),
                    calls=len(hour_calls),
                    leads=len(hour_leads),
                    duration=round(sum(hour_durations) / len(hour_durations), 1) if hour_durations else 0
                ))
        else:
            for i in range(7):
                day_start = start_date + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                day_calls = [call for call in calls if day_start <= call.call_started_at < day_end]
                day_leads = [call for call in day_calls if call.call_entity and call.call_entity != {}]
                day_durations = [call.call_duration for call in day_calls if call.call_duration and call.call_duration > 0]
                
                trends.append(TrendData(
                    date=day_start.strftime(date_format),
                    calls=len(day_calls),
                    leads=len(day_leads),
                    duration=round(sum(day_durations) / len(day_durations), 1) if day_durations else 0
                ))

        metrics = DashboardMetrics(
            total_calls=total_calls,
            total_leads=total_leads,
            conversion_rate=conversion_rate,
            avg_call_duration=avg_call_duration
        )

        return DashboardResponse(
            metrics=metrics,
            call_trends=trends,
            lead_trends=trends,
            period=period
        )

    except Exception as e:
        logger.error(f"Error generating dashboard metrics: {e}")
        return generate_fallback_dashboard_data(period)

def generate_fallback_dashboard_data(period: str) -> DashboardResponse:
    """Generate fallback dummy data if database queries fail"""
    if period == "1_day":
        trends = []
        total_calls = 0
        total_leads = 0
        total_duration = 0
        
        for hour in range(24):
            if 9 <= hour <= 17:
                calls = random.randint(15, 45)
                leads = random.randint(3, 12)
            elif 8 <= hour <= 20:
                calls = random.randint(5, 20)
                leads = random.randint(1, 6)
            else:
                calls = random.randint(0, 8)
                leads = random.randint(0, 2)
            
            duration = round(random.uniform(120, 400), 1)
            total_calls += calls
            total_leads += leads
            total_duration += duration
            
            trends.append(TrendData(
                date=f"{hour:02d}:00",
                calls=calls,
                leads=leads,
                duration=duration
            ))
        
        avg_duration = round(total_duration / 24, 1)
    else:
        trends = []
        total_calls = 0
        total_leads = 0
        total_duration = 0
        
        for i in range(7):
            date = datetime.now() - timedelta(days=6-i)
            calls = random.randint(80, 200)
            leads = random.randint(15, 50)
            duration = round(random.uniform(180, 350), 1)
            
            if date.weekday() >= 5:
                calls = int(calls * 0.6)
                leads = int(leads * 0.6)
            
            total_calls += calls
            total_leads += leads
            total_duration += duration
            
            trends.append(TrendData(
                date=date.strftime("%Y-%m-%d"),
                calls=calls,
                leads=leads,
                duration=duration
            ))
        
        avg_duration = round(total_duration / 7, 1)

    conversion_rate = round((total_leads / total_calls * 100) if total_calls > 0 else 0, 2)
    
    metrics = DashboardMetrics(
        total_calls=total_calls,
        total_leads=total_leads,
        conversion_rate=conversion_rate,
        avg_call_duration=avg_duration
    )

    return DashboardResponse(
        metrics=metrics,
        call_trends=trends,
        lead_trends=trends,
        period=period
    )

##################################################################################################
# LESS USED APIS (Commented for reference)
##################################################################################################


# Model Creation API (rarely used)
@app.post("/api/models/")
def create_model(model: ModelCreate, db: Session = Depends(get_database)):
    try:
        new_model = models.Model(**model.dict())
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        return new_model
    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in create_model: {e}")
        db.rollback()
        raise HTTPException(status_code=503, detail="Database connection issue, please try again")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating model: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating model: {str(e)}")

# Model Update API (rarely used)
@app.put("/api/models/{model_id}")
def update_model(model_id: str, updated_model: ModelUpdate, db: Session = Depends(get_database)):
    try:
        db_model = db.query(models.Model).filter(models.Model.model_id == model_id).first()
        if not db_model:
            raise HTTPException(status_code=404, detail="Model not found")

        for key, value in updated_model.dict(exclude_unset=True).items():
            setattr(db_model, key, value)

        db.commit()
        db.refresh(db_model)
        return db_model
    except HTTPException:
        raise
    except (OperationalError, DisconnectionError) as e:
        logger.warning(f"Database connection issue in update_model: {e}")
        db.rollback()
        raise HTTPException(status_code=503, detail="Database connection issue, please try again")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating model: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating model: {str(e)}")

# Chat Log API (alternative to transcript for chat sessions)
@app.get("/api/chat-log/{call_id}")
async def get_chat_log(call_id: str, db: Session = Depends(get_database)):
    try:
        chat = db.query(models.Call).filter(models.Call.call_id == call_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat session with ID {call_id} not found")
        
        return await get_transcript(call_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        return {"chat_log": "Error retrieving chat log", "status_code": 500, "function": "get_chat_log", "error": str(e)}

# Advanced Floating Chat APIs (for future use)
# These are more complex chat session management APIs that might be used later

class FloatingChatResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    session_id: Optional[str] = None
    room_id: Optional[str] = None
    participant_id: Optional[str] = None
    token: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    session_id: str
    customer_name: str
    agent_name: str
    started_at: datetime
    ended_at: Optional[datetime]
    status: str
    message_count: int
    last_message_preview: Optional[str]

class FloatingChatRequest(BaseModel):
    user_id: str
    customer_name: str = Field(..., description="Customer name")
    agent_id: str = Field(default="chat_agent_1", description="Agent ID for chat")


##################################################################################################
# APP STARTUP
##################################################################################################

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1234)