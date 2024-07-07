# The wsgi.py file creates an application object (or callable) for the Gunicorn server
# so that the server can use it. Each time a request comes, the server uses this application 
# object to run the application’s request handlers upon parsing the URL.

# Import the Flask app from gameserver.py
from gameserver import app, socketio, threading, game_timer

# Run the application from the main() method
def main() -> None:
    app_host = '0.0.0.0'
    app_port = 5000
    app_debug_state = True

    timer_thread = threading.Thread(target=game_timer)
    timer_thread.start()

    socketio.run(
        app, 
        host = app_host, 
        port = app_port, 
        debug = app_debug_state,
        allow_unsafe_werkzeug = True
    )

# Application entrypoint
if __name__ == '__main__':
    main()
