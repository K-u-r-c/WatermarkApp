import webbrowser
from threading import Timer
from waitress import serve
from watermark_project.wsgi import application


def open_browser():
    webbrowser.open_new("http://localhost:8080/")


if __name__ == "__main__":
    Timer(1, open_browser).start()
    serve(application, host="0.0.0.0", port=8080)

# pyinstaller --onefile --hidden-import=babel.numbers --hidden-import=whitenoise --add-data="templates:templates" --distpath=./build/dist --workpath=./build/work local_main.py
