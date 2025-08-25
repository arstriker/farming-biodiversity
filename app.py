from flask import Flask, render_template, request, jsonify
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io

# Load environment variables from .env file
# Try to load from current directory first
load_dotenv('.env')
# Also try the default behavior
load_dotenv()

app = Flask(__name__)

# --- Gemini API Configuration ---
api_key = os.getenv("GEMINI_API_KEY")

if not api_key or api_key == "YOUR_API_KEY_HERE":
    print("WARNING: GEMINI_API_KEY not found or not set. Please set it in your .env file.")
else:
    print("✅ Gemini API configured successfully!")
    genai.configure(api_key=api_key)

# --- Historical Data ---
try:
    with open('history.json', 'r') as f:
        historical_data = json.load(f)
except FileNotFoundError:
    historical_data = {"history": "No historical data found. Please create a history.json file."}
except json.JSONDecodeError:
    historical_data = {"history": "Error decoding history.json."}

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

def parse_gemini_response_to_json(response_text, expected_keys):
    """
    A more robust parser for Gemini responses that are expected to be in a JSON-like format.
    It tries to find a JSON block and parse it.
    """
    try:
        # Find the start and end of the JSON block
        json_start = response_text.find('```json')
        if json_start == -1:
            json_start = response_text.find('{')
        else:
            json_start += len('```json')
        json_end = response_text.rfind('```')
        if json_end == -1:
            json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end != -1:
            json_str = response_text[json_start:json_end].strip()
            # Let's try to parse it
            data = json.loads(json_str)
            # Basic validation
            if all(key in data for key in expected_keys):
                return data
    except json.JSONDecodeError:
        print("Failed to decode JSON from Gemini response.")
        return None # Indicate failure
    
    print("Could not find a valid JSON block in the response.")
    return None

@app.route('/analyze', methods=['POST'])
def analyze():
    if not api_key or api_key == "YOUR_API_KEY_HERE":
         return jsonify({"error": "API key is not configured on the server."}), 500

    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']
    text_input = request.form.get('text', '')

    try:
        image = Image.open(image_file.stream)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt_parts = [
            "You are an expert in agricultural science. Analyze the image and notes to identify plants. List them one per line. Do not add other text. If unsure, use 'Unknown Plant'.\n"
            "User's notes: " + (text_input if text_input else "None"),
            image,
        ]

        response = model.generate_content(prompt_parts)
        
        if not response.parts:
             return jsonify({"error": "Model response was blocked or empty."}), 500

        crops = []
        lines = response.text.strip().split('\n')
        for i, line in enumerate(lines):
            clean_line = line.strip().lstrip('*-123456789. ').strip()
            if clean_line:
                crops.append({"name": clean_line, "id": f"crop_{i}"})
        
        if not crops:
             return jsonify({"error": "Could not identify any crops."}), 500

        return jsonify({"identified_crops": crops})

    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/recommend', methods=['POST'])
def recommend():
    if not api_key or api_key == "YOUR_API_KEY_HERE":
         return jsonify({"error": "API key is not configured on the server."}), 500

    data = request.get_json()
    if not data or 'crops' not in data:
        return jsonify({"error": "No confirmed crops provided."}), 400

    confirmed_crops = data['crops']
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create the prompt
        prompt = (
            "You are an expert in agricultural biodiversity, polyculture, and sustainable farming.\n"
            "Based on the following information, recommend a list of compatible companion plants.\n\n"
            "**Current Confirmed Crops:**\n"
            f"- {', '.join(confirmed_crops)}\n\n"
            "**Historical Data for this Farmland Area:**\n"
            f"{json.dumps(historical_data, indent=2)}\n\n"
            "**Task:**\n"
            "Provide a list of 3-5 recommended companion plants. For each plant, provide a brief, practical explanation (2-3 sentences) of why it's a good companion, focusing on benefits like pest deterrence, soil health, structural support, or attracting beneficial insects.\n"
            "Format the response as a JSON object with a single key 'recommendations', which is a list of objects. Each object should have two keys: 'plant' (the name of the plant) and 'reason' (the explanation).\n"
            "Example format:\n"
            "```json\n"
            "{\n"
            '  "recommendations": [\n'
            '    {\n'
            '      "plant": "Example Plant",\n'
            '      "reason": "This is an example reason."\n'
            '    }\n'
            '  ]\n'
            '}\n'
            "```"
        )
        
        response = model.generate_content(prompt)
        
        if not response.parts:
            return jsonify({"error": "Model response was blocked or empty."}), 500
        
        # Use the JSON parser function
        recommendations_data = parse_gemini_response_to_json(response.text, ['recommendations'])
        if recommendations_data:
            return jsonify(recommendations_data)
        else:
            # Fallback for when JSON parsing fails
            return jsonify({"error": "Failed to parse the recommendation response from the model. The raw response was: " + response.text}), 500

    except Exception as e:
        print(f"An error occurred during recommendation: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)