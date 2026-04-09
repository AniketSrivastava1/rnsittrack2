import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..models import EnvironmentSnapshot, TeamPolicy, ToolVersion, DriftReport, VersionChange
from .drift_service import DriftDetectionService, _severity

logger = logging.getLogger(__name__)

class TeamSyncService:
    """Manages environment metadata synchronization with the Team Hub."""
    
    def __init__(self, db_session: Any = None):
        self.db_session = db_session
        self.hub_url = "https://api.devready.ai/v1/team" # Mock Hub URL
        self._last_sync_time: Optional[datetime] = None
    
    async def sync_snapshot(self, snapshot: EnvironmentSnapshot) -> bool:
        """Pushes a local environment snapshot to the Team Hub."""
        logger.info(f"Syncing snapshot {snapshot.id} for project {snapshot.project_name} to Team Hub...")
        
        # Simulating a Hub POST request
        # In a real implementation, we would use httpx.AsyncClient()
        await asyncio.sleep(0.5) 
        
        self._last_sync_time = datetime.utcnow()
        logger.info(f"Successfully synced {snapshot.id} with Team Hub.")
        return True

    async def get_team_health_summary(self) -> Dict[str, Any]:
        """Pulls the aggregate health status for the entire team from the Hub."""
        logger.debug("Fetching team health summary from Hub...")
        
        # High-fidelity mock data representing colleagues from the team
        await asyncio.sleep(0.3)
        now = datetime.utcnow()
        return {
            "team_name": "Core Platform Engineering",
            "aggregate_score": 88,
            "member_count": 4,
            "members": [
                {
                    "id": "gowri",
                    "name": "Gowri",
                    "role": "Lead Architect",
                    "score": 92,
                    "status": "online",
                    "last_scan": "2m ago",
                    "last_scan_dt": (now - timedelta(minutes=2)).isoformat(),
                    "avatar": "GS"
                },
                {
                    "id": "aniket",
                    "name": "Aniket",
                    "role": "Fullstack Engineer",
                    "score": 85,
                    "status": "offline",
                    "last_scan": "1h ago",
                    "last_scan_dt": (now - timedelta(hours=1)).isoformat(),
                    "avatar": "AS"
                },
                {
                    "id": "shuvam",
                    "name": "Shuvam",
                    "role": "QA Lead",
                    "score": 70,
                    "status": "warning",
                    "last_scan": "15h ago",
                    "last_scan_dt": (now - timedelta(hours=15)).isoformat(),
                    "avatar": "SM"
                },
                {
                    "id": "arun",
                    "name": "Arun",
                    "role": "DevOps Ninja",
                    "score": 100,
                    "status": "online",
                    "last_scan": "1m ago",
                    "last_scan_dt": (now - timedelta(minutes=1)).isoformat(),
                    "avatar": "AK"
                },
            ]
        }

    async def get_member_details(self, member_id: str) -> Dict[str, Any]:
        """Returns detailed history and setup for a specific teammate."""
        from datetime import timedelta
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=14)

        # High-fidelity mock history, dynamically generated
        all_history = [
            {"date_dt": now - timedelta(minutes=15), "score": 92, "event": "Environment updated"},
            {"date_dt": now - timedelta(hours=2), "score": 88, "event": "Dependency drift detected"},
            {"date_dt": now - timedelta(hours=13), "score": 95, "event": "Clean scan"},
            {"date_dt": now - timedelta(hours=20), "score": 85, "event": "Old scan (filtered)"},
            {"date_dt": now - timedelta(days=2), "score": 80, "event": "Very old scan"}
        ]
        
        # Filter history to only include last 14 hours as requested
        recent_history = [
            {
                "date": h["date_dt"].strftime("%Y-%m-%d %H:%M"),
                "score": h["score"],
                "event": h["event"]
            }
            for h in all_history if h["date_dt"] >= cutoff
        ]
        
        setups = {
            "gowri": {
                "bio": "Building the future of agentic coding.",
                "tools": [
                    {"name": "python", "version": "3.12.2", "status": "ok"},
                    {"name": "node", "version": "20.11.0", "status": "ok"},
                    {"name": "docker", "version": "25.0.3", "status": "ok"}
                ]
            },
            "aniket": {
                "bio": "Frontend perfectionist and API enthusiast.",
                "tools": [
                    {"name": "python", "version": "3.11.5", "status": "warning"},
                    {"name": "node", "version": "18.17.0", "status": "ok"},
                    {"name": "npm", "version": "9.6.7", "status": "ok"}
                ]
            },
            "shuvam": {
                "bio": "Ensuring quality through automated chaos.",
                "tools": [
                    {"name": "python", "version": "3.10.12", "status": "error"},
                    {"name": "pytest", "version": "8.0.0", "status": "ok"},
                    {"name": "selenium", "version": "4.15.0", "status": "ok"}
                ]
            },
            "arun": {
                "bio": "Infrastructure as Code is the only way.",
                "tools": [
                    {"name": "go", "version": "1.22.1", "status": "ok"},
                    {"name": "terraform", "version": "1.7.4", "status": "ok"},
                    {"name": "kubernetes", "version": "1.29.2", "status": "ok"}
                ]
            }
        }
        
        details = setups.get(member_id.lower(), {"bio": "Team member", "tools": []})
        return {
            "id": member_id,
            "bio": details["bio"],
            "tools": details["tools"],
            "history": recent_history
        }

    async def get_team_policy(self) -> Optional[TeamPolicy]:
        """Fetches the latest team-wide environment policy."""
        # Mock policy data
        return TeamPolicy(
            required_tools=[
                {"name": "python", "min_version": "3.11"},
                {"name": "docker", "min_version": "24.0"}
            ],
            forbidden_tools=["telnet", "ftp"],
            version_constraints={"node": ">=18.0.0 <21.0.0"}
        )

    async def get_drift_outliers(self) -> List[Dict[str, Any]]:
        """Identifies significant drift between the current user and the team average."""
        # E.g., 'You are on Node 18, but 80% of the team is on Node 20'
        return [
            {
                "tool": "node",
                "user_version": "18.1.0",
                "team_majority": "20.11.0",
                "adoption_rate": 0.85,
                "recommendation": "Upgrade to Node 20 to match team standards."
            }
        ]

    async def compare_with_member(self, user_snapshot: EnvironmentSnapshot, member_id: str) -> DriftReport:
        """Compares the current user's snapshot with a specific teammate's metadata."""
        # Mock teammate metadata lookup
        teammate_data = {
            "Alice": {"tools": [{"name": "python", "version": "3.12.0", "path": "/usr/bin/python", "status": "ok"}]},
            "Aniket": {"tools": [{"name": "node", "version": "20.0.0", "path": "/usr/bin/node", "status": "ok"}]},
            "Shuvam": {"tools": [{"name": "python", "version": "3.10.0", "path": "/usr/bin/python", "status": "ok"}]},
            "Arun": {"tools": [{"name": "python", "version": "3.11.0", "path": "/usr/bin/python", "status": "ok"}]}
        }
        
        member_metadata = teammate_data.get(member_id, {"tools": []})
        
        # We reuse the logic from DriftDetectionService
        drift_service = DriftDetectionService()
        
        # Create a mock snapshot for the teammate to use the comparison logic
        member_snapshot = EnvironmentSnapshot(
            id=f"member-{member_id}",
            project_path=user_snapshot.project_path,
            project_name=user_snapshot.project_name,
            tools=member_metadata["tools"],
            health_score=90,
            scan_duration_seconds=0.1
        )
        
        return drift_service.compare_snapshots(user_snapshot, member_snapshot)
