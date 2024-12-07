import cv2
import numpy as np
import tensorflow as tf
from flask import Flask, render_template, Response, jsonify
from flask_socketio import SocketIO, emit
from tensorflow.keras.models import load_model
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app)

# Load pre-trained Keras model
drowsiness_model = load_model('mobilenet_awake_drowsy.keras')

# Global camera variable
camera = None
drowsiness_thread = None
stop_thread = False

def preprocess_frame(frame):
    """Preprocess frame for model input"""
    resized = cv2.resize(frame, (224, 224))  # Adjust to your model's input size
    normalized = resized / 255.0  # Normalize pixel values
    return np.expand_dims(normalized, axis=0)

def detect_drowsiness(frame):
    """Detect drowsiness in a frame"""
    processed_frame = preprocess_frame(frame)
    
    # Predict drowsiness
    prediction = drowsiness_model.predict(processed_frame)
    drowsy_prob = prediction[0][0]
    
    # Annotate frame with drowsiness status
    status = "Awake" if drowsy_prob > 0.9 else "Drowsy"
    color = (0, 0, 255) if status == "Drowsy" else (0, 255, 0)
    
    cv2.putText(frame, 
                f"{status}: {drowsy_prob:.2f}", 
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                color, 
                2)
    
    return frame, status, drowsy_prob

def generate_frames():
    global camera
    while camera is not None:
        # Capture frame-by-frame
        success, frame = camera.read()
        if not success:
            break
        
        # Process frame
        annotated_frame, status, prob = detect_drowsiness(frame)
        
        # Encode frame
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def drowsiness_monitoring():
    global camera, stop_thread
    while not stop_thread and camera is not None:
        success, frame = camera.read()
        if success:
            _, status, prob = detect_drowsiness(frame)
            print(f"Drowsiness Status: {status}, Probability: {prob}")  # Debug print
            socketio.emit('drowsiness_update', {
                'status': status, 
                'probability': float(prob)
            })
        time.sleep(0.5)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_camera')
def start_camera():
    global camera, drowsiness_thread, stop_thread
    if camera is None:
        camera = cv2.VideoCapture(0)
        stop_thread = False
        drowsiness_thread = threading.Thread(target=drowsiness_monitoring)
        drowsiness_thread.start()
    return jsonify({"status": "Camera started"})

@app.route('/stop_camera')
def stop_camera():
    global camera, drowsiness_thread, stop_thread
    if camera is not None:
        stop_thread = True
        if drowsiness_thread:
            drowsiness_thread.join()
        camera.release()
        camera = None
    return jsonify({"status": "Camera stopped"})

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
