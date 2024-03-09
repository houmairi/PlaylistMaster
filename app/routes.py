from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .youtube_api import initiate_oauth_flow, get_playlist_videos, oauth2callback, create_playlist_with_name, get_user_info, get_user_playlists, delete_playlist, rename_playlist
from google.oauth2.credentials import Credentials
import json
from googleapiclient.errors import HttpError
import logging
from .cache import cache


bp = Blueprint('main', __name__)

@bp.route('/authorize')
def authorize():
    # Start the OAuth flow
    return initiate_oauth_flow()

@bp.route('/oauth2callback')
def callback():
    # Handle the OAuth2 callback
    oauth2callback()  # This will set session['credentials'] on success

    # Check if credentials were successfully saved in the session
    if 'credentials' in session:
        flash('You have been successfully logged in.')
        # Redirect to the index or a dashboard page
        return redirect(url_for('main.index'))
    else:
        # If credentials are not in session, authentication failed
        flash('Authentication failed. Please try logging in again.')
        return redirect(url_for('main.authorize'))

@bp.route('/', methods=['GET', 'POST'])
def index():
    user_name = None
    user_playlists = None

    credentials_json = session.get('credentials')
    if credentials_json:
        try:
            credentials = Credentials.from_authorized_user_info(
                info=json.loads(credentials_json)
            )
            user_name = get_user_info(credentials)
            logging.info(f'User name retrieved from API: {user_name}')

            user_playlists = get_user_playlists(credentials)
        except ValueError as e:
            logging.error(f'Failed to deserialize credentials: {e}')
        except Exception as e:
            logging.error(f'Failed to retrieve user playlists: {e}')

    if request.method == 'POST':
        playlist_name = request.form['playlist_name']
        song_list = request.form['song_list']
        privacy_status = request.form['privacy_status']
        song_names = [name.strip() for name in song_list.split('\n') if name.strip()]

        if not playlist_name:
            flash('Please provide a playlist name.')
        elif not song_names:
            flash('Please provide at least one song.')
        else:
            success, message = create_playlist_with_name(song_names, playlist_name, privacy_status)
            if success:
                flash(message)
            else:
                flash(f'Error: {message}')
        return redirect(url_for('main.index'))

    return render_template('index.html', user_name=user_name, user_playlists=user_playlists)

@bp.route('/playlists')
def playlists():
    credentials_json = session.get('credentials')
    if credentials_json:
        try:
            credentials = Credentials.from_authorized_user_info(
                info=json.loads(credentials_json)
            )
            playlists = get_user_playlists(credentials)
            for playlist in playlists:
                playlist['videos'] = get_playlist_videos(credentials, playlist['id'])
            return render_template('playlists.html', playlists=playlists)
        except ValueError as e:
            logging.error(f'Failed to deserialize credentials: {e}')
            flash('An error occurred while retrieving playlists. Please try again.')
        except HttpError as e:
            logging.error(f'Failed to retrieve user playlists: {e}')
            flash('An error occurred while retrieving playlists. Please try again.')
    return redirect(url_for('main.authorize'))

@bp.route('/rename_playlist/<playlist_id>', methods=['POST'])
def rename_playlist_route(playlist_id):
    credentials_json = session.get('credentials')
    if not credentials_json:
        flash('Please log in to rename a playlist.')
        return redirect(url_for('main.authorize'))

    new_title = request.form.get('new_title')
    if not new_title:
        flash('Please provide a new title for the playlist.')
        return redirect(url_for('main.playlists'))

    try:
        credentials = Credentials.from_authorized_user_info(
            info=json.loads(credentials_json)
        )
        rename_playlist(credentials, playlist_id, new_title)
        flash('Playlist renamed successfully.')
    except Exception as e:
        logging.error(f'Failed to rename playlist: {e}')
        flash('Failed to rename playlist. Please try again.')

    return redirect(url_for('main.playlists'))

@bp.route('/remove_playlist/<playlist_id>', methods=['POST'])
def remove_playlist_route(playlist_id):
    credentials_json = session.get('credentials')
    if not credentials_json:
        flash('Please log in to remove a playlist.')
        return redirect(url_for('main.authorize'))

    try:
        credentials = Credentials.from_authorized_user_info(
            info=json.loads(credentials_json)
        )
        delete_playlist(credentials, playlist_id)
        flash('Playlist removed successfully.')
    except Exception as e:
        logging.error(f'Failed to remove playlist: {e}')
        flash('Failed to remove playlist. Please try again.')

    return redirect(url_for('main.playlists'))

def remove_videos_from_playlist(credentials, playlist_id, video_ids):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
    for video_id in video_ids:
        youtube.playlistItems().delete(id=video_id).execute()

@bp.route('/remove_videos/<playlist_id>', methods=['POST'])
def remove_videos_route(playlist_id):
    credentials_json = session.get('credentials')
    if not credentials_json:
        flash('Please log in to remove videos from a playlist.')
        return redirect(url_for('main.authorize'))

    video_ids = request.form.getlist('video_ids[]')
    if not video_ids:
        flash('No videos selected for removal.')
        return redirect(url_for('main.playlists'))

    try:
        credentials = Credentials.from_authorized_user_info(
            info=json.loads(credentials_json)
        )
        remove_videos_from_playlist(credentials, playlist_id, video_ids)
        flash('Selected videos removed successfully.')
    except Exception as e:
        logging.error(f'Failed to remove videos from playlist: {e}')
        flash('Failed to remove videos from playlist. Please try again.')

    return redirect(url_for('main.playlists'))

from flask import make_response

@bp.route('/download_playlists')
def download_playlists():
    credentials_json = session.get('credentials')
    if not credentials_json:
        flash('Please log in to download playlists.')
        return redirect(url_for('main.authorize'))

    try:
        credentials = Credentials.from_authorized_user_info(
            info=json.loads(credentials_json)
        )
        playlists = get_user_playlists(credentials)
        playlist_info = []
        for playlist in playlists:
            playlist_videos = get_playlist_videos(credentials, playlist['id'])
            playlist_info.append(f"Playlist: {playlist['snippet']['title']}")
            for video in playlist_videos:
                duration = video.get('duration', 'N/A') #fix the code so it shows the duration
                playlist_info.append(f"- {video['title']} ({duration})")
            playlist_info.append("")  # Add an empty line between playlists

        # Generate the response with the playlist information
        response = make_response("\n".join(playlist_info))
        response.headers['Content-Disposition'] = 'attachment; filename=playlists.txt'
        response.headers['Content-type'] = 'text/plain'
        return response
    except Exception as e:
        logging.error(f'Failed to generate playlist information: {e}')
        flash('Failed to generate playlist information. Please try again.')

    return redirect(url_for('main.playlists'))

@bp.route('/logout')
def logout():
    session.clear()  # Clear the session data
    cache.clear()  # Clear the cache
    return redirect(url_for('main.index'))  # Redirect to the index page after logout