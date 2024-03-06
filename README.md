# YouTube Playlist Creator

## Overview
A Flask web application for creating YouTube playlists by submitting song names. Utilizes the YouTube Data API for user authentication and playlist manipulation.

## Prerequisites
- Python 3.x
- Flask
- A Google Cloud Platform account with the YouTube Data API v3 enabled
- OAuth 2.0 credentials from the Google Cloud Console

## Installation
**Clone the Repository:**
git clone YOUR_REPOSITORY_URL
cd YOUR_PROJECT_DIRECTORY

**Install Dependencies:**
pip install -r requirements.txt


**Configure the Application:**
- Update `config.py` with your configuration values.
- Place `client_secret.json` in the project root.

## Running the Application
flask run

Access the application at `http://127.0.0.1:5000`.

## Usage
1. Sign in with Google.
2. Submit song names.
3. Create and add songs to a YouTube playlist.
4. Logout when done.

## Project Structure
- `app.py`: Entry point
- `config.py`: Configuration
- `youtube_api.py`: Handles YouTube Data API interactions
- `routes.py`: Defines Flask routes
- `templates/`: Contains HTML templates

## Contributing
Fork the repository and submit pull requests with your changes.

## License
Licensed under the MIT License.

Please replace YOUR_REPOSITORY_URL and YOUR_PROJECT_DIRECTORY with the actual values for your project. This format should now be fully compatible with GitHub's Markdown rendering, allowing you to easily copy and paste it into your README.md file.