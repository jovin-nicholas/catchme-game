import os
import jwt
from http import HTTPStatus
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta, timezone
from bson.objectid import ObjectId
from redis_lib import *

# This variable will store the application settings and
# made available globally (used by app_settings() method)
g = dict()

# Initialize the Flask application
app = Flask(__name__)

# Allow Cross Origin Resource Sharing with default settings
CORS(app)

# Initialize SocketIO for broadcasting service
socketio = SocketIO(app, cors_allowed_origins="*")

# To use Bcrypt APIs, wrap the Flask app in Bcrypt()
bcrypt = Bcrypt(app)

# This variable will store the application settings and
# made available globally (used by app_settings() method)
g = dict()

# List to track the broadcast receipents
broadcast_receipents = dict()

# ==========================================================
# +++ Application settings +++
# These values are used throughout the 
# application 
# Be mindful of what you change here ...
# ==========================================================

def app_settings():
    global g

    # User data
    user_id = 1001
    username = "Elon Musk"
    password = "Tesla"
    status = "inactive"
    latitude = "37.7749"
    longitude = "-79.5555"
    role = "Cop"

    # Store user location
    store_user_location(user_id, username, password, status, latitude ,longitude, role)
    
    # User data
    user_id = 1002
    username = "Jeff Bezos"
    password = "BlueHorizon"
    status = "inactive"
    latitude = "37.7749"
    longitude = "-79.5555"
    role = "Mafia"

    # Store user location
    store_user_location(user_id, username, password, status, latitude ,longitude, role)

    # User data
    user_id = 1003
    username = "Bill Gates"
    password = "Clippy"
    status = "inactive"
    latitude = "35.89"
    longitude = "-54.4194"
    role = "Mafia"

    # Store user location
    store_user_location(user_id, username, password, status, latitude ,longitude, role)

    # # User data
    # user_id = 1003
    # username = "Rey Misterio"
    # password = "rey"
    # status = "inactive"
    # latitude = "35.89"
    # longitude = "-54.4194"
    # store_user_location(user_id, username, password, status, latitude ,longitude)

    # This key will be used when encoding and decoding the 
    # access tokens
    if 'secret_key' not in g:
        g['secret_key'] = os.environ.get("SECRET_KEY", "5VfA[<v9]F<I{Tc^XibO")

    # This will be used with Bcrypt APIs
    # Higher values for bcrypt_log_rounds mean more secure hashes
    # but slower performance
    if 'bcrypt_log_rounds' not in g:
        g['bcrypt_log_rounds'] = os.environ.get("BCRYPT_LOG_ROUNDS", 12)

    # Define how long an access token remains valid
    # By default, set to 900 seconds (which is 15 minutes)
    if 'access_token_expiration' not in g:
        g['access_token_expiration'] = os.environ.get("ACCESS_TOKEN_EXPIRATION", 0)
    
    # Similar to access_token_expiration, but for refresh tokens
    # Refresh tokens typically have a longer lifespan than access tokens
    # By default, set to 2,592,000 seconds (which is 30 days)
    if 'refresh_token_expiration' not in g:
        g['refresh_token_expiration'] = os.environ.get("REFRESH_TOKEN_EXPIRATION", 2592000)

    # +++ DEBUG BLOCK: For debugging purposes only (REMOVE BEFORE DEPLOYING)
    
    # Create some users for the application
    if 'users' not in g:
        users = os.environ.get("USERS", 'Elon Musk,Bill Gates,Jeff Bezos')
        g['users'] = list(users.split(','))
        print("g['users'] = ", g['users'])
    
    # Create their passwords and hash them using Bcrypt API
    if 'passwords' not in g:
        passwords = os.environ.get("PASSWORDS", 'Tesla,Clippy,BlueHorizon')
        g['passwords'] = list(passwords.split(','))
        print("g['passwords'] = ", g['passwords'])

        g['password_hashes'] = []
        for p in g['passwords']:
            g['password_hashes'].append(
                bcrypt.generate_password_hash(p, g['bcrypt_log_rounds']).decode('utf-8')
            )
        print("g['password_hashes]=", g['password_hashes'])

        # Assign these users their user_id
        g['user_ids'] = list(range(0, len(g['users'])))

    if 'logged_user' not in g:
        g['logged_userId'] = None
        
    # +++ DEBUG BLOCK: For debugging purposes only (REMOVE BEFORE DEPLOYING)

