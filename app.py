import logging
from app import create_app

app = create_app()

#oauth2 error finding
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    app.run(debug=True)
