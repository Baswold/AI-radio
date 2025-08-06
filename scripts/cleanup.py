import os
import shutil
import time

MEDIA_FOLDER = os.environ.get('MEDIA_FOLDER', '/Users/basil_jackson/Documents/ai_radio/media')
ARCHIVE_FOLDER = os.path.join(MEDIA_FOLDER, 'archive')
DAYS_UNPLAYED = int(os.environ.get('DAYS_UNPLAYED', '30'))

if not os.path.exists(ARCHIVE_FOLDER):
    os.makedirs(ARCHIVE_FOLDER)

def should_archive(file_path):
    # Archive files not accessed in DAYS_UNPLAYED days
    last_access = os.path.getatime(file_path)
    return (time.time() - last_access) > DAYS_UNPLAYED * 86400

def archive_old_files():
    for subdir in ['audio', 'video', 'dj_intros', 'uploads/pending']:
        folder = os.path.join(MEDIA_FOLDER, subdir)
        if not os.path.exists(folder):
            continue
        for fname in os.listdir(folder):
            fpath = os.path.join(folder, fname)
            if os.path.isfile(fpath) and should_archive(fpath):
                shutil.move(fpath, os.path.join(ARCHIVE_FOLDER, fname))
                print(f'Archived: {fpath}')

if __name__ == '__main__':
    archive_old_files()
