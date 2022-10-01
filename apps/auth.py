from oauth2client import client
import os
from pydantic import BaseModel
from authlib.integrations.starlette_client import OAuthError
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from apps.jwt import CREDENTIALS_EXCEPTION, create_token

# Create the auth app
auth_app = FastAPI()

# OAuth settings
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or None
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or None
if GOOGLE_CLIENT_ID is None or GOOGLE_CLIENT_SECRET is None:
    raise BaseException('Missing env variables')

# Set up the middleware to read the request session
SECRET_KEY = os.environ.get('SECRET_KEY') or None
if SECRET_KEY is None:
    raise 'Missing SECRET_KEY'
auth_app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


class GoogleAuthCode(BaseModel):
    code: str


@auth_app.post('/token')
async def auth(code_body: GoogleAuthCode):
    credentials = None
    try:
        auth_code = code_body.code
        credentials = client.credentials_from_code(
            GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, scope='', code=auth_code)
    except OAuthError:
        raise CREDENTIALS_EXCEPTION

    if not credentials and credentials.id_token:
        raise CREDENTIALS_EXCEPTION
    user_data = credentials.id_token
    return JSONResponse({
        **credentials.id_token,
        'access_token': create_token(user_data),
        'email': user_data['email'],
        'id': user_data['sub'],
    })
