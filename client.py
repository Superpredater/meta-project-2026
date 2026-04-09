import requests

BASE_URL = "http://localhost:8000"

def reset():
    response = requests.post(f"{BASE_URL}/reset")
    return response.json()

def step(action: dict):
    response = requests.post(f"{BASE_URL}/step", json=action)
    return response.json()

if __name__ == "__main__":
    obs = reset()
    print("Initial observation:", obs)