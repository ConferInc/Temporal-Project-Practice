import os

def ensure_directory(path: str):
    os.makedirs(path, exist_ok=True)

def get_file_extension(file_path: str) -> str:
    return os.path.splitext(file_path)[1].lower().replace('.', '')

def is_pdf(file_path: str) -> bool:
    return get_file_extension(file_path) == 'pdf'

def is_image(file_path: str) -> bool:
    return get_file_extension(file_path) in ['jpg', 'jpeg', 'png', 'heic', 'tiff']
