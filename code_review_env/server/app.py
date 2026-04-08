"""FastAPI server for the Code Review environment."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server import create_fastapi_app
from models import ReviewAction, ReviewObservation
from server.code_review_environment import CodeReviewEnvironment

app = create_fastapi_app(CodeReviewEnvironment, ReviewAction, ReviewObservation)

@app.get("/")
def root():
    return {"status": "ok", "environment": "code-review-env"}
