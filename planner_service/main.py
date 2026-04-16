from fastapi import FastAPI

app = FastAPI()

# import routes ที่มีอยู่จริง
from planner_service.app.routes import ai_routes
from planner_service.app.routes import config_routes
from planner_service.app.routes import user_routes

# include router
app.include_router(ai_routes.router)
app.include_router(config_routes.router)
app.include_router(user_routes.router)

@app.get("/")
def root():
    return {"message": "PSAI Planner Backend Running"}