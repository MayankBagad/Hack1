from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserRole(str, Enum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"
    JUDGE = "JUDGE"
    SCANNER = "SCANNER"


class VerificationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SubmissionRound(str, Enum):
    ROUND1 = "ROUND1"
    FINAL = "FINAL"


class SubmissionStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    LOCKED = "LOCKED"


class QRPurpose(str, Enum):
    ENTRY = "ENTRY"
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    DINNER = "DINNER"


class QRStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), default=UserRole.STUDENT)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SqlEnum(VerificationStatus), default=VerificationStatus.PENDING
    )
    otp_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    college_id_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    aadhaar_masked: Mapped[str | None] = mapped_column(String(32), nullable=True)
    selfie_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Hackathon(Base):
    __tablename__ = "hackathons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text)
    registration_deadline: Mapped[datetime] = mapped_column(DateTime)
    round1_deadline: Mapped[datetime] = mapped_column(DateTime)
    final_deadline: Mapped[datetime] = mapped_column(DateTime)


class ProblemStatement(Base):
    __tablename__ = "problem_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    captain_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    problem_statement_id: Mapped[int] = mapped_column(ForeignKey("problem_statements.id"))


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("team_id", "round", name="uq_team_round"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    round: Mapped[SubmissionRound] = mapped_column(SqlEnum(SubmissionRound), index=True)
    ppt_link: Mapped[str] = mapped_column(String(255))
    github_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    demo_video_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[SubmissionStatus] = mapped_column(SqlEnum(SubmissionStatus), default=SubmissionStatus.SUBMITTED)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EvaluationCriterion(Base):
    __tablename__ = "evaluation_criteria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"), index=True)
    round: Mapped[SubmissionRound] = mapped_column(SqlEnum(SubmissionRound), index=True)
    name: Mapped[str] = mapped_column(String(120))
    weight: Mapped[float] = mapped_column(Float)


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    round: Mapped[SubmissionRound] = mapped_column(SqlEnum(SubmissionRound), index=True)
    judge_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    criterion_id: Mapped[int] = mapped_column(ForeignKey("evaluation_criteria.id"), index=True)
    score: Mapped[float] = mapped_column(Float)


class QRToken(Base):
    __tablename__ = "qr_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id"), index=True)
    purpose: Mapped[QRPurpose] = mapped_column(SqlEnum(QRPurpose), index=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime)
    valid_to: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[QRStatus] = mapped_column(SqlEnum(QRStatus), default=QRStatus.ACTIVE)


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    qr_token_id: Mapped[int] = mapped_column(ForeignKey("qr_tokens.id"), index=True)
    scanner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    scanned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    success: Mapped[bool] = mapped_column(Boolean)
    message: Mapped[str] = mapped_column(String(255))
