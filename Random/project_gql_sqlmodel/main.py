import datetime
from asyncio import sleep

from fastapi import FastAPI
from starlette.responses import StreamingResponse

from app.api import router as api_router
from app.graphql import graphql_app

app = FastAPI()

# Include the REST API router
app.include_router(api_router, prefix="/api")

# Add GraphQL endpoint using Graphene's ASGIApp
app.add_route("/graphql", graphql_app)


async def example_logs_generator():
    while True:
        yield f"{datetime.datetime.utcnow()}: Example log"
        await sleep(1)

@app.get("/get-logs")
async def root():
    return StreamingResponse(example_logs_generator(), media_type="text/event-stream")
