from flask import Flask, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
# Secret key for session management.
app.secret_key = ''

# OAuth2 client setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='',
    client_secret='',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'https://www.googleapis.com/auth/youtube.readonly', 'redirect_uri': 'https://tunjic.at/oauth2callback'}
)

@app.route('/')
def index():
    return 'Welcome to Playlist Creator! <a href="/login">Login with Google</a>'

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/oauth2callback')
def authorize():
    token = google.authorize_access_token()
    resp = google.get('userinfo', token=token)
    user_info = resp.json()
    # You can do something with user_info, like storing it in the session
    session['user'] = user_info
    return 'You are logged in as: ' + user_info['name']



if __name__ == "__main__":
    app.run(debug=True)
