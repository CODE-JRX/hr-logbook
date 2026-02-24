import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, send_from_directory
from routes.all_routes import client_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-unsecure-key-for-dev')


@app.context_processor
def inject_year():
    return {'year': datetime.now().year}





app.register_blueprint(client_bp)
from routes.backup_routes import backup_bp
app.register_blueprint(backup_bp)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
