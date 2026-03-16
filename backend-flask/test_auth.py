import os
from auth_service import authenticate_user, create_user_token

username = os.getenv("TEST_USERNAME", "employee1")
password = os.getenv("TEST_PASSWORD", "CHANGE_ME")

user = authenticate_user(username, password)
if user:
    token = create_user_token(user)
    print("Login successful! JWT Token:", token)
else:
    print("Invalid username or password")