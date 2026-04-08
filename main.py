from fastapi import FastAPI
from pydantic import BaseModel
import random
import uvicorn

app = FastAPI(
    title="DevReady Health API",
    description="Backend API for the DevReady VS Code Extension Health Dashboard."
)

class HealthScore(BaseModel):
    score: int
    status: str
    message: str
    issues_found: int
    
@app.get("/api/health", response_model=HealthScore)
def get_health_score():
    """
    Returns the current environment health score.
    This simulates the "command line internship" scoring logic.
    """
    # For demonstration, generate a realistic health score (between 65 and 100)
    score = random.randint(65, 100)
    
    if score >= 90:
        status = "Healthy"
        message = "Your development environment is ready to go!"
        issues = 0
    elif score >= 75:
        status = "Warning"
        message = "Some minor issues detected. You can still code, but fixing them is recommended."
        issues = random.randint(1, 3)
    else:
        status = "Critical"
        message = "Significant drift detected in your environment. Please review."
        issues = random.randint(4, 8)
        
    return HealthScore(
        score=score,
        status=status,
        message=message,
        issues_found=issues
    )

if __name__ == "__main__":
    # Run the daemon locally for the extension to connect to it
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
