from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any
from datetime import datetime

class ActionItemBase(BaseModel):
    task: str
    owner: Optional[str] = None
    deadline_text: Optional[str] = None
    completed: bool = False

class ActionItemCreate(ActionItemBase):
    pass

class ActionItemResponse(ActionItemBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ActionItemUpdate(BaseModel):
    task: Optional[str] = None
    owner: Optional[str] = None
    deadline_text: Optional[str] = None
    completed: Optional[bool] = None

class LLMStructuredOutput(BaseModel):
    title: str = Field(description="Clear and concise title for the notes")
    summary: str = Field(description="Comprehensive summary of what was discussed")
    key_points: List[str] = Field(default_factory=list, description="Bulleted key points and takeaways")
    action_items: List[ActionItemBase] = Field(default_factory=list, description="Actionable tasks with owner/deadline if mentioned")
    keywords: List[str] = Field(default_factory=list, description="Relevant tags/keywords")

class NoteResponse(BaseModel):
    id: str
    transcript_id: str
    title: str
    summary: str
    content_json: Any
    created_at: datetime
    updated_at: datetime
    action_items: List[ActionItemResponse] = []
    model_config = ConfigDict(from_attributes=True)

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content_json: Optional[Any] = None

class GenerateNotesRequest(BaseModel):
    transcript_id: str
    custom_instructions: Optional[str] = None
