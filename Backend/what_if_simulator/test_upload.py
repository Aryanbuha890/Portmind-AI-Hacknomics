import requests

url = 'http://localhost:8000/upload'
files = {'file': open('E:\\Portmind-AI-Hacknomics\\Backend\\wagon number detection\\vids\\4.MP4', 'rb')}

try:
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
