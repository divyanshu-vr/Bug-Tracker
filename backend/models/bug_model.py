from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Type
from datetime import datetime, timezone
from enum import Enum


def validate_enum_field(value, enum_class: Type[Enum], field_name: str):
    """
    Reusable enum validator for Pydantic models.
    
    Args:
        value: The value to validate
        enum_class: The Enum class to validate against
        field_name: Name of the field for error messages
        
    Returns:
        The validated enum value
        
    Raises:
        ValueError: If the value is not a valid enum member
    """
    if isinstance(value, str):
        try:
            return enum_class(value)
        except ValueError:
            valid_values = ', '.join([e.value for e in enum_class])
            raise ValueError(f"Invalid {field_name}. Must be one of: {valid_values}")
    return value


class BugStatus(str, Enum):
    """Valid bug status values"""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class BugPriority(str, Enum):
    """Valid bug priority levels"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class BugSeverity(str, Enum):
    """Valid bug severity levels"""
    MINOR = "Minor"
    MAJOR = "Major"
    BLOCKER = "Blocker"


class Bug(BaseModel):
    """
    Bug entity model with validation rules.
    Represents a bug report in the system.
    """
    id: Optional[str] = Field(None, alias="_id")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    projectId: str = Field(..., min_length=1)
    reportedBy: str = Field(..., min_length=1)
    assignedTo: Optional[str] = None
    status: BugStatus = Field(default=BugStatus.OPEN)
    priority: BugPriority
    severity: BugSeverity
    tags: List[str] = Field(default_factory=list)
    validated: bool = Field(default=False)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status is a valid enum value"""
        return validate_enum_field(v, BugStatus, 'status')

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate priority is a valid enum value"""
        return validate_enum_field(v, BugPriority, 'priority')

    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        """Validate severity is a valid enum value"""
        return validate_enum_field(v, BugSeverity, 'severity')


class Comment(BaseModel):
    """
    Comment entity model.
    Represents a comment on a bug.
    """
    id: Optional[str] = Field(None, alias="_id")
    bugId: str = Field(..., min_length=1)
    authorId: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @field_validator('createdAt')
    @classmethod
    def validate_created_at(cls, v):
        """Ensure createdAt is not in the future"""
        if v > datetime.now(timezone.utc):
            raise ValueError("createdAt cannot be in the future")
        return v


class Project(BaseModel):
    """
    Project entity model.
    Represents a project in the system.
    """
    id: Optional[str] = Field(None, alias="_id")
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    createdBy: str = Field(..., min_length=1)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ActivityLog(BaseModel):
    """
    Activity log entity model.
    Represents an activity log entry tracking actions performed on bugs.
    """
    id: Optional[str] = Field(None, alias="_id")
    bugId: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    performedBy: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class User(BaseModel):
    """
    User entity model.
    
    Note: Users are predefined in Collection DB with roles.
    This model is used for validation only. No user creation or modification.
    """
    id: Optional[str] = Field(None, alias="_id")
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)  # e.g., "admin", "developer", "tester"
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Request Models

class BugCreateRequest(BaseModel):
    """Request model for creating a new bug"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    projectId: str = Field(..., min_length=1)
    reportedBy: str = Field(..., min_length=1)
    priority: BugPriority
    severity: BugSeverity


class BugStatusUpdateRequest(BaseModel):
    """Request model for updating bug status"""
    status: BugStatus
    userId: str = Field(..., min_length=1)  # User making the change
    userRole: str = Field(..., min_length=1)  # Role for validation

    @field_validator('status')
    @classmethod
    def validate_status_transition(cls, v):
        """Validate status is a valid enum value"""
        return validate_enum_field(v, BugStatus, 'status')


class BugAssignRequest(BaseModel):
    """Request model for assigning a bug to a user"""
    assignedTo: str = Field(..., min_length=1)
    assignedBy: str = Field(..., min_length=1)


class CommentCreateRequest(BaseModel):
    """Request model for creating a comment"""
    bugId: str = Field(..., min_length=1)
    authorId: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


# Response Models

class BugResponse(BaseModel):
    """Response model for bug data"""
    id: str = Field(..., alias="_id")
    title: str
    description: str
    projectId: str
    reportedBy: str
    assignedTo: Optional[str] = None
    status: str
    priority: str
    severity: str
    tags: List[str]
    validated: bool
    createdAt: datetime
    updatedAt: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CommentResponse(BaseModel):
    """Response model for comment data"""
    id: str = Field(..., alias="_id")
    bugId: str
    authorId: str
    message: str
    createdAt: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProjectResponse(BaseModel):
    """Response model for project data"""
    id: str = Field(..., alias="_id")
    name: str
    description: str
    createdBy: str
    createdAt: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BugWithCommentsResponse(BaseModel):
    """Response model for bug with associated comments"""
    bug: BugResponse
    comments: List[CommentResponse]


class StatusUpdateResponse(BaseModel):
    """Response model for status update operations"""
    success: bool
    message: str
    bug: Optional[BugResponse] = None


class AssignmentResponse(BaseModel):
    """Response model for assignment operations"""
    success: bool
    message: str
    bug: Optional[BugResponse] = None
