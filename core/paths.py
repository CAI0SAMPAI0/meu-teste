import os

def get_user_data_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "Study Practices")
    os.makedirs(path, exist_ok=True)
    return path
