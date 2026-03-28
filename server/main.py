from fastapi import FastAPI, HTTPException, Header
from auth import generate_api_key, hash_api_key, extract_key_from_header
from models import AgentRegisterResponse, RatingSubmit, RatingResponse
from db import execute_sql

app = FastAPI()

@app.post("/api/v1/agents/register", response_model=AgentRegisterResponse)
def register_agent():
    """Register a new agent and return API key."""
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)

    # Store hash in database (no lookup needed for MVP)
    execute_sql(
        "INSERT INTO ratings (tool_name, api_key_hash, accuracy, efficiency, usability, stability, overall, comment) VALUES ('__agent__', %s, 0, 0, 0, 0, 0, '__register__')",
        (api_key_hash,)
    )

    return AgentRegisterResponse(api_key=api_key)

async def verify_auth(authorization: str = Header(...)):
    """Verify API key from Authorization header."""
    api_key = extract_key_from_header(authorization)
    if not api_key:
        raise HTTPException(status_code=401, detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid authorization header"}})
    return api_key

@app.post("/api/v1/ratings", response_model=RatingResponse)
async def submit_rating(rating: RatingSubmit, authorization: str = Header(...)):
    """Submit a rating for a tool."""
    api_key = verify_auth(authorization)

    # Calculate overall score
    overall = (
        rating.accuracy * 0.40 +
        rating.stability * 0.30 +
        rating.efficiency * 0.20 +
        rating.usability * 0.10
    )
    overall = round(overall, 1)

    result = execute_sql(
        """INSERT INTO ratings (tool_name, api_key_hash, accuracy, efficiency, usability, stability, overall, comment)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING id""",
        (rating.tool_name, api_key, rating.accuracy, rating.efficiency, rating.usability, rating.stability, overall, rating.comment)
    )

    rating_id = result[0]['id']
    return RatingResponse(id=str(rating_id), success=True, message="Rating submitted")
