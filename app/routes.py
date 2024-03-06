from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .youtube_api import initiate_oauth_flow, oauth2callback, create_playlist_with_name, get_user_info, get_user_playlists, delete_playlist, rename_playlist
from google.oauth2.credentials import Credentials
import json
import logging

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

@bp.route('/')
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

    return render_template('index.html', user_name=user_name, user_playlists=user_playlists)

@bp.route('/playlists')
def playlists():
    credentials_json = session.get('credentials')
    if not credentials_json:
        flash('Please log in to view your playlists.')
        return redirect(url_for('main.authorize'))

    try:
        credentials = Credentials.from_authorized_user_info(
            info=json.loads(credentials_json)
        )
        playlists = get_user_playlists(credentials)
    except Exception as e:
        logging.error(f'Failed to get user playlists: {e}')
        playlists = []

    return render_template('playlists.html', playlists=playlists)

@bp.route('/delete_playlist/<playlist_id>', methods=['POST'])
def delete_playlist_route(playlist_id):
    credentials_json = session.get('credentials')
    if not credentials_json:
        flash('Please log in to delete a playlist.')
        return redirect(url_for('main.authorize'))

    try:
        credentials = Credentials.from_authorized_user_info(
            info=json.loads(credentials_json)
        )
        delete_playlist(credentials, playlist_id)
        flash('Playlist deleted successfully.')
    except Exception as e:
        logging.error(f'Failed to delete playlist: {e}')
        flash('Failed to delete playlist. Please try again.')

    return redirect(url_for('main.playlists'))

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

@bp.route('/logout')
def logout():
    session.clear()  # Clear the session data
    return redirect(url_for('main.index'))  # Redirect to the index page after logout