"""
TODO: CREATE FOLLOWING ENDPOINTS:

THIS IS FOR THE FRONTEND:
{
    first_name: 'Team Name',
    last_name: '',
    bio: 'Hi I work at Google',
    created_at: TIMESTAMP,
    last_updated: TIMESTAMP
}

'2011-11-04T00:05:23+04:00'

You'll get the user_id and email of the person who made the API call from the JWT

GET /user -> Return the information about the requesting user.

GET /user/verify?email={email@test.com} -> Return whether an account exists with the given email address.
Return the full user object if yes, otherwise give a 404 response error

POST /user -> Create the user
PUT /user -> Update the user
"""