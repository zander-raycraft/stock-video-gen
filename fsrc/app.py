from flask import Flask, render_template, redirect, url_for
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/audio')
def audio_recorder():
    audio_script_path = os.path.join(os.getcwd(), 'src', 'recordingGUI', 'audio.py')
    subprocess.Popen(["python", audio_script_path])
    
    return render_template('audio.html')

if __name__ == "__main__":
    app.run(debug=True)
