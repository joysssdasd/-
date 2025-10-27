from fastapi import FastAPI

from .database import Base, engine
from .routers import auth, points, posts, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Trading Matchmaking Platform API")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(points.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
