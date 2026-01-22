import os
import shutil
from fastapi import UploadFile

# Setup Uploads Directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Navigate up from backend/app/services -> backend/app -> backend -> .. -> uploads
# Actually, let's keep it relative to the app root cleanly.
# Old path: backend/app/main.py -> .. -> uploads (backend/uploads)
# New path: backend/app/services/files.py -> .. -> .. -> uploads (backend/uploads)
UPLOAD_ROOT = os.path.join(BASE_DIR, "..", "..", "uploads")
os.makedirs(UPLOAD_ROOT, exist_ok=True)

def get_upload_root():
    return UPLOAD_ROOT

def save_application_file(app_id: str, uf: UploadFile, label: str):
    app_dir = os.path.join(UPLOAD_ROOT, app_id)
    os.makedirs(app_dir, exist_ok=True)
    
    ext = os.path.splitext(uf.filename)[1]
    safe_name = f"{label}{ext}"
    path = os.path.join(app_dir, safe_name)
    
    with open(path, "wb") as buffer:
        shutil.copyfileobj(uf.file, buffer)
        
    return path, f"/static/{app_id}/{safe_name}"

def delete_application_files(app_id: str):
    app_dir = os.path.join(UPLOAD_ROOT, app_id)
    if os.path.exists(app_dir) and os.path.isdir(app_dir):
        shutil.rmtree(app_dir)
