import os
import uuid
from app.config import Config

def save_file(file):
    try:
        file_id = str(uuid.uuid4())
        file_path = os.path.join(Config.UPLOAD_FOLDER, file_id + "_" + file.filename)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file.save(file_path)
        return file_id
    except Exception as e:
        print(f"Error saving file: {e}")
        raise
