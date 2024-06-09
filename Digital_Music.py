import sqlite3  # To interact with SQLite database
import pyaudio  # To handle audio recording
import wave  # To manage WAV file formats
import getpass  # For secure password input
import random  # To generate random numbers
from cryptography.fernet import Fernet  # For encryption and decryption
import base64  # For encoding and decoding binary data
import os  # To interact with the operating system

# Constants for admin login credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# Function to generate an encryption key
def generate_key():
    key = Fernet.generate_key()
    return key

# Function to save the encryption key to a file
def save_key(key, filename='Digital_Music.key'):
    with open(filename, 'wb') as key_file:
        key_file.write(key)

# Function to load the encryption key from a file
def load_key(filename='Digital_Music.key'):
    return open(filename, 'rb').read()

# Function to encrypt a message using a key
def encrypt_message(message, key):
    f = Fernet(key)
    encrypted_message = f.encrypt(message.encode())
    return encrypted_message

# Function to decrypt a message using a key
def decrypt_message(encrypted_message, key):
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message).decode()
    return decrypted_message

# Check if encryption key exists, if not generate a new one
if not os.path.exists('Digital_Music.key'):
    key = generate_key()
    save_key(key)
else:
    key = load_key()

# Function to set up the database with users and recordings tables
def setup_database():
    conn = sqlite3.connect('Digital_Music.db')
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
        rating INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    conn.commit()
    conn.close()

# Function to register a new user
def register_user():
    conn = sqlite3.connect('Digital_Music.db')
    c = conn.cursor()

    username = input("Enter a new username: ")
    password = getpass.getpass("Enter a new password: ")

    encrypted_password = encrypt_message(password, key)

    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, encrypted_password))
        conn.commit()
        print("User registered successfully.")
        post_register_actions()
    except sqlite3.IntegrityError:
        print("Username already taken. Please try again.")
    finally:
        conn.close()

# Function to handle post-registration actions
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

# Function to login a user or admin
def login_user():
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        print("Admin login successful.")
        return 'admin'

    conn = sqlite3.connect('Digital_Music.db')
    c = conn.cursor()

    c.execute('SELECT id, password FROM users WHERE username = ?', (username,))
    user = c.fetchone()

    if user and decrypt_message(user[1], key) == password:
        print("Login successful.")
        conn.close()
        return user[0]
    else:
        print("Invalid username or password.")
        conn.close()
        return None

# Function to view a user's recordings
def view_files(user_id):
    conn = sqlite3.connect('digital_music.db')
    c = conn.cursor()

    c.execute('SELECT filename, timestamp, rating FROM recordings WHERE user_id = ?', (user_id,))
    files = c.fetchall()

    if files:
        print("Your recordings:")
        for file in files:
            print(f"Filename: {decrypt_message(file[0], key)}, Timestamp: {file[1]}, Rating: {file[2]}")
    else:
        print("No recordings found.")

    conn.close()

# Function for admin to view all recordings
def view_all_files():
    conn = sqlite3.connect('Digital_Music.db')
    c = conn.cursor()

    c.execute('SELECT users.username, recordings.filename, recordings.timestamp, recordings.rating FROM recordings JOIN users ON recordings.user_id = users.id')
    files = c.fetchall()

    if files:
        print("All recordings:")
        for file in files:
            print(f"Username: {file[0]}, Filename: {file[1]}, Timestamp: {file[2]}, Rating: {file[3]}")
    else:
        print("No recordings found.")

    conn.close()

# Function for admin to delete a recording
def delete_recording():
    conn = sqlite3.connect('Digital_Music.db')
    c = conn.cursor()

    recording_id = input("Enter the ID of the recording to delete: ")
    c.execute('DELETE FROM recordings WHERE id = ?', (recording_id,))
    conn.commit()
    conn.close()
    print("Recording deleted successfully.")

# Function to record audio and save it to a file
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

# Function to save recording metadata to the database
def save_to_database(user_id, filename):
    conn = sqlite3.connect('Digital_Music.db')
    c = conn.cursor()

    rating = random.randint(1, 10)
    c.execute('INSERT INTO recordings (user_id, filename, rating) VALUES (?, ?, ?)', (user_id, filename, rating))
    conn.commit()
    conn.close()

# Function to handle recording and saving audio
def record_and_save(user_id):
    filename = input("Enter the filename for the recording (without extension): ") + '.mp3'
    record_audio(filename)
    encrypted_filename = encrypt_message(filename, key)
    save_to_database(user_id, encrypted_filename)
    print("Recording saved successfully.")
    post_register_actions() if user_id == 'admin' else user_menu(user_id)

# Function to display the user menu
def user_menu(user_id):
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

# Main function to start the application
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
            user_menu(user_id)
    else:
        print("Invalid choice. Exiting.")

# Ensures that the main function is called when the script is run directly
if __name__ == '__main__':
    main()