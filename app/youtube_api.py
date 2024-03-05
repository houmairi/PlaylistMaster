import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
from flask import request, session, redirect, url_for, flash
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from oauthlib.oauth2 import OAuth2Error
import logging


# YouTube API service endpoints
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
YOUTUBE_API_BASE_URL = 'https://www.googleapis.com/youtube/v3'

# Replace these placeholders with your actual credentials
CLIENT_SECRETS_FILE = 'client_secret_1033164421113-5dang8disl6mn08ojvlgamlsoejr7qai.apps.googleusercontent.com.json'
SCOPES = [      'https://www.googleapis.com/auth/youtube.force-ssl',
                'https://www.googleapis.com/auth/userinfo.profile'
]
REDIRECT_URI = 'http://127.0.0.1:5000/oauth2callback'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def initiate_oauth_flow():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

def oauth2callback():
    state = session.get('state')
    if not state:
        logging.info('No session state found')
        flash('Session state not found.')
        return redirect(url_for('main.index'))

    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, state=state, redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(authorization_response=request.url)
        logging.info('Successfully fetched token')
    except OAuth2Error as e: 
        logging.error(f'OAuth2Error during authentication: {e.description}')
        flash(f'Failed to complete authentication: {e.description}')
        return redirect(url_for('main.index'))
    except Exception as e:
        logging.error(f'Unexpected error during authentication: {e}')
        flash(f'An error occurred: {e}')
        return redirect(url_for('main.index'))

    session['credentials'] = flow.credentials_to_dict()
    logging.info('Credentials saved to session')
    flash('You have been successfully logged in.')
    return redirect(url_for('main.index'))

def build_youtube_client():
    credentials = session.get('credentials')
    if credentials:
        youtube = build('youtube', 'v3', credentials=credentials)
        return youtube
    return None

def get_authenticated_service():
    credentials = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        credentials = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(credentials.to_json())

    return credentials

def search_youtube_for_song(song_name, credentials):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
    search_response = youtube.search().list(
        q=song_name,
        part='id,snippet',
        maxResults=1,
        type='video'
    ).execute()

    items = search_response.get('items', [])
    if not items:
        print(f"No search results for {song_name}")
        return None
    return items[0]['id']['videoId']

def create_youtube_playlist(credentials, playlist_title="New Playlist", playlist_description="Created via API"):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
    playlists_insert_response = youtube.playlists().insert(
        part="snippet,status",
        body=dict(
            snippet=dict(
                title=playlist_title,
                description=playlist_description
            ),
            status=dict(
                privacyStatus="private"
            )
        )
    ).execute()

    return playlists_insert_response["id"]

def add_video_to_playlist(credentials, playlist_id, video_id):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
    add_video_response = youtube.playlistItems().insert(
        part="snippet",
        body={
            'snippet': {
                'playlistId': playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id
                }
            }
        }
    ).execute()

def authenticate_youtube_api():
    """Authenticate with the YouTube API and return an authorized service object."""
    # Placeholder: Implement the actual authentication logic here
    return None

def search_song(song_name):
    """Search for a song on YouTube and return the video ID of the first result."""
    # Placeholder: Implement the actual search logic here
    return "video_id_mock"

def create_playlist(title="New Playlist", description="Created via API"):
    """Create a new YouTube playlist and return its ID."""
    # Placeholder: Implement the actual playlist creation logic here
    return "playlist_id_mock"

def add_song_to_playlist(playlist_id, video_id):
    """Add a song to the specified YouTube playlist."""
    # Placeholder: Implement the actual logic to add a song to a playlist here
    pass

# Now, define the create_playlist_with_songs function
def create_playlist_with_songs(song_names):
    """Create a playlist and add the provided songs to it."""
    success = True
    message = "Playlist created successfully!"
    
    # Authenticate with the YouTube API
    youtube_service = authenticate_youtube_api()
    
    if not youtube_service:
        return False, "Failed to authenticate with the YouTube API."
    
    # Create a new playlist
    playlist_id = create_playlist()
    
    if not playlist_id:
        return False, "Failed to create a new playlist."
    
    # For each song name, search for the song and add it to the playlist
    for song_name in song_names:
        video_id = search_song(song_name)
        if video_id:
            add_song_to_playlist(playlist_id, video_id)
        else:
            success = False
            message += f" Failed to find or add song: {song_name}."
    
    return success, message

    return add_video_response
