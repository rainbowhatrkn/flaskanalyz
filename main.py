from flask import Flask, render_template, request, jsonify
import openai
from dotenv import load_dotenv
import os
import random
import requests
from user_agents import parse

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# List of OpenAI API keys
API_KEYS = [
    os.getenv("OPENAI_API_KEY"),
    os.getenv("OPENAI_API_KEY_2"),
    os.getenv("OPENAI_API_KEY_3")
]

def get_random_api_key():
    """Select a random API key from the list."""
    return random.choice(API_KEYS)

def get_ip_info(ip):
    """Get geolocation information for an IP address using ipgeolocation.io."""
    ipgeolocation_api_key = os.getenv("IPGEOLOCATION_API_KEY")
    response = requests.get(f"https://api.ipgeolocation.io/ipgeo?apiKey={ipgeolocation_api_key}&ip={ip}")
    return response.json()

def analyze_user_agent(user_agent_string):
    """Analyze the user agent to determine device type."""
    user_agent = parse(user_agent_string)
    return {
        'is_mobile': user_agent.is_mobile,
        'is_tablet': user_agent.is_tablet,
        'is_pc': user_agent.is_pc,
        'is_bot': user_agent.is_bot,
        'browser': user_agent.browser.family,
        'os': user_agent.os.family,
        'device': user_agent.device.family
    }

def get_visitor_ip():
    """Get the real IP address of the visitor."""
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        ip = request.remote_addr
    return ip

@app.route('/')
def index():
    """Serve the main page and analyze the visitor's IP."""
    visitor_ip = get_visitor_ip()
    user_agent_string = request.headers.get('User-Agent')

    # Get geolocation data
    ip_info = get_ip_info(visitor_ip)
    location = f"{ip_info.get('city', 'Unknown')}, {ip_info.get('country_name', 'Unknown')}"

    # Analyze user agent
    device_info = analyze_user_agent(user_agent_string)

    # Create a summary of the data to send to GPT-4
    messages = [
        {"role": "system", "content": "You are a helpful assistant for analyzing network connections."},
        {"role": "user", "content": (
            f"Analyze the following connection:\n"
            f"IP Address: {visitor_ip}\n"
            f"Location: {location}\n"
            f"Device: {device_info['device']} (Mobile: {device_info['is_mobile']}, Tablet: {device_info['is_tablet']}, PC: {device_info['is_pc']}, Bot: {device_info['is_bot']})\n"
            f"Browser: {device_info['browser']}\n"
            f"Operating System: {device_info['os']}\n"
            f"Please provide insights on this connection."
        )}
    ]

    # Make the request to the OpenAI API
    openai.api_key = get_random_api_key()
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=150
    )

    # Pass the analysis result to the template
    analysis = {
        'visitor_ip': visitor_ip,
        'location': location,
        'device_info': device_info,
        'analysis': response['choices'][0]['message']['content'].strip()
    }

    return render_template('index.html', analysis=analysis)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze incoming connection data."""
    data = request.json
    ip_address = data.get('ip', '')
    user_agent_string = data.get('user_agent', '')

    # Get geolocation data
    ip_info = get_ip_info(ip_address)
    location = f"{ip_info.get('city', 'Unknown')}, {ip_info.get('country_name', 'Unknown')}"

    # Analyze user agent
    device_info = analyze_user_agent(user_agent_string)

    # Create a summary of the data to send to GPT-4
    messages = [
        {"role": "system", "content": "You are a helpful assistant for analyzing network connections."},
        {"role": "user", "content": (
            f"Analyze the following connection:\n"
            f"IP Address: {ip_address}\n"
            f"Location: {location}\n"
            f"Device: {device_info['device']} (Mobile: {device_info['is_mobile']}, Tablet: {device_info['is_tablet']}, PC: {device_info['is_pc']}, Bot: {device_info['is_bot']})\n"
            f"Browser: {device_info['browser']}\n"
            f"Operating System: {device_info['os']}\n"
            f"Please provide insights on this connection."
        )}
    ]

    # Make the request to the OpenAI API
    openai.api_key = get_random_api_key()
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=150
    )

    return jsonify({
        'analysis': response['choices'][0]['message']['content'].strip(),
        'location': location,
        'device_info': device_info
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))