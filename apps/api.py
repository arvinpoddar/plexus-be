from fastapi import FastAPI, Depends
from apps.jwt import get_current_user_data
from apps.users import user_api
from apps.teams import team_api

api_app = FastAPI()


@api_app.get('/')
def test():
    return {'response': 'Plexus API V1'}


@api_app.get('/protected')
def test2(current_user: dict = Depends(get_current_user_data)):
    return current_user

api_app.mount('/users', user_api)
api_app.mount('/teams', team_api)