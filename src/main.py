from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .routes import payorder, quote

from .config import GZIP_MINIMUM_SIZE


app = FastAPI()

app.add_middleware(GZipMiddleware, minimum_size=GZIP_MINIMUM_SIZE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payorder.router)
# app.include_router(quote.router)
