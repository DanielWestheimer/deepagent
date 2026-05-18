import webview
import threading
import uvicorn
import time
import requests
import socket

from main import app_api

PORT = 8000
HOST = "127.0.0.1"
URL = f"http://{HOST}:{PORT}"

def is_port_free(port):
    """בודק אם הפורט פנוי או שרת כבר רץ עליו"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) != 0

def run_server():
    """מפעיל את השרת שלנו"""
    uvicorn.run(app_api, host=HOST, port=PORT, log_level="error")

def wait_for_server():
    """מוודא שהשרת באוויר לפני פתיחת החלון"""
    timeout = 10
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(URL)
            if response.status_code == 200:
                print("✅ שרת ה-Backend מוכן ומזומן!")
                return True
        except requests.ConnectionError:
            time.sleep(0.2)
            
    print("❌ שגיאה: שרת ה-Backend לא עלה בזמן.")
    return False

if __name__ == "__main__":
    print("🚀 מתחיל טעינה של Deep Agent...")

    if not is_port_free(PORT):
        print(f"⚠️ פורט {PORT} תפוס (השרת כבר רץ). פותח את החלון ישירות...")
        window = webview.create_window(
            title="Deep Agent",
            url=URL,
            width=1100,
            height=800,
            background_color="#1e1e2e"
        )
        webview.start(debug=False, http_server=False)
        
    else:
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        if wait_for_server():
            window = webview.create_window(
                title="Deep Agent",
                url=URL,
                width=1100,
                height=800,
                background_color="#1e1e2e"
            )
            webview.start(debug=False, http_server=False)
        else:
            print("לא ניתן לפתוח את חלון האפליקציה כי השרת לא הגיב.")