from datetime import datetime
from pydantic import BaseModel, Field
from pydantic import BaseModel, EmailStr, Field

from .models import QRPurpose, SubmissionRound, UserRole, VerificationStatus


class UserSignup(BaseModel):
    name: str
    email: str = Field(min_length=5, max_length=255)
    phone: str
    password: str = Field(min_length=6, max_length=128)
    role: UserRole = UserRole.STUDENT


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserCreate(BaseModel):
    name: str
    email: str = Field(min_length=5, max_length=255)
    email: EmailStr
    phone: str
    role: UserRole = UserRole.STUDENT


class OTPVerify(BaseModel):
    user_id: int
    otp: str = Field(min_length=6, max_length=6)


class DocumentUpload(BaseModel):
    college_id_path: str
    aadhaar_masked: str
    selfie_path: str


class VerificationAction(BaseModel):
    status: VerificationStatus


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    role: UserRole
    verification_status: VerificationStatus
    otp_verified: bool

    class Config:
        from_attributes = True


class HackathonCreate(BaseModel):
    title: str
    description: str
    registration_deadline: datetime
    round1_deadline: datetime
    final_deadline: datetime


class ProblemStatementCreate(BaseModel):
    title: str
    description: str


class TeamCreate(BaseModel):
    hackathon_id: int
    name: str
    captain_id: int
    member_ids: list[int]
    problem_statement_id: int


class SubmissionCreate(BaseModel):
    team_id: int
    round: SubmissionRound
    ppt_link: str
    github_link: str | None = None
    demo_video_link: str | None = None


class CriterionCreate(BaseModel):
    hackathon_id: int
    round: SubmissionRound
    name: str
    weight: float


class ScoreCreate(BaseModel):
    team_id: int
    round: SubmissionRound
    judge_id: int
    criterion_id: int
    score: float


class QRGenerate(BaseModel):
    user_id: int
    hackathon_id: int
    purpose: QRPurpose
    valid_from: datetime
    valid_to: datetime


class ScanRequest(BaseModel):
    token: str
    scanner_id: int


class LeaderboardRow(BaseModel):
    team_id: int
    team_name: str
    total_score: float
