import simpy
import random
import numpy as np
try:
    from .predict import predict_scenario
except ImportError:
    from predict import predict_scenario

class PortTerminal(object):
    """Models a port terminal layout with berths and cranes."""
    def __init__(self, env, num_berths, crane_speed_teu_hour):
        self.env = env
        self.berths = simpy.Resource(env, num_berths)
        self.crane_speed = crane_speed_teu_hour

    def service_vessel(self, vessel_name, cargo_volume_teu):
        """Simulate loading/unloading container cargo."""
        if self.crane_speed <= 0:
            # Cranes locked out: wait until wind clears
            # Simulate a 12-hour force majeure delay
            yield self.env.timeout(12.0)
            # Re-evaluate handling time with a slow baseline recovery speed
            actual_speed = 10.0
        else:
            actual_speed = self.crane_speed
            
        handling_duration = cargo_volume_teu / actual_speed
        yield self.env.timeout(handling_duration)

def vessel_generator(env, terminal, arrival_rate, results):
    """Generate ship arrival events based on average turnaround intervals."""
    vessel_id = 0
    while True:
        # Time until next ship arrival (exponential distribution)
        yield env.timeout(random.expovariate(1.0 / arrival_rate))
        vessel_id += 1
        name = f"Vessel_{vessel_id}"
        cargo = random.randint(300, 1500) # TEUs of cargo to load/unload
        
        env.process(vessel_flow(env, name, cargo, terminal, results))

def vessel_flow(env, name, cargo, terminal, results):
    """Handles the lifecycle of a ship arriving at the port."""
    arrival_time = env.now
    
    # Request a free berth slot
    with terminal.berths.request() as request:
        yield request
        berth_assigned_time = env.now
        waiting_time = berth_assigned_time - arrival_time
        
        # Service cargo
        yield env.process(terminal.service_vessel(name, cargo))
        departure_time = env.now
        total_time = departure_time - arrival_time
        
        results.append({
            'vessel': name,
            'cargo_teu': cargo,
            'arrival': round(arrival_time, 2),
            'berthing_wait_hours': round(waiting_time, 2),
            'handling_hours': round(departure_time - berth_assigned_time, 2),
            'total_turnaround_hours': round(total_time, 2)
        })

def run_monte_carlo_simulation(wind_speed, visibility, precipitation, temperature, vessel_queue, yard_occupancy, num_berths=3, sim_duration_days=7):
    """
    Predict operational weather coefficients and run a discrete-event queue simulation
    to predict total container handling throughput and queues over a simulated week.
    """
    # 1. Fetch ML-predicted operational speeds
    ml_out = predict_scenario(
        wind_speed=wind_speed,
        visibility=visibility,
        precipitation=precipitation,
        temperature=temperature,
        vessel_queue=vessel_queue,
        yard_occupancy=yard_occupancy,
        is_holiday=0
    )
    
    crane_speed = ml_out['crane_efficiency_teu_hour']
    
    # 2. Setup SimPy environment
    env = simpy.Environment()
    terminal = PortTerminal(env, num_berths=num_berths, crane_speed_teu_hour=crane_speed)
    
    # Ship arrival rate: average 1 ship every 18 hours
    arrival_interval_hours = 18.0
    results = []
    
    # Seed simulation random numbers
    random.seed(42)
    
    # Initialize generators
    env.process(vessel_generator(env, terminal, arrival_interval_hours, results))
    
    # 3. Run simulation for the week
    env.run(until=sim_duration_days * 24.0)
    
    # 4. Analyze results
    if len(results) == 0:
        return {
            'simulated_ships_completed': 0,
            'average_berth_wait_hours': 0,
            'total_teus_handled': 0,
            'bottleneck_detected': "Operations Halted (Wind Lockout)" if crane_speed == 0 else "No ship traffic arrived"
        }
        
    avg_wait = np.mean([r['berthing_wait_hours'] for r in results])
    avg_turnaround = np.mean([r['total_turnaround_hours'] for r in results])
    total_teus = sum([r['cargo_teu'] for r in results])
    
    # Detect bottlenecks
    if avg_wait > 8.0:
        bottleneck = "Severe Berth Congestion (Insufficent Berth allocation or slow crane speed)"
    elif yard_occupancy > 85.0:
        bottleneck = "High Yard Stack Density (Slowing down terminal dispatch)"
    elif crane_speed < 15.0:
        bottleneck = "Weather-Induced Crane Sluggishness"
    else:
        bottleneck = "Normal Traffic Operations"
        
    return {
        'simulated_ships_completed': len(results),
        'average_berth_wait_hours': round(float(avg_wait), 2),
        'average_turnaround_hours': round(float(avg_turnaround), 2),
        'total_teus_handled': int(total_teus),
        'bottleneck_status': bottleneck,
        'crane_efficiency_teu_hour': crane_speed,
        'rail_delay_mins': ml_out['rail_dispatch_delay_mins']
    }