# To make reading 'g' more clean, hide the functionality
# behind a method
def read_app_settings(setting_name):
    global g
    return g[setting_name]

# ==========================================================
# +++ Health-check Endpoint +++
# To test if the server is running and 
# accessible
# ==========================================================

@app.route("/health")
@cross_origin()
def health(): 
    return """
        <h3>
            If you are reading this message, then it means the server is up and 
        running!
        </h3>
        <h3>
            Happy cake day!! <3
        </h3>
    """

# ==========================================================
# +++ Methods to access the JSON Web Tokens +++
# Encode and decode the JWT
# ==========================================================
def encode_token(user_id, token_type):

    # Set token expiration time based on token_type
    if token_type == "access":
        expiration_time = read_app_settings("access_token_expiration")
    else:
        expiration_time = read_app_settings("refresh_token_expiration")

    # Define the contents of the token
    expiration_time = datetime.utcnow() + timedelta(seconds = expiration_time)
    issued_at =  datetime.utcnow()

    payload = {
        "expiration_time": expiration_time.timestamp(),
        "issued_at": issued_at.timestamp(),
        "subject": user_id,
    }

    # Encode the payload, create the token, and return it
    # For encoding, use the HMAC-SHA256 hashing algorithm
    return jwt.encode(
        payload, 
        read_app_settings("secret_key"), 
        algorithm = "HS256"
    )

def decode_token(token):
    
    # Decode the token (YES, it is 'algorithms' not 'algorithm')
    encoded_payload = jwt.decode(
        token, 
        read_app_settings("secret_key"), 
        algorithms = ["HS256"]
    )

    # If access_token_expiration is 0, convert the cookie to a session cookie
    expiration_time = 0

    # Convert expiration_time to UTC string to help setting cookies in
    # Javascript without any further convertion
    if read_app_settings('access_token_expiration'):
        expiration_time = datetime\
                            .fromtimestamp(encoded_payload['expiration_time'], timezone.utc)\
                            .strftime('%a, %d %b %Y %H:%M:%S UTC')
    
    # Do the same for issued_at
    issued_at = datetime\
                        .fromtimestamp(encoded_payload['issued_at'], timezone.utc)\
                        .strftime('%a, %d %b %Y %H:%M:%S UTC')

    decoded_payload = {
        "expiration_time": expiration_time,
        "issued_at": issued_at,
        "subject": encoded_payload['subject'],
    }

    return decoded_payload

# ==========================================================
# +++ Player Login Endpoint +++
# Sets the access tokens for the authenticated 
# players 
# ==========================================================
@app.route("/login", methods=["POST"])
@cross_origin()
def login():
    try:
        print("getting user details from request object..")
        user_name = request.json['name']
        print("got user_name ", user_name)
        password = request.json['password']
        print("got password ", password)
        role = request.json['role']
        print("got role ", role)

        # +++ DEBUG BLOCK: For debugging purposes only (REMOVE BEFORE DEPLOYING)
        
        # Get all users setup by app_settings()
        #old code
        # available_users = read_app_settings('users')

        #getting user credentials using redis
        print("getting user details... ")
        user = get_user_credentials(user_name)
        print("outside if: ", user)

        if user[1] == "":

            # +++ DEBUG BLOCK: For debugging purposes only (REMOVE BEFORE DEPLOYING)
            print('Unknown user trying to login ...')

            server_response = (
                "Error! This user does not have an account", 
                HTTPStatus.UNAUTHORIZED
            )
        else:

            # Get the user's hashed password from app_settings()
            password_hash = user[2]
            print("within else condition",user[2])
            # password_hash = read_app_settings('password_hashes')[available_users.index(user)]

            # Hash the user provided password and compare it with
            # password_hash
            # if not bcrypt.check_password_hash(password_hash, password):
            if password != password_hash:
                print("within else-if condition ",user[2])

                # Wrong password
                server_response = (
                    "ERROR: Password mismatch", 
                    HTTPStatus.UNAUTHORIZED
                )
            else:
                # Create the tokens for the user
                # user_id = read_app_settings('user_ids')[available_users.index(user)]
                user_id = user[0]
                
                access_token = encode_token(user_id, "access")
                print("else: access token ", access_token)
                refresh_token = encode_token(user_id, "refresh")
                expiration_time = decode_token(access_token)['expiration_time']
                g['logged_userId'] = user_id
                
                user_data = fetch_user_data(user_id)
                print(user_data)
                user_data[2] = "active"
                user_data[-1] = role

                update_user(user_id, user_data)
                
                # Prepare the tokens for serialization
                server_response = ({
                    "userId": user_id,
                    "role": role,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expiration_time": expiration_time
                }, HTTPStatus.OK)

        return jsonify(server_response)
    except Exception as e:

        # +++ DEBUG BLOCK: For debugging purposes only (REMOVE BEFORE DEPLOYING)
        print("Something went wrong in '/login' method")
        print(e)
        return jsonify((
            "Something went wrong in '/login' method", 
            HTTPStatus.INTERNAL_SERVER_ERROR
        ))


