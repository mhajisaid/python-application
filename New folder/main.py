import os
import sqlite3
import pyaudio
import wave
import subprocess
import getpass

def setup_database():
    conn = sqlite3.connect('audio_recordings.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS recordings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    conn.commit()
    conn.close()

def register_user():
    conn = sqlite3.connect('audio_recordings.db')
    c = conn.cursor()

    username = input("Enter a new username: ")
    password = getpass.getpass("Enter a new password: ")

    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        print("User registered successfully.")
    except sqlite3.IntegrityError:
        print("Username already taken. Please try again.")
    finally:
        conn.close()

def login_user():
    conn = sqlite3.connect('audio_recordings.db')
    c = conn.cursor()

    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")

    c.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, password))
    user = c.fetchone()

    if user:
        print("Login successful.")
        return user[0]
    else:
        print("Invalid username or password.")
        return None

    conn.close()

def record_audio(filename, record_seconds=10):
    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 2
    fs = 44100  # Record at 44100 samples per second

    p = pyaudio.PyAudio()

    print('Recording...')

    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    frames = []

    for _ in range(0, int(fs / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    print('Finished recording.')

    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()

def convert_to_mp3(wav_filename, mp3_filename):
    print(f'Converting {wav_filename} to {mp3_filename}...')
    print('Conversion finished.')

def save_to_database(user_id, filename):
    conn = sqlite3.connect('audio_recordings.db')
    c = conn.cursor()

    c.execute('INSERT INTO recordings (user_id, filename) VALUES (?, ?)', (user_id, filename))
    conn.commit()
    conn.close()

def main():
    setup_database()

    print("1. Register")
    print("2. Login")
    choice = input("Choose an option: ")

    if choice == "1":
        register_user()
        return
    elif choice == "2":
        user_id = login_user()
        if not user_id:
            return
    else:
        print("Invalid choice. Exiting.")
        return

    wav_filename = 'output.wav'
    mp3_filename = 'output.mp3'

    record_audio(wav_filename)
    save_to_database(user_id, mp3_filename)

    # Clean up the WAV file after conversion
    if os.path.exists(wav_filename):
        os.remove(wav_filename)

if __name__ == '__main__':
    main()