if __name__ == '__main__':
    # Make sure we run in the correct folder
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    import argparse
    import json
    import sys
    import requests
    
    parser = argparse.ArgumentParser(description="What-If Port Operations Simulator CLI")
    parser.add_argument("--action", type=str, required=True, choices=["simulate", "weather"], help="Action to perform")
    
    # Simulation parameters
    parser.add_argument("--wind", type=float, default=4.2, help="Wind speed in m/s")
    parser.add_argument("--visibility", type=float, default=10000.0, help="Visibility in meters")
    parser.add_argument("--precip", type=float, default=0.0, help="Precipitation in mm")
    parser.add_argument("--temp", type=float, default=15.0, help="Temperature in Celsius")
    parser.add_argument("--vessels", type=int, default=22, help="Active inbound vessels")
    parser.add_argument("--yard", type=float, default=70.0, help="Yard occupancy percentage")
    parser.add_argument("--berths", type=int, default=3, help="Number of berths")
    parser.add_argument("--days", type=int, default=7, help="Simulation duration in days")
    
    # Weather parameters
    parser.add_argument("--city", type=str, default="Rotterdam", help="City name for current weather")
    
    args = parser.parse_args()
    
    if args.action == "simulate":
        try:
            res = run_monte_carlo_simulation(
                wind_speed=args.wind,
                visibility=args.visibility,
                precipitation=args.precip,
                temperature=args.temp,
                vessel_queue=args.vessels,
                yard_occupancy=args.yard,
                num_berths=args.berths,
                sim_duration_days=args.days
            )
            # Print JSON on stdout
            print(json.dumps({"status": "success", "result": res}))
            sys.exit(0)
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}))
            sys.exit(1)
            
    elif args.action == "weather":
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            default_weather = {
                "wind_speed": 4.2,
                "visibility": 10000.0,
                "precipitation": 0.0,
                "temperature": 16.5,
                "city": args.city,
                "is_fallback": True
            }
            try:
                preds = predict_scenario(4.2, 10000.0, 0.0, 16.5, args.vessels, args.yard, 0)
                print(json.dumps({"status": "success", "weather": default_weather, "predictions": preds}))
                sys.exit(0)
            except Exception as e:
                print(json.dumps({"status": "error", "message": str(e)}))
                sys.exit(1)
        
        url = f"http://api.openweathermap.org/data/2.5/weather?q={args.city}&appid={api_key}&units=metric"
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()
            
            wind_speed = float(data['wind']['speed']) # m/s
            visibility = float(data.get('visibility', 10000.0)) # meters
            precipitation = float(data.get('rain', {}).get('1h', 0.0)) # mm
            temperature = float(data['main']['temp']) # Celsius
            
            weather_data = {
                "wind_speed": wind_speed,
                "visibility": visibility,
                "precipitation": precipitation,
                "temperature": temperature,
                "city": args.city,
                "is_fallback": False
            }
            
            preds = predict_scenario(wind_speed, visibility, precipitation, temperature, args.vessels, args.yard, 0)
            print(json.dumps({"status": "success", "weather": weather_data, "predictions": preds}))
            sys.exit(0)
        except Exception as e:
            default_weather = {
                "wind_speed": 4.2,
                "visibility": 10000.0,
                "precipitation": 0.0,
                "temperature": 16.5,
                "city": args.city,
                "is_fallback": True,
                "error": str(e)
            }
            try:
                preds = predict_scenario(4.2, 10000.0, 0.0, 16.5, args.vessels, args.yard, 0)
                print(json.dumps({"status": "success", "weather": default_weather, "predictions": preds}))
                sys.exit(0)
            except Exception as e2:
                print(json.dumps({"status": "error", "message": f"Weather fetch failed: {e}. Prediction failed: {e2}"}))
                sys.exit(1)
