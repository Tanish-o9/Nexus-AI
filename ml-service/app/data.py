"""
Data Fetcher
============
Fetches user-project interaction data from the Django backend API.
This is the input for training the recommendation model.

What data do we need?
  - Which users interacted with which projects
  - What type of interaction (view, edit, comment, star)
  - When it happened
  - User features (role, org, how long they've been active)
  - Project features (category, size, member count)

The backend exposes: GET /api/v1/analytics/interactions
"""

from datetime import datetime, timedelta
from typing import Any

import httpx
from app.config import get_settings


class Interaction:
    """One user-project interaction record."""
    def __init__(self, user_id: str, project_id: str, org_id: str,
                 interaction_type: str, timestamp: datetime,
                 user_role: str = 'member', project_member_count: int = 0):
        self.user_id = user_id
        self.project_id = project_id
        self.org_id = org_id
        self.interaction_type = interaction_type
        self.timestamp = timestamp
        self.user_role = user_role
        self.project_member_count = project_member_count


async def fetch_interactions(days_back: int = 90) -> list[Interaction]:
    """
    Fetch interactions from the backend API.

    Args:
        days_back: Only fetch interactions from last N days

    Returns:
        List of Interaction objects
    """
    settings = get_settings()
    url = f"{settings.BACKEND_URL}/api/v1/analytics/interactions"
    cutoff = datetime.utcnow() - timedelta(days=days_back)

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            params={"since": cutoff.isoformat(), "limit": 10000},
            headers={"X-Internal-Secret": settings.INTERNAL_SERVICE_SECRET},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

    interactions = []
    for item in data.get("results", []):
        interactions.append(Interaction(
            user_id=item["user_id"],
            project_id=item["project_id"],
            org_id=item.get("org_id", ""),
            interaction_type=item.get("type", "view"),
            timestamp=datetime.fromisoformat(item["timestamp"]),
            user_role=item.get("user_role", "member"),
            project_member_count=item.get("member_count", 0),
        ))
    return interactions


def get_sample_data() -> list[Interaction]:
    """
    Returns sample interaction data for testing when backend is not available.
    This lets us test the training pipeline without a live backend.
    """
    now = datetime.utcnow()
    samples = []
    users = [f"user_{i}" for i in range(1, 21)]
    projects = [f"project_{i}" for i in range(1, 11)]

    for user_id in users:
        for project_id in projects[:5]:  # each user interacts with 5 projects
            samples.append(Interaction(
                user_id=user_id,
                project_id=project_id,
                org_id="org_1",
                interaction_type="view",
                timestamp=now - timedelta(days=len(samples) % 30),
                user_role="member",
                project_member_count=len(projects),
            ))
    return samples