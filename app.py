import logging
from app import create_app

logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
