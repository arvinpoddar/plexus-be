# Plexus Backend

## Setup Instructions:

1. Create virtual env (first time only):
```
pip install virtualenv
virtualenv env
```

2. Activate virtual env:
```
source env/bin/activate
```

3. Install packages:
```
pip install -r requirements.txt
```

4. Create a `firebase_creds.json` file in the root directory. To generate this file, follow the Firebase documentation here: https://firebase.google.com/docs/admin/setup. The resulting file should be similar to the contents below:
```json
{
  "type": "service_account",
  "project_id": REPLACE_ME,
  "private_key_id": REPLACE_ME,
  "private_key": REPLACE_ME,
  "client_email": REPLACE_ME,
  "client_id": REPLACE_ME,
  "auth_uri": REPLACE_ME,
  "token_uri": REPLACE_ME,
  "auth_provider_x509_cert_url": REPLACE_ME,
  "client_x509_cert_url": REPLACE_ME
}

```

5. Set environment variables and run the API by creating a `start.sh` bash script in the root directory. The environment variables contain necessary data to use the Google OAuth APIs. Follow the Google OAuth docs to setup OAuth and retrieve this information: https://developers.google.com/identity/protocols/oauth2.

The contents of our `script.sh` file should look like this:
```bash
source env/bin/activate
export GOOGLE_CLIENT_ID=REPLACE_ME
export GOOGLE_CLIENT_SECRET=REPLACE_ME
export SECRET_KEY=REPLACE_ME
export API_SECRET_KEY=REPLACE_ME
export TOKEN_URL=https://path-to-frontend-redirect-url
python3 root.py
```

6. Launch the API using `script.sh`
```
chmod +x script.sh
./start.sh
```
