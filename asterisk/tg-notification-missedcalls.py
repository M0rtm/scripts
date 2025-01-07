# Designed by Dmytro Fedorov, 2025

# The script is designed to notify you of missed calls (asterisk) to the Telegram group. This script checks the notification queue 
# table <tg_notification_mc_queue> every 10 seconds, if a new entry appears in the table, it sends a notification to the telegram group 
# and deletes the entry from the table. 
# Works in combination with a trigger to process the <asterisk.queue_log> table


import mysql.connector # type: ignore
import requests # type: ignore
import time

# configure connection to db mysql
db_config = {
    'host': 'localhost',
    'user': 'db-user',
    'password': 'db-pass',
    'database': 'db-asterisk',
}

# Configure Telegram
telegram_token = 'YOU TG TOKEN'
telegram_chat_id = 'CHAT ID'
telegram_api_url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'

def send_telegram_message(chat_id, text):
    response = requests.post(telegram_api_url, json={
        'chat_id': chat_id,
        'text': text,
    })
    if response.status_code == 200:
        print(f"Message has been sent: {text}")
    else:
        print(f"Error sending the message: {response.text}")

def process_notifications():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)

    try:
        # Get record from queue
        cursor.execute("SELECT * FROM tg_notification_mc_queue")
        rows = cursor.fetchall()

        for row in rows:
            message = f"Missed call from number: \"{row['number']}\"\nClient: \"{row['client_description']}\""
            send_telegram_message(telegram_chat_id, message)
            
            # Delete a processed record
            cursor.execute("DELETE FROM tg_notification_mc_queue WHERE id = %s", (row['id'],))
            connection.commit()

    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    while True:
        process_notifications()
        time.sleep(10)  # check every 10 sec
