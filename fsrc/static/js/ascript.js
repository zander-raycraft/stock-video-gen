let mediaRecorder;
let audioChunks = [];
let audioBlob;

const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const saveButton = document.getElementById('saveButton');
const audioPlayback = document.getElementById('audioPlayback');

startButton.addEventListener('click', async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    startButton.disabled = true;
    stopButton.disabled = false;

    mediaRecorder.start();
    mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
    };
});

stopButton.addEventListener('click', () => {
    mediaRecorder.stop();
    stopButton.disabled = true;
    saveButton.disabled = false;
    mediaRecorder.onstop = () => {
        audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        audioPlayback.src = audioUrl;
    };
});

saveButton.addEventListener('click', () => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    fetch('/save_audio', {
        method: 'POST',
        body: formData
    }).then(response => {
        if (response.ok) {
            alert('Audio saved successfully!');
            saveButton.disabled = true;
        } else {
            alert('Failed to save audio.');
        }
    });
});
