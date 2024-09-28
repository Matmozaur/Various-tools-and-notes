from fastapi import FastAPI
from app.api import router as api_router
from app.graphql import graphql_app

app = FastAPI()

# Include the REST API router
app.include_router(api_router, prefix="/api")

# Add GraphQL endpoint using Graphene's ASGIApp
app.add_route("/graphql", graphql_app)
