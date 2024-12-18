from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import user, product, order, quote

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(product.router)
app.include_router(order.router)
app.include_router(quote.router)


