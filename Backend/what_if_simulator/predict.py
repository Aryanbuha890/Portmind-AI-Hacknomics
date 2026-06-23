import os
import requests
import joblib
import pandas as pd
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

# File paths for the saved models
MODEL_PATHS = {
    'crane': 'crane_model.pkl',
    'vessel': 'vessel_model.pkl',
    'rail': 'rail_model.pkl'
}

def load_models():
    """Load the three trained models from disk."""
    models = {}
    for name, path in MODEL_PATHS.items():
        if os.path.exists(path):
            models[name] = joblib.load(path)
        else:
            raise FileNotFoundError(f"Model file '{path}' not found. Please run train_model.py first to train models.")
    return models

def predict_scenario(wind_speed, visibility, precipitation, temperature, vessel_queue, yard_occupancy, is_holiday):
    """
    Predict operational performance metrics based on input scenario parameters.
    """
    models = load_models()
    
    # Format features as a DataFrame matching the training columns
    features = pd.DataFrame([{
        'wind_speed': float(wind_speed),
        'visibility': float(visibility),
        'precipitation': float(precipitation),
        'temperature': float(temperature),
        'vessel_queue': int(vessel_queue),
        'yard_occupancy': float(yard_occupancy),
        'is_holiday': int(is_holiday)
    }])
    
    # Execute model predictions
    crane_teu_hour = models['crane'].predict(features)[0]
    vessel_turnaround_hours = models['vessel'].predict(features)[0]
    rail_delay_mins = models['rail'].predict(features)[0]
    
    # Post-process outputs to handle causal logic boundaries (like lockouts)
    if float(wind_speed) > 22.0:
        crane_teu_hour = 0.0 # Lockout safety override
        
    return {
        'crane_efficiency_teu_hour': round(max(0.0, crane_teu_hour), 2),
        'vessel_turnaround_hours': round(max(0.0, vessel_turnaround_hours), 2),
        'rail_dispatch_delay_mins': round(max(0.0, rail_delay_mins), 2)
    }

def fetch_weather_and_predict(city_name="Rotterdam", vessel_queue=3, yard_occupancy=65.0, is_holiday=0):
    """
    Fetch current weather from OpenWeather API and predict port operational metrics.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        print("Warning: OPENWEATHER_API_KEY not found in environment. Using default baseline weather metrics.")
        # Default Rotterdam weather
        return predict_scenario(4.2, 10000, 0.0, 16.5, vessel_queue, yard_occupancy, is_holiday)
        
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
    
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        
        # Parse weather variables
        wind_speed = data['wind']['speed'] # m/s
        visibility = data.get('visibility', 10000) # meters
        precipitation = data.get('rain', {}).get('1h', 0.0) # mm
        temperature = data['main']['temp'] # Celsius
        
        print(f"\nFetched current weather for {city_name}:")
        print(f"- Temp: {temperature}°C | Wind: {wind_speed} m/s | Vis: {visibility}m | Rain: {precipitation}mm")
        
        # Predict scenario
        predictions = predict_scenario(wind_speed, visibility, precipitation, temperature, vessel_queue, yard_occupancy, is_holiday)
        return predictions
        
    except Exception as e:
        print(f"Error fetching weather from OpenWeather API: {e}. Falling back to default predictions.")
        return predict_scenario(4.2, 10000, 0.0, 16.5, vessel_queue, yard_occupancy, is_holiday)

if __name__ == '__main__':
    # Make sure we run in the correct folder
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Run a sample manual scenario prediction (Wind Storm)
    print("Simulating Storm Scenario (Wind = 24 m/s, Visibility = 1200m, Congestion = 8 ships):")
    storm_result = predict_scenario(
        wind_speed=24.0, 
        visibility=1200.0, 
        precipitation=3.5, 
        temperature=8.0, 
        vessel_queue=8, 
        yard_occupancy=85.0, 
        is_holiday=0
    )
    print(storm_result)
    
    # 2. Run API check
    print("\nSimulating Real-Time Weather Scenario using OpenWeather API:")
    api_result = fetch_weather_and_predict("Rotterdam")
    print(api_result)
