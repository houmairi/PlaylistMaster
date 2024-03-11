# Flask YouTube Playlist Manager

A Flask application to manage YouTube playlists, including operations such as creating playlists, adding songs, renaming and deleting playlists, and user authentication through Google OAuth 2.0.

## Features

- OAuth 2.0 Authentication with Google
- Create new YouTube playlists
- Add songs to playlists
- View and manage user playlists
- Rename and delete playlists
- Flash messaging for user interaction feedback
- Logging for error tracking and informational messages

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/houmairi/PlaylistMaster
   cd PlaylistMaster
   ```

2. **Set Up a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Requirements**

   ```bash
   pip install -r requirements.txt
   ```

   Ensure you have `Flask`, `requests`, `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, and `google-api-python-client` packages among others in your `requirements.txt`.

4. **Configure Environment Variables**

   Create a `.env` file in the root directory of your project and populate it with the necessary environment variables, such as `FLASK_APP=app.py` and `FLASK_ENV=development`.

## Configuration

- **config.py**: Contains base configuration settings, including `SECRET_KEY` and Flask environment settings.
- **Client Secrets File**: Ensure you have the `client_secret_<your_client_id>.json` file downloaded from the Google Developer Console and located in your project directory for OAuth to work properly.

## Running the Application

To start the application, use the following command:

```bash
flask run
```

This will start a local development server on `http://127.0.0.1:5000` where you can access the application.

## Application Structure

- **app.py**: The entry point to the application. Initializes logging and runs the Flask application.
- **config.py**: Contains configuration settings for the application.
- **routes.py**: Defines the routes and views for the application.
- **youtube_api.py**: Contains functions for interacting with the YouTube API, including OAuth flow, playlist management, and video management.
- **__init__.py**: Initializes the Flask application and registers blueprints and extensions.

## Logging

Logging is configured in `app.py` to write informational and error messages to `app.log` with timestamps, aiding in troubleshooting.

## Templates and Static Files

Ensure your project directory contains a `templates` folder for HTML files and a `static` folder for CSS, JavaScript, and other static files as referenced in your Flask application.

## Further Notes

- **OAuth Callback URL**: Make sure to add `http://127.0.0.1:5000/oauth2callback` to your list of authorized redirect URIs in the Google Cloud Console.
- **Security**: Never expose your `SECRET_KEY` or OAuth client secrets in public repositories.
