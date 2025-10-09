# mintmuse-agent/app/main.py

import os
print("TEST_VAR is:", os.getenv("TEST_VAR"))
from fastapi import FastAPI
from app.routes import mint_route

app = FastAPI()

# Include the minting route
app.include_router(mint_route.router)


@app.get("/")
def read_root():
    return {"message": "MintMuse API is running"}
