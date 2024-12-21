from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import notification

from  . import models
from .database import engine
from .routers import like, post, user, auth, pet, comment, notification

# models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(like.router)
app.include_router(pet.router)
app.include_router(comment.router)
app.include_router(notification.router)


@app.get("/")
async def root():
    return {"message": "Hello World 1"}
   