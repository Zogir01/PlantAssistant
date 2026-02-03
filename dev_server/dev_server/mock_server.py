from flask import Flask, request, jsonify
import api_mock as api  # Import mock API

app = Flask(__name__, static_folder='www', static_url_path='')

@app.route('/')
def root():
    return app.send_static_file('index.html')  # Domyślny entry point

if __name__ == '__main__':
    app.run(debug=True, port=5000)  # Uruchom na localhost:5000