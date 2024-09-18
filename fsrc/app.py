from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/audio')
def audio():
    return render_template('audio.html')

@app.route('/save_audio', methods=['POST'])
def save_audio():
    audio_file = request.files['audio']
    if audio_file:
        audio_path = os.path.join(UPLOAD_FOLDER, 'recording.wav')
        audio_file.save(audio_path)
        return jsonify({'message': 'Audio saved successfully!'}), 200
    return jsonify({'message': 'No audio file found'}), 400

if __name__ == "__main__":
    app.run(debug=True)
