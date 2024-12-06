const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const videoStream = document.getElementById('video-stream');
const statusDisplay = document.getElementById('status');
const drowsinessResult = document.getElementById('drowsiness-result');
const alarmSound = document.getElementById('alarm-sound');

        // Variable to track if alarm is currently playing
    let isAlarmPlaying = false;

    startBtn.addEventListener('click', () => {
        fetch('/start_camera')
            .then(response => response.json())
            .then(data => {
                if (data.status === "Camera started") {
                    videoStream.src = '/video_feed';
                    videoStream.style.display = 'block';
                    statusDisplay.textContent = 'Camera Status: Active';
                    startBtn.disabled = true;
                    stopBtn.disabled = false;
                }
            });
    });

    stopBtn.addEventListener('click', () => {
        fetch('/stop_camera')
            .then(response => response.json())
            .then(data => {
                if (data.status === "Camera stopped") {
                    videoStream.src = '';
                    videoStream.style.display = 'none';
                    statusDisplay.textContent = 'Camera Status: Inactive';
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                    drowsinessResult.textContent = '';
                        
                     // Stop and reset alarm if it's playing
                    alarmSound.pause();
                    alarmSound.currentTime = 0;
                    isAlarmPlaying = false;
                }
            });
    });

        const socket = io.connect(window.location.origin);
        isAlarmPlaying = false;

    socket.on('drowsiness_update', (data) => {
    drowsinessResult.textContent = `Status: ${data.status} (${data.probability.toFixed(2)})`;
    drowsinessResult.style.color = data.status === 'Drowsy' ? 'red' : 'green';

    if (data.status === 'Drowsy') {
        if (!isAlarmPlaying) {
            try {
                alarmSound.loop = true;
                alarmSound.play().then(() => {
                    isAlarmPlaying = true;
                }).catch(error => {
                    console.error('Error playing audio:', error);
                });
            } catch (error) {
                console.error('Unexpected audio play error:', error);
            }
        }
    } else {
        if (isAlarmPlaying) {
            alarmSound.pause();
            alarmSound.currentTime = 0;
            isAlarmPlaying = false;
        }
    }
});

// Ensure the audio context is unlocked on user interaction
    document.addEventListener('click', () => {
        alarmSound.play().catch(() => {}); // Start and immediately pause to unlock audio context
        alarmSound.pause();
        alarmSound.currentTime = 0;
        document.removeEventListener('click', this);
});
