from flask import Flask, send_from_directory
from routes.all_routes import employee_bp


app = Flask(__name__)
app.secret_key = 'change-this-to-a-secure-random-string'


# Map existing folders into the conventional `/static/...` URL space so templates can
# use `url_for('static', filename=...)` without physically moving files.
@app.route('/static/css/<path:filename>')
def static_css(filename):
    # maps /static/css/... -> files under ./css/
    return send_from_directory('css', filename)


@app.route('/static/js/<path:filename>')
def static_js(filename):
    # maps /static/js/... -> files under ./js/
    return send_from_directory('js', filename)


@app.route('/static/resources/<path:filename>')
def static_resources(filename):
    # maps /static/resources/... -> files under ./resources/
    return send_from_directory('resources', filename)


@app.route('/static/webfonts/<path:filename>')
def static_webfonts(filename):
    # maps /static/webfonts/... -> files under ./webfonts/
    return send_from_directory('webfonts', filename)


app.register_blueprint(employee_bp)


if __name__ == "__main__":
    app.run(debug=True)
