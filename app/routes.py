from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .youtube_api import initiate_oauth_flow, oauth2callback, create_playlist_with_songs

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
    if request.method == 'POST':
        song_list = request.form.get('song_list')
        if song_list:
            song_names = song_list.splitlines()
            song_names = [song.strip() for song in song_names if song.strip()]
            
            # Ensure the user is authenticated before attempting to create a playlist
            if 'credentials' not in session:
                flash('You need to log in before creating a playlist.')
                return redirect(url_for('main.authorize'))

            # Call the function to create a playlist and pass the list of song names
            success, message = create_playlist_with_songs(song_names)
            flash(message)
            if success:
                # Redirect to a success page or the index with a success message
                return redirect(url_for('main.index'))
        else:
            flash('Please enter at least one song name.')

    # If the method is GET or credentials are not set, show the main page
    return render_template('index.html')
