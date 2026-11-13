import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_activity(monkeypatch):
    activity_name = "Test Activity"
    activity = {
        "description": "A test activity",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 3,
        "participants": ["existing@mergington.edu"],
    }
    monkeypatch.setitem(activities, activity_name, activity)
    return activity_name, activity


def test_get_activities_returns_activity_details(client, sample_activity):
    # Arrange
    activity_name, activity = sample_activity

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[activity_name] == activity


def test_signup_adds_student_to_activity(client, sample_activity):
    # Arrange
    activity_name, activity = sample_activity
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert activity["participants"] == [
        "existing@mergington.edu",
        email,
    ]


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_student(client, sample_activity):
    # Arrange
    activity_name, activity = sample_activity
    email = activity["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activity["participants"] == [email]


def test_unregister_removes_student_from_activity(client, sample_activity):
    # Arrange
    activity_name, activity = sample_activity
    email = activity["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activity["participants"]


def test_unregister_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_not_found_for_unregistered_student(client, sample_activity):
    # Arrange
    activity_name, activity = sample_activity
    email = "unregistered@mergington.edu"
    original_participants = activity["participants"].copy()

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activity["participants"] == original_participants
