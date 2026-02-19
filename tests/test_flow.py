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
def _register_user(name, email, phone, role="STUDENT"):
    user = client.post(
        "/auth/register",
        json={"name": name, "email": email, "phone": phone, "role": role},
    ).json()
    client.post("/auth/verify-otp", json={"user_id": user["id"], "otp": "123456"})
    if role == "STUDENT":
        client.post(
            "/verification/upload-documents",
            params={"user_id": user["id"]},
            json={
                "college_id_path": "docs/id.png",
                "aadhaar_masked": "XXXX-XXXX-1234",
                "selfie_path": "docs/selfie.png",
            },
        )
        client.patch(f"/admin/verification/{user['id']}", json={"status": "APPROVED"})
    return user


def test_end_to_end_flow():
    student = _register_user("Alice", "alice@example.com", "9000000001")
    judge = _register_user("Judge", "judge@example.com", "9000000002", role="JUDGE")
    scanner = _register_user("Scan", "scanner@example.com", "9000000003", role="SCANNER")

    now = datetime.utcnow()
    hackathon = client.post(
        "/admin/hackathons",
        json={
            "title": "Campus Hack 2026",
            "description": "Demo",
            "registration_deadline": (now + timedelta(days=2)).isoformat(),
            "round1_deadline": (now + timedelta(days=3)).isoformat(),
            "final_deadline": (now + timedelta(days=4)).isoformat(),
        },
    ).json()

    ps = client.post(
        f"/admin/hackathons/{hack['id']}/problem-statements",
        headers=admin_h,
        json={"title": "Smart Campus", "description": "desc"},
        f"/admin/hackathons/{hackathon['id']}/problem-statements",
        json={"title": "Smart Campus", "description": "Digitize operations"},
    ).json()

    team = client.post(
        "/teams",
        headers=student_h,
        json={
            "hackathon_id": hack["id"],
        json={
            "hackathon_id": hackathon["id"],
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
    submission = client.post(
        "/submissions",
        json={
            "team_id": team_id,
            "round": "ROUND1",
            "ppt_link": "https://example.com/ppt",
        },
    )
    assert submission.status_code == 200

    criterion = client.post(
        "/admin/evaluation-criteria",
        json={
            "hackathon_id": hackathon["id"],
            "round": "ROUND1",
            "name": "Innovation",
            "weight": 0.4,
        },
    ).json()

    score = client.post(
        "/judge/scores",
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
            "criterion_id": criterion["id"],
            "score": 9,
        },
    )
    assert score.status_code == 200

    leaderboard = client.get(
        "/admin/leaderboard",
        params={"hackathon_id": hackathon["id"], "round_name": "ROUND1"},
    )
    assert leaderboard.status_code == 200
    assert leaderboard.json()[0]["team_id"] == team_id

    qr = client.post(
        "/qr/generate",
        json={
            "user_id": student["id"],
            "hackathon_id": hackathon["id"],
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
    scan = client.post("/scan", json={"token": qr["token"], "scanner_id": scanner["id"]})
    assert scan.status_code == 200
    assert scan.json()["success"] is True

    duplicate_scan = client.post("/scan", json={"token": qr["token"], "scanner_id": scanner["id"]})
    assert duplicate_scan.status_code == 200
    assert duplicate_scan.json()["success"] is False

    analytics = client.get("/admin/scan-analytics", params={"hackathon_id": hackathon["id"]})
    assert analytics.status_code == 200
    assert analytics.json()["successful_scans"] == 1
