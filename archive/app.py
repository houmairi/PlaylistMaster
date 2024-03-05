from flask import Flask, redirect, url_for, session, request, render_template, flash, jsonify
import os
import requests
import logging
import time
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "[:oUX7tG)E_61Du.O+b")
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id='1033164421113-5dang8disl6mn08ojvlgamlsoejr7qai.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={
        'scope': 'https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/userinfo.profile',
        'redirect_uri': 'http://127.0.0.1:5000/oauth2callback'
    }
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/oauth2callback')
def authorize():
    token = google.authorize_access_token()
    session['credentials'] = token
    user_info = google.get('userinfo').json()
    session['user'] = user_info
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q')
    if not query:
        return render_template('search_results.html', results=None, query=None)

    search_results = search_youtube_for_songs(query)

    if search_results:
        return render_template('search_results.html', results=search_results, query=query)
    else:
        flash('No results found', 'info')
        return redirect(url_for('index'))

# Configure logging
logging.basicConfig(filename='youtube_search.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def search_youtube_for_songs(query):
    search_url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': query,
        'key': 'AIzaSyCZmhIb1GkKhU_UhCC7NWLbCGLYt5anDnc',
        'maxResults': 10,
        'type': 'video'
    }
    response = requests.get(search_url, params=params)

    if response.status_code == 200:
        search_results = response.json().get('items', [])
        formatted_results = []
        for item in search_results:
            video_id = item['id']['videoId']
            title = item['snippet']['title']
            channel_title = item['snippet']['channelTitle']
            formatted_results.append({'videoId': video_id, 'title': title, 'channelTitle': channel_title})
        
        # Log the formatted search results
        for result in formatted_results:
            logging.info(f"Video ID: {result['videoId']}, Title: {result['title']}, Channel Title: {result['channelTitle']}")
        
        return formatted_results
    else:
        logging.error("Failed to fetch search results from YouTube API")
        return None

# CSRF Protection Setup
@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            return jsonify(error="CSRF error", reason="The CSRF token is missing or incorrect."), 400

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = os.urandom(16).hex()
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    if 'credentials' not in session:
        return redirect(url_for('login'))

    songs_text = request.form.get('songs')
    if not songs_text:
        flash('Please enter at least one song.', 'error')
        return redirect(url_for('index'))

    song_names = songs_text.splitlines()
    song_names = [song.strip() for song in song_names if song.strip()]
    access_token = session['credentials']['access_token']

    playlist_id = create_youtube_playlist(access_token)

    if not playlist_id:
        flash('Failed to create a new YouTube playlist.', 'error')
        return redirect(url_for('index'))

    for song_name in song_names:
        video_id = search_youtube_for_song(song_name, access_token)
        if video_id:
            add_video_to_playlist(video_id, playlist_id, access_token)

    flash('Playlist created successfully!', 'success')
    return redirect(url_for('index'))

def create_youtube_playlist(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    playlist_data = {
        "snippet": {
            "title": "New Playlist",
            "description": "Playlist created via Flask app",
            "tags": ["sample", "playlist"],
            "privacyStatus": "public"
        },
        "status": {
            "privacyStatus": "public"
        }
    }
    response = requests.post('https://www.googleapis.com/youtube/v3/playlists?part=snippet,status',
                             headers=headers, json=playlist_data)
    if response.status_code == 200:
        playlist_id = response.json().get('id')
        logging.info(f"Playlist created successfully! Playlist ID: {playlist_id}")
        return playlist_id
    else:
        logging.error(f"Failed to create playlist: {response.content}")
        return None


def search_youtube_for_song(song_name, access_token):
    search_url = 'https://www.googleapis.com/youtube/v3/search'
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        'part': 'snippet',
        'maxResults': 1,
        'q': song_name,
        'type': 'video'
    }
    response = requests.get(search_url, headers=headers, params=params)
    if response.status_code == 200:
        items = response.json().get('items')
        if not items:
            logging.error(f"No search results for: {song_name}")
            return None
        return items[0]['id']['videoId']
    else:
        logging.error(f"Failed to search for song {song_name}: {response.content}")
        return None

def add_video_to_playlist(video_id, playlist_id, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    item_data = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id
            }
        }
    }
    response = requests.post('https://www.googleapis.com/youtube/v3/playlistItems?part=snippet',
                             headers=headers, json=item_data)
    if response.status_code != 200:
        logging.error(f"Failed to add video {video_id} to playlist: {response.content}")
    
    max_retries = 5
    retry_wait = 1  # Start with a 1 second wait time

    for attempt in range(max_retries):
        item_response = requests.post('https://www.googleapis.com/youtube/v3/playlistItems?part=snippet', headers=headers, json=item_data)
        if item_response.status_code == 200:
            logging.info(f"Video {video_id} added to playlist {playlist_id}.")
            break
        elif item_response.status_code == 429:
            logging.warning(f"Rate limit exceeded when adding video to playlist. Attempt {attempt+1}. Waiting {retry_wait} seconds before retrying...")
            time.sleep(retry_wait)
            retry_wait *= 2  # Exponentially increase wait time
        else:
            logging.error(f"Failed to add video to playlist. HTTP Status Code: {item_response.status_code}. Response: {item_response.text}")
            item_response.raise_for_status()

    if item_response.status_code != 200:
        raise Exception(f"Failed to add video {video_id} to playlist after {max_retries} attempts.")

if __name__ == "__main__":
    app.run(debug=True)
