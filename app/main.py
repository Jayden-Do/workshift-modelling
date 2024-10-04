
from fastapi import FastAPI

from app.routers import auth_router, table_router, user_router

app = FastAPI()


app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(user_router.router, prefix="/users", tags=["users"])
app.include_router(table_router.router, prefix="/tables", tags=["tables"])
