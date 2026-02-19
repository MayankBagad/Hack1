from datetime import datetime, timedelta
import os

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

client = TestClient(app)


def setup_module():
    if os.path.exists("hackathon.db"):
        os.remove("hackathon.db")
    Base.metadata.create_all(bind=engine)


def _signup_and_login(name, email, phone, role="STUDENT"):
    user = client.post(
        "/auth/signup",
        json={"name": name, "email": email, "phone": phone, "password": "secret123", "role": role},
    ).json()
    login = client.post("/auth/login", json={"email": email, "password": "secret123"}).json()
    token = login["access_token"]
    return user, {"Authorization": f"Bearer {token}"}


def test_end_to_end_flow():
    admin, admin_h = _signup_and_login("Admin", "admin@example.com", "9000000000", role="ADMIN")
    student, student_h = _signup_and_login("Alice", "alice@example.com", "9000000001")
    judge, judge_h = _signup_and_login("Judge", "judge@example.com", "9000000002", role="JUDGE")
    scanner, _ = _signup_and_login("Scan", "scanner@example.com", "9000000003", role="SCANNER")

    client.post("/auth/verify-otp", headers=student_h, json={"user_id": student["id"], "otp": "123456"})
    client.post(
        "/verification/upload-documents",
        headers=student_h,
        json={"college_id_path": "id.png", "aadhaar_masked": "XXXX-XXXX-1111", "selfie_path": "selfie.png"},
    )
    client.patch(f"/admin/verification/{student['id']}", headers=admin_h, json={"status": "APPROVED"})

    now = datetime.utcnow()
    hack = client.post(
        "/admin/hackathons",
        headers=admin_h,
        json={
            "title": "Campus Hack",
            "description": "demo",
            "registration_deadline": (now + timedelta(days=2)).isoformat(),
            "round1_deadline": (now + timedelta(days=3)).isoformat(),
            "final_deadline": (now + timedelta(days=4)).isoformat(),
        },
    ).json()

    ps = client.post(
        f"/admin/hackathons/{hack['id']}/problem-statements",
        headers=admin_h,
        json={"title": "Smart Campus", "description": "desc"},
    ).json()

    team = client.post(
        "/teams",
        headers=student_h,
        json={
            "hackathon_id": hack["id"],
            "name": "Team One",
            "captain_id": student["id"],
            "member_ids": [],
            "problem_statement_id": ps["id"],
        },
    )
    assert team.status_code == 200
    team_id = team.json()["id"]

    sub = client.post(
        "/submissions",
        headers=student_h,
        json={"team_id": team_id, "round": "ROUND1", "ppt_link": "https://ppt"},
    )
    assert sub.status_code == 200

    c = client.post(
        "/admin/evaluation-criteria",
        headers=admin_h,
        json={"hackathon_id": hack["id"], "round": "ROUND1", "name": "Innovation", "weight": 0.4},
    ).json()

    s = client.post(
        "/judge/scores",
        headers=judge_h,
        json={
            "team_id": team_id,
            "round": "ROUND1",
            "judge_id": judge["id"],
            "criterion_id": c["id"],
            "score": 9,
        },
    )
    assert s.status_code == 200

    lb = client.get(
        "/admin/leaderboard",
        headers=admin_h,
        params={"hackathon_id": hack["id"], "round_name": "ROUND1"},
    )
    assert lb.status_code == 200

    qr = client.post(
        "/qr/generate",
        headers=admin_h,
        json={
            "user_id": student["id"],
            "hackathon_id": hack["id"],
            "purpose": "LUNCH",
            "valid_from": (now - timedelta(minutes=5)).isoformat(),
            "valid_to": (now + timedelta(minutes=30)).isoformat(),
        },
    ).json()

    scan = client.post(
        "/scan",
        headers=admin_h,
        json={"token": qr["token"], "scanner_id": scanner["id"]},
    )
    assert scan.status_code == 200
