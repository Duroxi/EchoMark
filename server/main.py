from fastapi import FastAPI, HTTPException, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from auth import generate_api_key, extract_key_from_header
from models import AgentRegisterResponse, RatingSubmit, RatingResponse, ToolStatsResponse
from db import execute_sql

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "UNAUTHORIZED" if exc.status_code == 401 else "ERROR", "message": exc.detail}}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}
    )

@app.post("/api/v1/agents/register", response_model=AgentRegisterResponse)
def register_agent():
    """Register a new agent and return API key. No DB operation for MVP."""
    api_key = generate_api_key()
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
    api_key = await verify_auth(authorization)

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
        (rating.tool_name, api_key, rating.accuracy, rating.efficiency, rating.usability, rating.stability, overall, rating.comment),
        fetch_one=True
    )

    rating_id = result['id']
    return RatingResponse(id=str(rating_id), success=True, message="Rating submitted")

@app.get("/api/v1/ratings/{tool_name}", response_model=ToolStatsResponse)
async def get_rating(tool_name: str, authorization: str = Header(...)):
    """Get rating stats for a tool."""
    api_key = await verify_auth(authorization)

    result = execute_sql(
        """SELECT tool_name, total_ratings, avg_accuracy, avg_efficiency,
                  avg_usability, avg_stability, avg_overall, last_updated
           FROM tool_stats WHERE tool_name = %s""",
        (tool_name,),
        fetch_one=True
    )

    if not result:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": f"No ratings found for tool: {tool_name}"}})

    return ToolStatsResponse(
        tool_name=result['tool_name'],
        stats={
            "total_ratings": result['total_ratings'],
            "avg_overall": float(result['avg_overall']) if result['avg_overall'] else 0.0,
            "avg_accuracy": float(result['avg_accuracy']) if result['avg_accuracy'] else 0.0,
            "avg_efficiency": float(result['avg_efficiency']) if result['avg_efficiency'] else 0.0,
            "avg_usability": float(result['avg_usability']) if result['avg_usability'] else 0.0,
            "avg_stability": float(result['avg_stability']) if result['avg_stability'] else 0.0,
            "last_updated": result['last_updated'].isoformat() if result['last_updated'] else None
        }
    )

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from jobs.nightly_update import nightly_update

scheduler = AsyncIOScheduler()
scheduler.add_job(nightly_update, 'cron', hour=0, minute=5)

@app.on_event("startup")
async def startup():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