# ==========================================================
# +++ Location Endpoint +++
# To get location co-ordinates (along with
# other data) from players
# ==========================================================

@app.route("/location", methods = ["POST"])
@cross_origin()
def get_player_location():
    try:
       
        # Try getting the player details from the query parameters
        player_id = request.json['id']
        player_latitude = request.json['lat']
        player_longitude = request.json['lon']
        player_role = request.json['role']

         # Get the player details from the request and broadcast
        data = request.get_json()
        data['userId'] = player_id
        # socketio.emit('location_update', data)

        # +++ DEBUG BLOCK: For debugging purposes only (REMOVE BEFORE DEPLOYING)
        
        print("Player ID is ", player_id)
        print("Player Role is ", player_role)
        print("Player Latitude is ", player_latitude)
        print("Player Longitude is ", player_longitude)
        
        # +++ DEBUG BLOCK: For debugging purposes only (REMOVE BEFORE DEPLOYING)

        #debug
        print("before update location: ", player_id, player_latitude, player_longitude, player_role)
        #update the user's current location
        update_location(player_id, player_latitude, player_longitude, player_role)
         
        print("[DONE]update location")

        #Code to get data of all active users from redis
        active_users = get_active_users()

        # Create a dictionary with player details to send back as a response
        for item in active_users:
            for user_id, details in item.items():
                broadcast_receipents[user_id] = {
                    'role': details[-1],       # The last element in the list is the role
                    'latitude': details[-3],   # The third last element is the latitude
                    'longitude': details[-2]   # The second last element is the longitude
                }

        ############OLD CODE###########
        # broadcast_receipents[player_id] = {
        #     'role': player_role,
        #     'latitude': player_latitude,
        #     'longitude': player_longitude
        # }
        ############OLD CODE###########

        # Broadcast logged-in user's location to all connected users
        socketio.emit(
            'location_update', 
            {player_id: broadcast_receipents[player_id]}
        )
      
        # Return a HTTP 200 OK status with player details
        server_response = (broadcast_receipents[player_id], HTTPStatus.OK)

    except Exception as e:

        # +++ DEBUG BLOCK: For debugging purposes only (REMOVE BEFORE DEPLOYING)
        print("An exception occurred while receiving player location:")
        print(e)
        server_response = (
            "Exception occurred in '/location' route", 
            HTTPStatus.INTERNAL_SERVER_ERROR
        )
        # +++ DEBUG BLOCK: For debugging purposes only (REMOVE BEFORE DEPLOYING)

    return jsonify(server_response)

# ==========================================================
# +++ Broadcast handler +++
# Handle broadcast connection
# ==========================================================
@socketio.on('connect')
def handle_connect():
    emit('all_users', broadcast_receipents)
    
# ==========================================================
# +++ App pre-run configuration +++
# ==========================================================

# !! DEPRECATED !!
# @app.before_first_request
# This annotation no longer works

def before_first_request():
    print("Starting python server for the first time")
    app_settings()

# Instead use app.app_context()
with app.app_context():
    before_first_request()


# ==========================================================
# +++ TO RUN THIS FILE, RUN wsgi.py FILE +++
# ==========================================================
