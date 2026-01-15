from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
import pytesseract
from PIL import Image
import os
import speech_recognition as sr
from pydub import AudioSegment
import shutil
import re
import google.generativeai as genai
from PIL import Image
import qrcode
import cv2
import cv2
from pyzbar.pyzbar import decode

#initialize qr object
qr = qrcode.QRCode(
    version =1,
    box_size =10,
    border=6)

# import telepot

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Configure Gemini API
genai.configure(api_key='AIzaSyCOgfZwbgOWApgdoYkD3YDqMLqBVRXZb5w')
model = genai.GenerativeModel('gemini-2.0-flash')

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe'

# Database setup
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db_connection()
cursor = conn.cursor()

# Create users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
''')

# Create patients table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        medical_history TEXT,
        medications TEXT,
        allergies TEXT,
        extracted_text TEXT,
        image_path TEXT,
        audio_text TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
''')

conn.commit()
conn.close()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', 
                           (email, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['phone'] = email
            # import pywhatkit as kit
            # import random
            # messages = ["Take a Morning tabulate", "Take an afternoon tabulate", "Take a night tabulate"]
            # selected_message = random.choice(messages)
            # kit.sendwhatmsg_instantly(f"+91{session['phone']}", selected_message)
            return redirect(url_for('dashboard'))
        else:
            return render_template('signin.html', error='Invalid email or password')
    
    return render_template('signin.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    if password != confirm_password:
        return render_template('signin.html', register_error='Passwords do not match')
    
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO users (name, email, password, created_at) VALUES (?, ?, ?, ?)',
                     (name, email, password, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return redirect(url_for('signin'))
    except sqlite3.IntegrityError:
        return render_template('signin.html', register_error='Email already exists')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    return render_template('logged.html', user_name=session['user_name'])

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    if 'image' not in request.files:
        return redirect(url_for('dashboard'))
    
    if 'audio' not in request.files:
        return redirect(url_for('dashboard'))
    
    file = request.files['image']
    filename = secure_filename(file.filename)
    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    # Extract text from image using pytesseract
    try:
        extracted_text = pytesseract.image_to_string(Image.open(filepath))
    except Exception as e:
        extracted_text = f"Error extracting text: {str(e)}"

    file1 = request.files['audio']
    filename1 = secure_filename(file1.filename)
    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    filepath1 = os.path.join(upload_folder, filename1)
    file1.save(filepath1)

    text = ''
    ffmpeg_path = "ffmpeg.exe"
    audio = AudioSegment.from_file(filepath1, format="mp3", ffmpeg=ffmpeg_path)
    segment_length = 60 * 1000
    segments = [audio[start:start + segment_length] for start in range(0, len(audio), segment_length)]

    recognizer = sr.Recognizer()
    for i, segment in enumerate(segments):
        print(i, segment)
        segment.export("temp.wav", format="wav")
        with sr.AudioFile("temp.wav") as source:
            audio_data = recognizer.record(source)
            try:
                Text = recognizer.recognize_google(audio_data)
                text += Text
                print(f"Segment {i+1}: Recognized text:", text)
            except sr.UnknownValueError:
                print(f"Segment {i+1}: Speech recognition could not understand the audio")
            except sr.RequestError as e:
                print(f"Segment {i+1}: Could not request results; {e}")

    print('recognised text')
    print(text)
    
    # Save patient details to database
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO patients (name, age, gender, extracted_text, image_path, audio_text, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        request.form['name'],
        request.form['age'],
        request.form['gender'],
        extracted_text,
        filename,
        text, 
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    conn.commit()
    conn.close()

    # data = (
    #     f"Name: {request.form['name']} | "
    #     f"Age: {request.form['age']} | "
    #     f"Gender: {request.form['gender']} | "
    #     f"Image_text: {extracted_text} | "
    #     f"Audio_text: {text}"
    # )

    qr.add_data(request.form['name'])
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color= "white")
    image.save("frame.png")
    print("QR code has been generated successfully!")

    import pywhatkit
    import pyautogui
    import time
    pywhatkit.sendwhats_image(
        receiver=f"+91{session['phone']}",
        img_path="frame.png",
        caption="Scan the QR code for patient info",
        wait_time=20,  
        tab_close=True, 
        close_time=3    
    )

    time.sleep(5) 
    pyautogui.press("enter")
    return redirect(url_for('dashboard'))

@app.route('/view_details', methods=['POST'])
def view_details():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    name = request.form['name']
    
    conn = get_db_connection()
    patient = conn.execute('SELECT * FROM patients WHERE name = ? and name = ?', (name, session['user_name'])).fetchall()
    conn.close()
    
    if patient:
        return render_template('patientdetails.html', patient=dict(patient[-1]))
    else:
        return redirect(url_for('dashboard'))

@app.route('/chatbot')
def chatbot():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    return render_template('chatbot.html')

@app.route('/scanqr')
def scanqr():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    vs = cv2.VideoCapture(0)
    while True:
        # read the image in numpy array using cv2
        ret, img = vs.read()
        # Decode the barcode image
        detectedBarcodes = decode(img)
        d=''
        t=''
        # Traverse through all the detected barcodes in image
        for barcode in detectedBarcodes:
            # Locate the barcode position in image
            (x, y, w, h) = barcode.rect
            # Put the rectangle in image using
            # cv2 to heighlight the barcode
            cv2.rectangle(img, (x-10, y-10),
                        (x + w+10, y + h+10),
                        (255, 0, 0), 2)
            d = barcode.data
            t = barcode.type
        if d != "":
            d = d.decode('utf-8', 'ignore')
            cv2.putText(img, str(d), (50, 50) , cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0) , 2)		
        #Display the image
        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        if d != "":
            break
            
    vs.release()
    cv2.destroyAllWindows()
    print(d)

    conn = get_db_connection()
    patient = conn.execute('SELECT * FROM patients WHERE name = ? and name = ?', (d,session['user_name'])).fetchall()
    conn.close()
    if patient:
        patient = patient[-1]
        d = (
            f"Patient {patient['name']} is a {patient['age']}-year-old {patient['gender']} "
            f"Extracted image text: '{patient['extracted_text']}', "
            f"and audio transcription: '{patient['audio_text']}'."
        )
        return render_template('qrdetails.html', d=d)
    else:
        return redirect(url_for('dashboard'))

@app.route('/get_chat_response', methods=['POST'])
def get_chat_response():
    if 'user_id' not in session:
        return jsonify({'response': 'Please sign in to use the chatbot.'})
    
    data = request.get_json()
    user_message = data.get('message', '')

    conn = get_db_connection()
    patient = conn.execute('SELECT * FROM patients WHERE name = ? and name = ?', (user_message,session['user_name'])).fetchall()
    conn.close()
    
    if patient:
        patient = patient[-1]
        response_sentence = (
            f"Patient {patient['name']} is a {patient['age']}-year-old {patient['gender']} "
            f"with medical history: {patient['medical_history']}, "
            f"currently taking medications: {patient['medications']}, "
            f"allergic to: {patient['allergies']}. "
            f"Extracted image text: '{patient['extracted_text']}', "
            f"and audio transcription: '{patient['audio_text']}'."
        )
        return jsonify({'response': response_sentence})
    else:
        try:
            # Get response from Gemini API
            response = model.generate_content(
                f"You are a medical assistant chatbot. Provide helpful, accurate, but not definitive medical information. "
                f"Always recommend consulting a healthcare professional for serious concerns. "
                f"User question: {user_message}"
                f"response should be in html code"
            )
            return jsonify({'response': response.text})
        except Exception as e:
            return jsonify({'response': f"Sorry, I encountered an error: {str(e)}"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)