from flask import Flask, send_from_directory
from routes.all_routes import client_bp
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'change-this-to-a-secure-random-string'


@app.context_processor
def inject_year():
    return {'year': datetime.now().year}





app.register_blueprint(client_bp)
from routes.backup_routes import backup_bp
app.register_blueprint(backup_bp)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
