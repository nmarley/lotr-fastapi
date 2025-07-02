from fastapi import FastAPI

from routes import health, quotes

app = FastAPI()

app.include_router(health.router)
app.include_router(quotes.router)
