# Designed by Dmytro Fedorov, 2024
# This script is designed to receive an admin token, 
# logout (clear active sessions) all users except the list of admins,
# and stop the service to prevent re-logins.

import requests  # type: ignore
import os
import subprocess
import time

# Configuration the server and administrator credentials
homeserver_url = "http://localhost:8008"
admin_username = "@admin:matrix.your.domain"  # user with admin privileges
admin_password = "admin pass"  # admin password 
admin_users = ["@admin:matrix.your.domain", "@admin2:matrix.your.domain"]  # admins list

# Parameter's for getting admin token
def get_admin_token():
    login_url = f"{homeserver_url}/_matrix/client/r0/login"
    login_payload = {
        "type": "m.login.password",
        "user": admin_username,
        "password": admin_password
    }
    response = requests.post(login_url, json=login_payload)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("Failed to get an administrator token:", response.text)
        exit()

# get token
admin_token = get_admin_token()

headers = {
    "Authorization": f"Bearer {admin_token}",
    "Content-Type": "application/json"
}

# get list for all users
response = requests.get(f"{homeserver_url}/_synapse/admin/v2/users", headers=headers)
if response.status_code != 200:
    print("Failed to get an users list:", response.text)
    exit()

users = response.json().get('users', [])

all_devices_removed = True

# go through all users
for user in users:
    user_id = user['name']

    # skip admins
    if user_id in admin_users:
        print(f"Skip admins list: {user_id}")
        continue

    # get list all user devices
    devices_response = requests.get(
        f"{homeserver_url}/_synapse/admin/v2/users/{user_id}/devices",
        headers=headers
    )
    if devices_response.status_code != 200:
        print(f"Could not get devices for {user_id}: {devices_response.text}")
        all_devices_removed = False
        continue

    devices = devices_response.json().get('devices', [])

    # Remove each device
    for device in devices:
        device_id = device['device_id']
        delete_response = requests.delete(
            f"{homeserver_url}/_synapse/admin/v2/users/{user_id}/devices/{device_id}",
            headers=headers
        )
        if delete_response.status_code == 200:
            print(f"Device {device_id} for {user_id} successfully removed.")
        else:
            print(f"Unable to remove the device {device_id} for {user_id}: {delete_response.text}")
            all_devices_removed = False

print("Script finished.")

# Add a delay to make sure all devices are deleted
if all_devices_removed:
    print("All devices are successfully deleted. Waiting 5 seconds before stopping the service...")
    time.sleep(5)

# Stop service matrix-synapse
try:
    print("Stoping service matrix-synapse...")
    subprocess.run(["systemctl", "stop", "matrix-synapse"], check=True)
    print("Service matrix-synapse successfully stoped.")
except subprocess.CalledProcessError as e:
    print(f"Failed to stop the service matrix-synapse: {e}")