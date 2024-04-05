from waitress import serve
from watermark_project.wsgi import application

if __name__ == "__main__":
    serve(application, host="0.0.0.0", port=8080)

# pyinstaller --onefile --hidden-import=babel.numbers --add-data="templates:templates" local_main.py
