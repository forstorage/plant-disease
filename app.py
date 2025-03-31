from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import base64
import time

app = Flask(__name__)
CORS(app)

API_KEY = "R6sRLGUH35rKcydFbjwE4XbBjfSq5IHqgpw7NRCRzr0N4WGo26"
BASE_URL = "https://plant.id/api/v3/identification"

def analyze_plant(image_data):
    try:
        # Step 1: Create identification request
        headers = {
            "Api-Key": API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "images": [image_data],
            "health": "all",
            "symptoms": True,
            "similar_images": True
        }

        # Create identification
        response = requests.post(BASE_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        identification = response.json()

        if not identification.get('access_token'):
            return {"error": "Failed to get access token"}

        access_token = identification['access_token']
        print(f"Access Token: {access_token}")

        # Step 2: Initialize conversation with proper question
        chat_url = f"{BASE_URL}/{access_token}/conversation"
        chat_payload = {
            "question": "Please analyze this plant for diseases and suggest treatment.",
            "prompt": "Provide detailed response about diseases and treatment.",
            "temperature": 0.3,
            "app_name": "PlantMD"
        }

        # Retry logic for conversation initialization
        max_retries = 5
        chat_data = None
        
        for _ in range(max_retries):
            chat_response = requests.post(  # Changed to POST
                chat_url,
                headers=headers,
                json=chat_payload,
                timeout=25
            )
            
            if chat_response.status_code == 404:
                print("Conversation not ready, retrying...")
                time.sleep(3)
                continue
                
            chat_response.raise_for_status()
            chat_data = chat_response.json()
            break

        if not chat_data:
            return {
                "identification": identification,
                "warning": "Disease analysis took too long, showing basic results"
            }

        return {
            "identification": identification,
            "chatbot": chat_data
        }

    except requests.exceptions.HTTPError as e:
        return {"error": f"API Error: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Invalid file"}), 400

    try:
        image_data = base64.b64encode(file.read()).decode('utf-8')
        result = analyze_plant(image_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
handler = app