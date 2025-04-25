from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv
import os

load_dotenv()  

app = Flask(__name__)

VERIFY_TOKEN       = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN  = os.getenv("PAGE_ACCESS_TOKEN")
CHATBOT_API_URL    = os.getenv("CHATBOT_API_URL")

# Endpoint for Facebook to verify your webhook (GET request)
@app.route("/webhook", methods=["GET"])
def verify():
    # Facebook sends a 'hub.mode', 'hub.verify_token', and 'hub.challenge'
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            return "Verification token mismatch", 403
    return "Missing parameters", 400

# Endpoint to receive messages from Facebook (POST request)
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json()
    # Log the payload for debugging
    print("Received payload:", payload)
    
    # Process each entry in the webhook payload
    if payload.get("object") == "page":
        for entry in payload.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"].get("text")
                    # Forward the message to your chatbot API
                    response_text = forward_to_chatbot(message_text)
                    # Send the chatbot's response back to Messenger
                    send_message(sender_id, response_text)
        return "EVENT_RECEIVED", 200
    else:
        return "Not a page subscription", 404

def forward_to_chatbot(message):
    """
    Forward the user's message to your chatbot API.
    Adjust the payload format as required by your chatbot.
    """
    try:
        response = requests.post(CHATBOT_API_URL, json={"message": message})
        if response.status_code == 200:
            # Adjust this to match your API's response structure
            return response.json().get("reply", "Sorry, I didn't understand that.")
        else:
            return "Error contacting chatbot API."
    except Exception as e:
        print("Error forwarding to chatbot:", e)
        return "Error processing your request."

def send_message(recipient_id, message_text):
    """
    Send a message back to the Facebook Messenger user.
    You must set up your Page Access Token from Facebook.
    """
    post_message_url = "https://graph.facebook.com/v12.0/me/messages?access_token=" + PAGE_ACCESS_TOKEN
    response_msg = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    try:
        response = requests.post(post_message_url, json=response_msg)
        print("Message sent:", response.json())
    except Exception as e:
        print("Error sending message:", e)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

