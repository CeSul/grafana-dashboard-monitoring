import os
from autogen import ConversableAgent
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from PIL import Image
import time
import base64
import tempfile
import shutil
from io import BytesIO
import requests
import json

load_dotenv()

class HPCGrafanaMonitor:
    def __init__(self):
        self.dashboard_url = "https://hpc-grafana.usc.edu"
        self.screenshot_path = "dashboard_screenshot.png"
        self.temp_dir = tempfile.mkdtemp()
        self.setup_selenium()
        
    def setup_selenium(self):
        try:
            firefox_options = Options()
            firefox_options.add_argument("--headless")
            firefox_options.add_argument("--width=1920")
            firefox_options.add_argument("--height=1080")
            
            # Use GeckoDriverManager to automatically handle driver installation
            service = Service(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
        except Exception as e:
            print(f"Error setting up Selenium: {str(e)}")
            raise
        
    def capture_dashboard(self):
        try:
            self.driver.get(self.dashboard_url)
            time.sleep(5)  # Wait for dashboard to load
            self.driver.save_screenshot(self.screenshot_path)
        except Exception as e:
            print(f"Error capturing dashboard: {str(e)}")
            raise
        
    def get_screenshot_base64(self):
        try:
            with open(self.screenshot_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error reading screenshot: {str(e)}")
            raise
        
    def close(self):
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
            # Clean up temporary directory
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

def analyze_with_groq(image_base64):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",  # Updated to use specified Meta Llama model
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this HPC Grafana dashboard screenshot. If any system usage metrics are above 80%, generate a detailed report. Otherwise, just confirm that everything is normal."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }
    
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code != 200:
        raise Exception(f"Groq API error: {response.text}")
    
    return response.json()["choices"][0]["message"]["content"]

def main():
    monitor = HPCGrafanaMonitor()
    
    try:
        # Capture dashboard
        monitor.capture_dashboard()
        screenshot_base64 = monitor.get_screenshot_base64()
        
        # Analyze with Groq
        response = analyze_with_groq(screenshot_base64)
        print(response)
        
    finally:
        monitor.close()

if __name__ == "__main__":
    main() 