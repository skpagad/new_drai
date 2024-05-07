import json
import bcrypt
import logging
import re  # Import regex module

def hash_password(password):
    """Hash a password for storing."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode('utf-8')

def is_password_valid(password):
    """Check password validity based on given criteria."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    return True, ""

def save_user(s3_client, username, password, user_type, email, S3_BUCKET_NAME):
    valid, message = is_password_valid(password)
    if not valid:
        logging.error("Password validation failed: %s", message)
        return False, message
    hashed_password = hash_password(password)
    user_data = {
        'username': username,
        'password': hashed_password,
        'type': user_type,
        'email': email  # Add email to user data
    }
    try:
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=f'users/{user_type}/{username}.json',
                             Body=json.dumps(user_data))
        return True, "User saved successfully."
    except Exception as e:
        logging.error("Failed to save user: %s", e)
        return False, str(e)


# Other functions remain the same


# The rest of the functions such as verify_user_password, check_user_exists, and delete_user 
# can be similarly updated with proper exception handling and logging.
#     
def verify_user_password(stored_password, provided_password):
    stored_password_bytes = stored_password.encode('utf-8')
    provided_password_bytes = provided_password.encode('utf-8')
    result = bcrypt.checkpw(provided_password_bytes, stored_password_bytes)
    print("Retrieved hashed password:", stored_password)  # Use stored_password to show the hash used in verification
    return result

    
def check_user_exists(s3_client, username, user_type, S3_BUCKET_NAME):
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=f'users/{user_type}/{username}.json')
        user_data = json.load(response['Body'])
        if 'password' in user_data:
            print("Retrieved password hash:", user_data['password'])
            return True, user_data
        else:
            print("Password not found in retrieved data")
            return False, None
    except Exception as e:
        print(f"Failed to retrieve user data: {str(e)}")
        return False, None
