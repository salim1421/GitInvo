import sys
import os

APP_DIR = os.path.join(os.getenv("APPDATA") or os.getcwd(), "GitInvo")
DB_NAME = os.path.join(APP_DIR, "myinventory.db")
BACKUP_DIR = os.path.join(APP_DIR, "backups")
LICENSE_FILE = os.path.join(APP_DIR, "license.key")


def resource_path(relative_path):
    """Gets the correct path whether running as script or bundled .exe"""
    if hasattr(sys, '_MEIPASS'):
        # Running as bundled .exe — PyInstaller extracts files here
        return os.path.join(sys._MEIPASS, relative_path)
    # Running as normal script
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

