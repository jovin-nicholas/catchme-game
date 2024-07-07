import redis
import os

# Connect to Redis
# redis_url = os.environ.get("DATABASE_URL", 'redis://localhost:6379/')
# client = redis.from_url(redis_url)
client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

def store_user_location(user_id, username, password, status, latitude, longitude, role):
    """
    Store the user's location as a list in Redis.

    Args:
        user_id (str): The user's unique identifier.
        username (str): The user's username.
        password (str): The user's password.
        latitude (float): The user's latitude.
        longitude (float): The user's longitude.
        role (str): The user's role.
    """
    # List of user data
    print("Inside store_user user_id ", user_id)
    user_data = [username, password, status, latitude, longitude, role]
    key = f"users:{user_id}"
    client.delete(key)
    client.rpush(key, *user_data)

def fetch_user_data(user_id):
    """
    Fetch the user's data from Redis.

    Args:
        user_id (str): The user's unique identifier.

    Returns:
        list: A list containing the latitude and longitude.
    """
    key = f"users:{user_id}"
    print(key)
    data = client.lrange(key, 0, -1)
    print("Len of data and data: ", len(data), data)
    return data

def get_active_users():
    """
    Fetches all active users from redis db
    """
    cursor = '0'
    active_users = []

    while True:
        cursor, keys = client.scan(cursor=cursor, match='users:*')
        for key in keys:
            user_data = client.lrange(key, 0, -1)  # Get the entire list
            # user_data = [item.decode('utf-8') for item in user_data]

            # print(user_data)
            if len(user_data) >2 and user_data[2] == 'active':  # Assuming status is the second element
                active_users.append({key.split(':')[1]: user_data})

        if cursor == 0:
            break

    # print(active_users)

    return active_users

def get_all_users():
    """
    Fetches all users from redis db
    """
    cursor = '0'
    available_users = []

    while True:
        cursor, keys = client.scan(cursor=cursor, match='users:*')
        for key in keys:
            user_data = client.lrange(key, 0, -1)
            available_users.append({key: user_data})

        if cursor == 0:
            break

    # print(available_users)

    return available_users

def delete_user(user_id):
    """
    deletes a user with a particular user_id
    """
    cursor = '0'

    while True:
        cursor, keys = client.scan(cursor=cursor, match='users:*')
        for key in keys:
            if key == 'users:'+ user_id:
                user_data = client.lrange(key, 0, -1)
                deleted_count = client.delete(key)
                # Check if key was deleted
                if deleted_count == 1:
                    print(f"User with user_id {user_id} deleted successfully.")
                else:
                    print(f"User with user_id {user_id} not found.")
                break

        if cursor == 0:
            print("No matching keys")
            break

    print("remaining users: ", get_all_users())

def update_user(user_id, user_data):
    """
    updates a user with a particular user_id
    """
    cursor = '0'

    while True:
        cursor, keys = client.scan(cursor=cursor, match='users:*')
        for key in keys:
            # print("key : ", key, " user_id: ", user_id)
            if key.split(':')[1] == user_id:
                user_data_new = [user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5]]
                print("user_data_new: ", user_data_new)
                store_user_location(key.split(':')[1], *user_data_new)
                print("updated user succesfully! ", user_data_new)
                break

        if cursor == 0:
            break
    
def get_user_credentials(user_name):
    all_users = get_all_users()
    user_credentials = ["","",""]
    print(all_users)
    for user in all_users:
        for k,v in user.items():
            if user_name == v[0]:
                user_credentials = [k.split(':')[1], user_name, v[1]]
                break
    print(user_credentials)
    return user_credentials

def update_location(user_id, latitude, longitude, role):
    user_data = fetch_user_data(user_id)
    print("within-> before updating location: user_data", user_data)
    #change latitude
    user_data[3] = latitude
    #change longitude
    user_data[4] = longitude
    #change longitude
    user_data[5] = role
    
    user_data_new = user_data[:6]
    print("within -> after updating location: user_data", user_data_new)
    store_user_location(user_id, *user_data_new)

    print("Location for the user: ", user_data[0], " updated successfully!")
    
def fetch_user_location(user_id):
    print("Inside fetch_user_location user_id ", user_id)
    user_data = fetch_user_data(user_id)
    print(user_data)
    location = (user_data[3], user_data[4])
    # print(location)
    return location
# User data
# user_id = 1003
# username = "john_doe"
# password = "secure_password"
# status = "active"
# latitude = "37.7749"
# longitude = "-79.5555"

# Store user location
# store_user_location(user_id, username, password, status, latitude ,longitude)

# User data
# user_id = 1002
# username = "mary_kom"
# password = "secure_password"
# status = "active"
# latitude = "35.89"
# longitude = "-54.4194"
