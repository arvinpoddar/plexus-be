import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api import api_app
from apps.auth import auth_app

ALLOWED_HOSTS = ["*"]
PORT = 4000

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount('/auth', auth_app)
app.mount('/api', api_app)

if __name__ == '__main__':
    uvicorn.run(app, port=PORT)
