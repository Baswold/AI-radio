import os
import requests
import sqlite3

def check_database(db_url):
    try:
        if db_url.startswith('sqlite:///'):
            db_path = db_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            conn.execute('SELECT 1')
            conn.close()
            return True
        # Add other DB checks as needed
    except Exception as e:
        print(f'Database check failed: {e}')
        return False

def check_streaming_server(url):
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f'Streaming server check failed: {e}')
        return False

def check_ai_brain(url):
    try:
        r = requests.get(url + '/health', timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f'AI Brain check failed: {e}')
        return False

def main():
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///ai_radio.db')
    stream_url = os.environ.get('ICECAST_STREAM_URL', 'http://localhost:8000/stream')
    ai_brain_url = os.environ.get('AI_BRAIN_URL', 'http://localhost:8080')

    print('Database:', 'OK' if check_database(db_url) else 'FAIL')
    print('Streaming Server:', 'OK' if check_streaming_server(stream_url) else 'FAIL')
    print('AI Brain:', 'OK' if check_ai_brain(ai_brain_url) else 'FAIL')

if __name__ == '__main__':
    main()
