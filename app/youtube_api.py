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
import json
import google.auth.transport.requests

# YouTube API service endpoints
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
YOUTUBE_API_BASE_URL = 'https://www.googleapis.com/youtube/v3'

# Replace these placeholders with your actual credentials
CLIENT_SECRETS_FILE = 'client_secret_1033164421113-5dang8disl6mn08ojvlgamlsoejr7qai.apps.googleusercontent.com.json'
SCOPES = [      'https://www.googleapis.com/auth/youtube.force-ssl',
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/youtube.readonly',
                'https://www.googleapis.com/auth/youtube',
                'openid'
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

        # Serialize the credentials to a JSON string
        credentials_json = flow.credentials.to_json()

        # Store the serialized credentials in the session
        session['credentials'] = credentials_json
        logging.info('Credentials saved to session')

    except OAuth2Error as e:
        logging.error(f'OAuth2Error during authentication: {e.description}')
        flash(f'Failed to complete authentication: {e.description}')
        return redirect(url_for('main.index'))
    except Exception as e:
        logging.error(f'Unexpected error during authentication: {e}')
        flash(f'An error occurred: {e}')
        return redirect(url_for('main.index'))

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

def get_user_info(credentials):
    """Get the user's name from the Google API."""
    try:
        oauth_scopes = [
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'openid'
        ]
        credentials = credentials.with_scopes(oauth_scopes)
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        return user_info.get('name', 'User')
    except Exception as e:
        logging.error(f'Failed to get user info: {e}')
        return 'User'

def create_playlist_with_name(song_names, playlist_name):
    """Create a playlist with a custom name and add the provided songs to it."""
    success = True
    message = f"Playlist '{playlist_name}' created successfully!"

    # Get the authenticated YouTube service
    credentials_json = session.get('credentials')
    if not credentials_json:
        return False, "Failed to get user credentials from the session."

    # Deserialize the credentials from the JSON string
    try:
        credentials = Credentials.from_authorized_user_info(
            info=json.loads(credentials_json)
        )
    except ValueError as e:
        return False, f"Failed to deserialize credentials: {e}"

    try:
        youtube = build('youtube', 'v3', credentials=credentials)
    except HttpError as e:
        return False, f"Failed to build YouTube client: {e}"

    # Create a new playlist with the provided name
    try:
        playlists_insert_response = youtube.playlists().insert(
            part="snippet,status",
            body=dict(
                snippet=dict(
                    title=playlist_name,
                    description="Created via API"
                ),
                status=dict(
                    privacyStatus="private"
                )
            )
        ).execute()
        playlist_id = playlists_insert_response["id"]
    except HttpError as e:
        return False, f"Failed to create a new playlist: {e}"

    # For each song name, search for the song and add it to the playlist
    for song_name in song_names:
        video_id = search_youtube_for_song(song_name, credentials)
        if video_id:
            try:
                youtube.playlistItems().insert(
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
            except HttpError as e:
                success = False
                message += f" Failed to add song '{song_name}' to the playlist: {e}"
        else:
            success = False
            message += f" Failed to find song: {song_name}."

    return success, message

def revoke_credentials(credentials):
    try:
        request = google.auth.transport.requests.Request()
        credentials.revoke(request)
    except Exception as e:
        logging.error(f'Failed to revoke credentials: {e}')

def logout():
    credentials_json = session.get('credentials')
    if credentials_json:
        try:
            credentials = Credentials.from_authorized_user_info(
                info=json.loads(credentials_json)
            )
            revoke_credentials(credentials)
        except ValueError as e:
            logging.error(f'Failed to deserialize credentials: {e}')
    session.clear()