let mediaRecorder: MediaRecorder | undefined;
let audioChunks: Blob[] = [];
let audioBlob: Blob | undefined;

const startButton = document.getElementById('startButton') as HTMLButtonElement;
const stopButton = document.getElementById('stopButton') as HTMLButtonElement;
const saveButton = document.getElementById('saveButton') as HTMLButtonElement;
const audioPlayback = document.getElementById('audioPlayback') as HTMLAudioElement;

startButton.addEventListener('click', async () => {
    try {
        const stream: MediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        startButton.disabled = true;
        stopButton.disabled = false;

        mediaRecorder.start();
        mediaRecorder.ondataavailable = (event: BlobEvent) => {
            audioChunks.push(event.data);
        };
    } catch (err) {
        console.error('Error accessing microphone', err);
    }
});

stopButton.addEventListener('click', () => {
    if (mediaRecorder) {
        mediaRecorder.stop();
        stopButton.disabled = true;
        saveButton.disabled = false;

        mediaRecorder.onstop = () => {
            audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            audioPlayback.src = audioUrl;
        };
    }
});

saveButton.addEventListener('click', () => {
    if (audioBlob) {
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
        }).catch(err => {
            console.error('Error saving audio', err);
        });
    }
});
