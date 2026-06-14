import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import simulate, analytics, refuel, ai, scenarios

# Create SQLite database tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FuelSense API", version="1.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production if needed, allow all for demo/judging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers as defined in technical-spec
app.include_router(scenarios.router)
app.include_router(simulate.router)
app.include_router(analytics.router)
app.include_router(refuel.router)
app.include_router(ai.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to FuelSense API. Refer to specifications for details."}
