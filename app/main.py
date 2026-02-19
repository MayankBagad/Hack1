from collections import defaultdict
from datetime import datetime, timedelta
import hashlib
import logging
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import logging
import secrets

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import secrets

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import Base, EFFECTIVE_DATABASE_URL, engine, get_db
from .models import (
    AuthSession,

from .models import (
    EvaluationCriterion,
    Hackathon,
    ProblemStatement,
    QRStatus,
    QRToken,
    QRPurpose,
    ScanLog,
    Score,
    Submission,
    SubmissionRound,
    SubmissionStatus,
    Team,
    TeamMember,
    User,
    UserRole,
    VerificationStatus,
)
from .schemas import (
    AuthResponse,
    CriterionCreate,
    DocumentUpload,
    HackathonCreate,
    LeaderboardRow,
    LoginRequest,
    OTPVerify,
    ProblemStatementCreate,
    QRGenerate,
    ScanRequest,
    ScoreCreate,
    SubmissionCreate,
    TeamCreate,
    UserOut,
    UserSignup,
    VerificationAction,
)

app = FastAPI(title="College Hackathon Management API", version="0.2.0")
app.mount("/assets", StaticFiles(directory="frontend"), name="assets")
logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _issue_token(db: Session, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    session = AuthSession(user_id=user_id, token=token, expires_at=datetime.utcnow() + timedelta(days=7))
    db.add(session)
    db.commit()
    return token


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.replace("Bearer ", "", 1)
    session = db.query(AuthSession).filter(AuthSession.token == token).first()
    if not session or session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_roles(*roles: UserRole):
    def checker(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permission")
        return user

    return checker
    UserCreate,
    UserOut,
    VerificationAction,
)

app = FastAPI(title="College Hackathon Management API", version="0.1.0")
app.mount("/assets", StaticFiles(directory="frontend"), name="assets")


logger = logging.getLogger(__name__)


@app.on_event("startup")
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        app.state.db_ready = True
        app.state.startup_error = None
    except Exception as exc:
        app.state.db_ready = False
        app.state.startup_error = str(exc)
        logger.exception("Database initialization failed during startup")


@app.get("/", include_in_schema=False)
def root():
    return FileResponse("frontend/index.html")

@app.get("/")
def root():
    return {
        "message": "College Hackathon Management API",
        "health": "/health",
        "docs": "/docs",
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok" if getattr(app.state, "db_ready", False) else "degraded",
        "db_ready": getattr(app.state, "db_ready", False),
        "database_backend": EFFECTIVE_DATABASE_URL.split(":", 1)[0],
        "startup_error": getattr(app.state, "startup_error", None),
    }


@app.post("/auth/signup", response_model=UserOut)
def signup(payload: UserSignup, db: Session = Depends(get_db)):
    if db.query(User).filter((User.email == payload.email) | (User.phone == payload.phone)).first():
        raise HTTPException(status_code=400, detail="User with email/phone already exists")
    user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        role=payload.role,
        password_hash=_hash_password(payload.password),
    )
@app.post("/auth/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter((User.email == payload.email) | (User.phone == payload.phone)).first():
        raise HTTPException(status_code=400, detail="User with email/phone already exists")
    user = User(**payload.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or user.password_hash != _hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = _issue_token(db, user.id)
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@app.post("/auth/verify-otp", response_model=UserOut)
def verify_otp(payload: OTPVerify, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
@app.post("/auth/verify-otp", response_model=UserOut)
def verify_otp(payload: OTPVerify, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.otp != "123456":
        raise HTTPException(status_code=400, detail="Invalid OTP")
    user.otp_verified = True
    db.commit()
    db.refresh(user)
    return user


@app.post("/verification/upload-documents", response_model=UserOut)
def upload_documents(payload: DocumentUpload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
def upload_documents(user_id: int, payload: DocumentUpload, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.college_id_path = payload.college_id_path
    user.aadhaar_masked = payload.aadhaar_masked
    user.selfie_path = payload.selfie_path
    db.commit()
    db.refresh(user)
    return user


@app.post("/verification/face-match")
def face_match(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user = db.get(User, user.id)
    if not user.college_id_path or not user.selfie_path:
        raise HTTPException(status_code=400, detail="Upload documents first")
    return {"user_id": user.id, "face_match": True, "score": 0.93}


@app.patch("/admin/verification/{user_id}", response_model=UserOut)
def admin_verify(
    user_id: int,
    payload: VerificationAction,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
def face_match(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.college_id_path or not user.selfie_path:
        raise HTTPException(status_code=400, detail="Upload documents first")
    return {"user_id": user_id, "face_match": True, "score": 0.93}


@app.patch("/admin/verification/{user_id}", response_model=UserOut)
def admin_verify(user_id: int, payload: VerificationAction, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.verification_status = payload.status
    db.commit()
    db.refresh(user)
    return user


@app.post("/admin/hackathons")
def create_hackathon(
    payload: HackathonCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
def create_hackathon(payload: HackathonCreate, db: Session = Depends(get_db)):
    hackathon = Hackathon(**payload.model_dump())
    db.add(hackathon)
    db.commit()
    db.refresh(hackathon)
    return hackathon


@app.post("/admin/hackathons/{hackathon_id}/problem-statements")
def add_problem_statement(
    hackathon_id: int,
    payload: ProblemStatementCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
def add_problem_statement(hackathon_id: int, payload: ProblemStatementCreate, db: Session = Depends(get_db)):
    if not db.get(Hackathon, hackathon_id):
        raise HTTPException(status_code=404, detail="Hackathon not found")
    ps = ProblemStatement(hackathon_id=hackathon_id, **payload.model_dump())
    db.add(ps)
    db.commit()
    db.refresh(ps)
    return ps


@app.post("/teams")
def create_team(payload: TeamCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.id != payload.captain_id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Can create only your own team")
def create_team(payload: TeamCreate, db: Session = Depends(get_db)):
    if not db.get(Hackathon, payload.hackathon_id):
        raise HTTPException(status_code=404, detail="Hackathon not found")
    captain = db.get(User, payload.captain_id)
    if not captain or captain.verification_status != VerificationStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Captain must be verified")

    team = Team(
        hackathon_id=payload.hackathon_id,
        name=payload.name,
        captain_id=payload.captain_id,
        problem_statement_id=payload.problem_statement_id,
    )
    db.add(team)
    db.flush()

    all_members = set(payload.member_ids + [payload.captain_id])
    for member_id in all_members:
        member = db.get(User, member_id)
        if not member or member.verification_status != VerificationStatus.APPROVED:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Member {member_id} not verified")
        db.add(TeamMember(team_id=team.id, user_id=member_id))
    for user_id in all_members:
        user = db.get(User, user_id)
        if not user or user.verification_status != VerificationStatus.APPROVED:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Member {user_id} not verified")
        db.add(TeamMember(team_id=team.id, user_id=user_id))

    db.commit()
    db.refresh(team)
    return team


def _ensure_submission_allowed(db: Session, team_id: int, round_name: SubmissionRound):
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    hackathon = db.get(Hackathon, team.hackathon_id)
    now = datetime.utcnow()
    deadline = hackathon.round1_deadline if round_name == SubmissionRound.ROUND1 else hackathon.final_deadline
    if now > deadline:
        raise HTTPException(status_code=400, detail="Submission deadline passed")


@app.post("/submissions")
def create_submission(payload: SubmissionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_submission_allowed(db, payload.team_id, payload.round)
    team = db.get(Team, payload.team_id)
    if user.role != UserRole.ADMIN and user.id != team.captain_id:
        raise HTTPException(status_code=403, detail="Only captain can submit")

    existing = db.query(Submission).filter(Submission.team_id == payload.team_id, Submission.round == payload.round).first()
def create_submission(payload: SubmissionCreate, db: Session = Depends(get_db)):
    _ensure_submission_allowed(db, payload.team_id, payload.round)

    existing = (
        db.query(Submission)
        .filter(Submission.team_id == payload.team_id, Submission.round == payload.round)
        .first()
    )
    if existing and existing.status == SubmissionStatus.LOCKED:
        raise HTTPException(status_code=400, detail="Submission is locked")

    if existing:
        existing.ppt_link = payload.ppt_link
        existing.github_link = payload.github_link
        existing.demo_video_link = payload.demo_video_link
        existing.submitted_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    submission = Submission(**payload.model_dump())
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@app.post("/admin/submissions/lock")
def lock_submissions(
    round_name: SubmissionRound,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    updated = db.query(Submission).filter(Submission.round == round_name).update(
        {Submission.status: SubmissionStatus.LOCKED}, synchronize_session=False
def lock_submissions(round_name: SubmissionRound, db: Session = Depends(get_db)):
    updated = (
        db.query(Submission)
        .filter(Submission.round == round_name)
        .update({Submission.status: SubmissionStatus.LOCKED}, synchronize_session=False)
    )
    db.commit()
    return {"locked_count": updated}


@app.post("/admin/evaluation-criteria")
def add_criterion(
    payload: CriterionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
def add_criterion(payload: CriterionCreate, db: Session = Depends(get_db)):
    criterion = EvaluationCriterion(**payload.model_dump())
    db.add(criterion)
    db.commit()
    db.refresh(criterion)
    return criterion


@app.post("/judge/scores")
def submit_score(payload: ScoreCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in (UserRole.JUDGE, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Judge role required")
def submit_score(payload: ScoreCreate, db: Session = Depends(get_db)):
    judge = db.get(User, payload.judge_id)
    if not judge or judge.role != UserRole.JUDGE:
        raise HTTPException(status_code=400, detail="Judge role required")
    criterion = db.get(EvaluationCriterion, payload.criterion_id)
    if not criterion or criterion.round != payload.round:
        raise HTTPException(status_code=400, detail="Invalid criterion for round")
    record = Score(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get("/admin/leaderboard", response_model=list[LeaderboardRow])
def leaderboard(
    hackathon_id: int,
    round_name: SubmissionRound,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.JUDGE)),
):
    teams = db.query(Team).filter(Team.hackathon_id == hackathon_id).all()
    criteria = db.query(EvaluationCriterion).filter(
        EvaluationCriterion.hackathon_id == hackathon_id, EvaluationCriterion.round == round_name
    ).all()
def leaderboard(hackathon_id: int, round_name: SubmissionRound, db: Session = Depends(get_db)):
    teams = db.query(Team).filter(Team.hackathon_id == hackathon_id).all()
    criteria = (
        db.query(EvaluationCriterion)
        .filter(EvaluationCriterion.hackathon_id == hackathon_id, EvaluationCriterion.round == round_name)
        .all()
    )
    weights = {c.id: c.weight for c in criteria}
    totals = defaultdict(float)

    scores = db.query(Score).filter(Score.round == round_name).all()
    for score in scores:
        totals[score.team_id] += score.score * weights.get(score.criterion_id, 0.0)

    rows = [LeaderboardRow(team_id=t.id, team_name=t.name, total_score=round(totals[t.id], 2)) for t in teams]
    return sorted(rows, key=lambda row: row.total_score, reverse=True)


@app.post("/qr/generate")
def generate_qr(payload: QRGenerate, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN))):
    for s in scores:
        totals[s.team_id] += s.score * weights.get(s.criterion_id, 0.0)

    rows = [LeaderboardRow(team_id=t.id, team_name=t.name, total_score=round(totals[t.id], 2)) for t in teams]
    return sorted(rows, key=lambda r: r.total_score, reverse=True)


@app.post("/qr/generate")
def generate_qr(payload: QRGenerate, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user or user.verification_status != VerificationStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Only verified users can receive QR")
    token = f"{payload.purpose.value}-{secrets.token_urlsafe(16)}"
    qr = QRToken(token=token, **payload.model_dump())
    db.add(qr)
    db.commit()
    db.refresh(qr)
    return qr


@app.post("/scan")
def scan_qr(payload: ScanRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
def scan_qr(payload: ScanRequest, db: Session = Depends(get_db)):
    scanner = db.get(User, payload.scanner_id)
    if not scanner or scanner.role != UserRole.SCANNER:
        raise HTTPException(status_code=400, detail="Scanner role required")

    qr = db.query(QRToken).filter(QRToken.token == payload.token).first()
    if not qr:
        raise HTTPException(status_code=404, detail="QR token not found")

    now = datetime.utcnow()
    success = False
    message = "invalid"

    if qr.status != QRStatus.ACTIVE:
        message = f"Token already {qr.status.value.lower()}"
    elif now < qr.valid_from or now > qr.valid_to:
        qr.status = QRStatus.EXPIRED
        message = "Token expired or not yet active"
    else:
        success = True
        message = "Scan successful"
        qr.status = QRStatus.CONSUMED
        if qr.purpose in (QRPurpose.BREAKFAST, QRPurpose.LUNCH, QRPurpose.DINNER, QRPurpose.ENTRY):
            qr.status = QRStatus.CONSUMED

    log = ScanLog(qr_token_id=qr.id, scanner_id=scanner.id, success=success, message=message)
    db.add(log)
    db.commit()
    return {"success": success, "message": message, "purpose": qr.purpose}


@app.get("/admin/scan-analytics")
def scan_analytics(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
def scan_analytics(hackathon_id: int, db: Session = Depends(get_db)):
    total_scans = (
        db.query(func.count(ScanLog.id))
        .join(QRToken, QRToken.id == ScanLog.qr_token_id)
        .filter(QRToken.hackathon_id == hackathon_id)
        .scalar()
    )
    successful = (
        db.query(func.count(ScanLog.id))
        .join(QRToken, QRToken.id == ScanLog.qr_token_id)
        .filter(QRToken.hackathon_id == hackathon_id, ScanLog.success.is_(True))
        .scalar()
    )

    by_purpose = (
        db.query(QRToken.purpose, func.count(ScanLog.id))
        .join(ScanLog, ScanLog.qr_token_id == QRToken.id)
        .filter(QRToken.hackathon_id == hackathon_id, ScanLog.success.is_(True))
        .group_by(QRToken.purpose)
        .all()
    )
    return {
        "total_scans": total_scans or 0,
        "successful_scans": successful or 0,
        "by_purpose": {purpose.value: count for purpose, count in by_purpose},
        "by_purpose": {p.value: c for p, c in by_purpose},
    }
