# models.py
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict

class Experience(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None

class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    years: Optional[str] = None

class ResumeInfo(BaseModel):
    """Pydantic model for structured Resume data."""
    candidate_name: Optional[str] = Field(None, description="Full name of the candidate")
    email: Optional[EmailStr] = Field(None, description="Email address of the candidate")
    phone: Optional[str] = Field(None, description="Phone number of the candidate")
    summary: Optional[str] = Field(None, description="Professional summary or objective")
    skills: List[str] = Field([], description="List of skills")
    experience: List[Experience] = Field([], description="List of work experiences")
    education: List[Education] = Field([], description="List of educational qualifications")
    misc: Optional[Dict] = Field({}, description="Any other relevant extracted information")

class JobDescriptionInfo(BaseModel):
    """Pydantic model for structured Job Description data."""
    job_title: str = Field(..., description="The title of the job")
    company: Optional[str] = Field(None, description="Company name (if available)")
    location: Optional[str] = Field(None, description="Job location (if available)")
    summary: Optional[str] = Field(None, description="Brief summary of the role")
    responsibilities: List[str] = Field([], description="List of key responsibilities")
    required_skills: List[str] = Field([], description="List of mandatory skills")
    preferred_skills: List[str] = Field([], description="List of desired but not mandatory skills")
    required_experience: Optional[str] = Field(None, description="Minimum years/type of experience required")
    required_education: Optional[str] = Field(None, description="Minimum education level required")
    misc: Optional[Dict] = Field({}, description="Other details like salary range, benefits etc.")