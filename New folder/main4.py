import sqlite3
import pyaudio
import wave
import getpass

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

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
        post_register_actions()
    except sqlite3.IntegrityError:
        print("Username already taken. Please try again.")
    finally:
        conn.close()

def post_register_actions():
    print("1. Record Audio")
    print("2. Logout")
    choice = input("Choose an option: ")

    if choice == "1":
        user_id = login_user()  # Simulate login after registration for simplicity
        if user_id:
            record_and_save(user_id)
    elif choice == "2":
        print("Logged out.")
    else:
        print("Invalid choice. Exiting.")

def login_user():
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        print("Admin login successful.")
        return 'admin'

    conn = sqlite3.connect('audio_recordings.db')
    c = conn.cursor()

    c.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, password))
    user = c.fetchone()

    if user:
        print("Login successful.")
        conn.close()
        return user[0]
    else:
        print("Invalid username or password.")
        conn.close()
        return None

def view_files(user_id):
    conn = sqlite3.connect('audio_recordings.db')
    c = conn.cursor()

    c.execute('SELECT filename, timestamp FROM recordings WHERE user_id = ?', (user_id,))
    files = c.fetchall()

    if files:
        print("Your recordings:")
        for file in files:
            print(f"Filename: {file[0]}, Timestamp: {file[1]}")
    else:
        print("No recordings found.")

    conn.close()

def view_all_files():
    conn = sqlite3.connect('audio_recordings.db')
    c = conn.cursor()

    c.execute('SELECT users.username, recordings.filename, recordings.timestamp FROM recordings JOIN users ON recordings.user_id = users.id')
    files = c.fetchall()

    if files:
        print("All recordings:")
        for file in files:
            print(f"Username: {file[0]}, Filename: {file[1]}, Timestamp: {file[2]}")
    else:
        print("No recordings found.")

    conn.close()

def delete_recording():
    conn = sqlite3.connect('audio_recordings.db')
    c = conn.cursor()

    recording_id = input("Enter the ID of the recording to delete: ")
    c.execute('DELETE FROM recordings WHERE id = ?', (recording_id,))
    conn.commit()
    conn.close()
    print("Recording deleted successfully.")

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

def save_to_database(user_id, filename):
    conn = sqlite3.connect('audio_recordings.db')
    c = conn.cursor()

    c.execute('INSERT INTO recordings (user_id, filename) VALUES (?, ?)', (user_id, filename))
    conn.commit()
    conn.close()

def record_and_save(user_id):
    filename = input("Enter the filename for the recording (without extension): ") + '.mp3'
    record_audio(filename)
    save_to_database(user_id, filename)

def main():
    setup_database()

    print("1. Register")
    print("2. Login")
    choice = input("Choose an option: ")

    if choice == "1":
        register_user()
    elif choice == "2":
        user_id = login_user()
        if not user_id:
            return
        if user_id == 'admin':
            while True:
                print("1. View All Recordings")
                print("2. Delete Recording")
                print("3. Record New Audio")
                print("4. Logout")
                choice = input("Choose an option: ")

                if choice == "1":
                    view_all_files()
                elif choice == "2":
                    delete_recording()
                elif choice == "3":
                    record_and_save('admin')
                elif choice == "4":
                    print("Logged out.")
                    break
                else:
                    print("Invalid choice. Please try again.")
        else:
            while True:
                print("1. View My Recordings")
                print("2. Record New Audio")
                print("3. Logout")
                choice = input("Choose an option: ")

                if choice == "1":
                    view_files(user_id)
                elif choice == "2":
                    record_and_save(user_id)
                elif choice == "3":
                    print("Logged out.")
                    break
                else:
                    print("Invalid choice. Please try again.")
    else:
        print("Invalid choice. Exiting.")

if __name__ == '__main__':
    main()