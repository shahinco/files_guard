### JSON file protection script 
#  Create log file  sudo touch /var/log/config_guard.log && chmod 644 /var/log/config_guard.log 

import os
import json
import shutil
import hashlib
from datetime import datetime

# Paths
CONFIG_PATH = '/etc/audiobridge/config.json'
BACKUP_PATH = '/etc/audiobridge/config.json.backup'
MD5_PATH = '/etc/audiobridge/config.json.md5'
SIZE_PATH = '/etc/audiobridge/config.json.size'
TIMESTAMP_PATH = '/etc/audiobridge/config.json.timestamp'
LOG_PATH = '/var/log/config_guard.log'

def log(message):
    timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    # full_message = f"[{timestamp}], {message}"  //strange syntax error.. 
    full_message = "[{}], {}".format(timestamp, message)
    try:
        with open(LOG_PATH, 'a') as log_file:
            log_file.write(full_message + '\n')
    except PermissionError:
        print f("[ERROR] Cannot write to log file {LOG_PATH}".format(LOG_PATH))
        # print f("[ERROR] Cannot write to log file: {LOG_PATH}")
    print(full_message)

def is_json_valid(file_path):
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        return True
    except Exception:
        return False

def compute_md5(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except IOError:
        return None

def get_file_size(file_path):
    try:
        return os.path.getsize(file_path)
    except IOError:
        return None

def read_file(path):
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except IOError:
        return None

def write_file(path, data):
    with open(path, 'w') as f:
        f.write(str(data))


def make_backup():
    shutil.copy2(CONFIG_PATH, BACKUP_PATH)
    md5 = compute_md5(CONFIG_PATH)
    size = get_file_size(CONFIG_PATH)
    timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    
    if md5 and size is not None:
        write_file(MD5_PATH, md5)
        write_file(SIZE_PATH, size)
        write_file(TIMESTAMP_PATH, timestamp)
        log("BACKUP: config.json backed up at {} (MD5: {}, Size: {} bytes)".format(timestamp, md5, size))
        

def restore_backup():
    if os.path.exists(BACKUP_PATH):
        backup_time = read_file(TIMESTAMP_PATH)
        shutil.copy2(BACKUP_PATH, CONFIG_PATH)
        if backup_time:
            log("RESTORE: config.json restored from backup taken at {}".format(backup_time))
        else:
            log("RESTORE: config.json restored from backup (timestamp unknown)")
    else:
        log("ERROR: No backup found to restore.")

def main():
    if not os.path.exists(CONFIG_PATH):
        log("ERROR: config.json not found.")
        return

    if not is_json_valid(CONFIG_PATH):
        log("WARNING: config.json is not valid JSON. Attempting to restore from backup.")
        restore_backup()
        return

    current_md5 = compute_md5(CONFIG_PATH)
    saved_md5 = read_file(MD5_PATH)

    current_size = get_file_size(CONFIG_PATH)
    saved_size = read_file(SIZE_PATH)
    saved_size = int(saved_size) if saved_size and saved_size.isdigit() else None

    if current_md5 != saved_md5:
        log("MD5 has changed. Creating Нew Backup...")
        make_backup()
    elif current_size != saved_size:
        log("Size has changed. Creating New Backup...")
        make_backup()
    else:
        log("config.json Unchanged. No backup needed.")

if __name__ == '__main__':
    main()
