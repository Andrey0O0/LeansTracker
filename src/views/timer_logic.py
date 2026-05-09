import threading
import time
import flet as ft

def format_time(seconds):
    h = seconds // 3600 
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"
