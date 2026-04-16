from fastapi import FastAPI

app = FastAPI()

# import routes ของคุณ
from app.routes import commit_routes
from app.routes import ai_routes
from app.routes import config_routes
from app.routes import restore_routes
from app.routes import user_routes

# include router
app.include_router(commit_routes.router)
app.include_router(ai_routes.router)
app.include_router(config_routes.router)
app.include_router(restore_routes.router)
app.include_router(user_routes.router)


@app.get("/")
def root():
    return {"message": "PSAI Planner Backend Running"}