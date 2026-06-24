import pandas as pd
import numpy as np
import os

def generate_synthetic_dataset(num_samples=8000, output_path='port_operations_dataset.csv'):
    """
    Generate a synthetic port operations dataset with 11 input features and 4 target variables.
    Uses domain-expert causal equations to model realistic maritime operations physics.
    """
    print(f"Generating {num_samples} synthetic port operations records...")
    
    # Seed for reproducibility
    np.random.seed(42)
    
    # ──────────────────────────────────────────────────────────────────
    # 1. Generate Input Feature Variables (11 Independent variables)
    # ──────────────────────────────────────────────────────────────────
    
    # Wind speed in m/s (heavy right-skew, standard maritime distribution)
    wind_speed = np.random.exponential(scale=5.0, size=num_samples)
    wind_speed = np.clip(wind_speed, 0, 32)  # clip at storm level
    
    # Visibility in meters (fog representation)
    visibility = np.random.choice(
        [10000, 8000, 5000, 2000, 800, 300], 
        size=num_samples, 
        p=[0.75, 0.12, 0.07, 0.03, 0.02, 0.01]
    )
    visibility = np.clip(visibility + np.random.normal(0, 100, num_samples), 100, 10000)
    
    # Precipitation in mm/hour
    precipitation = np.random.exponential(scale=0.5, size=num_samples)
    precipitation = np.where(np.random.rand(num_samples) > 0.8, precipitation, 0)  # 80% dry days
    
    # Temperature in Celsius
    temperature = np.random.normal(loc=18.0, scale=12.0, size=num_samples)
    temperature = np.clip(temperature, -10, 45)
    
    # Congestion metrics
    vessel_queue = np.random.poisson(lam=3.0, size=num_samples)
    vessel_queue = np.clip(vessel_queue, 0, 15)
    
    yard_occupancy = np.random.uniform(low=30.0, high=95.0, size=num_samples)
    
    is_holiday = np.random.choice([0, 1], size=num_samples, p=[0.88, 0.12])
    
    # ── NEW: Vessel-specific features ──
    # Vessel type: Container=0, Bulk=1, Tanker=2, RoRo=3
    vessel_type = np.random.choice([0, 1, 2, 3], size=num_samples, p=[0.45, 0.25, 0.20, 0.10])
    
    # Cargo volume in TEUs (varies by vessel type)
    cargo_volume_teu = np.zeros(num_samples, dtype=int)
    for i in range(num_samples):
        if vessel_type[i] == 0:    # Container - high TEU
            cargo_volume_teu[i] = np.random.randint(800, 4500)
        elif vessel_type[i] == 1:  # Bulk - medium TEU equivalent
            cargo_volume_teu[i] = np.random.randint(400, 2000)
        elif vessel_type[i] == 2:  # Tanker - low TEU equivalent
            cargo_volume_teu[i] = np.random.randint(300, 1200)
        else:                      # RoRo - medium TEU
            cargo_volume_teu[i] = np.random.randint(500, 1800)
    
    # Route distance in nautical miles (from origin port)
    route_distance_nm = np.random.choice(
        [350, 800, 1500, 3200, 5500, 7800],  # Short-haul to trans-oceanic
        size=num_samples,
        p=[0.15, 0.20, 0.25, 0.20, 0.12, 0.08]
    )
    route_distance_nm = route_distance_nm + np.random.normal(0, 50, num_samples)
    route_distance_nm = np.clip(route_distance_nm, 200, 8500).astype(float)
    
    # Port congestion level (0.0 = empty, 1.0 = fully saturated)
    # Derived from vessel_queue and yard_occupancy with added operational noise
    port_congestion_level = np.clip(
        (vessel_queue / 15.0) * 0.5 + (yard_occupancy / 95.0) * 0.4 + np.random.normal(0, 0.05, num_samples),
        0.0, 1.0
    )
    
    # ──────────────────────────────────────────────────────────────────
    # 2. Define Output Target Variables (4 Dependent variables)
    # ──────────────────────────────────────────────────────────────────
    base_crane_speed = 42.0
    
    crane_efficiency = []
    turnaround_time_hours = []
    rail_dispatch_delay_mins = []
    eta_delay_minutes = []
    
    for i in range(num_samples):
        w_speed = wind_speed[i]
        vis = visibility[i]
        precip = precipitation[i]
        temp = temperature[i]
        v_queue = vessel_queue[i]
        yard_occ = yard_occupancy[i]
        holiday = is_holiday[i]
        v_type = vessel_type[i]
        cargo = cargo_volume_teu[i]
        route_dist = route_distance_nm[i]
        congestion = port_congestion_level[i]
        
        # ── Target A: Crane Efficiency (TEUs/hour) ──
        speed = base_crane_speed
        
        # Wind effect (Critical safety lockout at high wind speeds)
        if w_speed > 22.0:
            speed = 0.0  # Full operations halt
        elif w_speed > 14.0:
            speed *= 0.65  # 35% speed reduction
        elif w_speed > 9.0:
            speed *= 0.85  # 15% speed reduction
            
        # Fog/Visibility effect
        if speed > 0:
            if vis < 1000:
                speed *= 0.50
            elif vis < 3000:
                speed *= 0.80
                
        # Rain/Precipitation effect
        if speed > 0:
            if precip > 6.0:
                speed *= 0.70
            elif precip > 1.5:
                speed *= 0.88
                
        # Temperature extremes effect
        if speed > 0:
            if temp > 40.0 or temp < -5.0:
                speed *= 0.90
                
        # Vessel type modifier (tankers and bulk need specialized equipment)
        if speed > 0:
            if v_type == 2:   # Tanker
                speed *= 0.85
            elif v_type == 1: # Bulk
                speed *= 0.92
                
        # Add random operational noise
        if speed > 0:
            speed += np.random.normal(0, 1.5)
            speed = np.clip(speed, 5, 50)
            
        crane_efficiency.append(round(speed, 2))
        
        # ── Target B: Vessel Turnaround Time (hours) ──
        vessel_time = 14.0
        
        if speed > 0:
            vessel_time += (base_crane_speed / speed) * 8.0 - 8.0
        else:
            vessel_time += 24.0
            
        vessel_time += (v_queue * 1.8)
        vessel_time += (yard_occ / 100.0) * 6.0
        
        # Cargo volume effect (more cargo = longer turnaround)
        vessel_time += (cargo / 1000.0) * 3.5
        
        if holiday == 1:
            vessel_time += 4.5
            
        vessel_time += np.random.normal(0, 2.0)
        vessel_time = max(4.0, vessel_time)
        turnaround_time_hours.append(round(vessel_time, 2))
        
        # ── Target C: Rail Dispatch Delay (minutes) ──
        rail_delay = 15.0
        
        if yard_occ > 80.0:
            rail_delay += (yard_occ - 80.0) * 1.5
            
        if precip > 2.0:
            rail_delay += (precip * 3.5)
        if vis < 1500:
            rail_delay += 12.0
            
        rail_delay += np.random.normal(0, 3.0)
        rail_delay = max(2.0, rail_delay)
        rail_dispatch_delay_mins.append(round(rail_delay, 2))
        
        # ── Target D: ETA Delay (minutes) — NEW ──
        # Base ETA variance from route distance (longer routes = more uncertainty)
        eta = (route_dist / 400.0) * np.random.normal(0, 6.0)
        
        # Weather amplifiers
        if w_speed > 18.0:
            eta += w_speed * 3.0    # Severe wind → major delay
        elif w_speed > 12.0:
            eta += w_speed * 1.5    # Moderate wind → some delay
            
        if vis < 1500:
            eta += 18.0             # Poor visibility → navigation slow-down
        elif vis < 3000:
            eta += 8.0
            
        if precip > 4.0:
            eta += precip * 3.5     # Heavy rain → channel speed restrictions
        elif precip > 1.5:
            eta += precip * 1.8
            
        # Port congestion amplifier (queued ships → pilot/tug unavailability)
        eta += congestion * 30.0
        eta += v_queue * 3.2
        
        # Vessel type modifier (tankers are slower to maneuver in channels)
        if v_type == 2:    # Tanker
            eta += 15.0
        elif v_type == 1:  # Bulk
            eta += 8.0
        elif v_type == 3:  # RoRo
            eta += 5.0
            
        # Holiday effect (reduced pilot/tug availability)
        if holiday == 1:
            eta += 12.0
            
        # Add operational noise
        eta += np.random.normal(0, 5.0)
        
        # Negative eta = early arrival (possible with favorable conditions)
        eta = np.clip(eta, -45, 240)
        eta_delay_minutes.append(round(eta, 2))
        
    # ──────────────────────────────────────────────────────────────────
    # 3. Create and Save DataFrame
    # ──────────────────────────────────────────────────────────────────
    df = pd.DataFrame({
        # Input features (11)
        'wind_speed': np.round(wind_speed, 2),
        'visibility': np.round(visibility, 2),
        'precipitation': np.round(precipitation, 2),
        'temperature': np.round(temperature, 2),
        'vessel_queue': vessel_queue,
        'yard_occupancy': np.round(yard_occupancy, 2),
        'is_holiday': is_holiday,
        'vessel_type': vessel_type,
        'cargo_volume_teu': cargo_volume_teu,
        'route_distance_nm': np.round(route_distance_nm, 2),
        'port_congestion_level': np.round(port_congestion_level, 4),
        # Target variables (4)
        'crane_efficiency': crane_efficiency,
        'turnaround_time_hours': turnaround_time_hours,
        'rail_dispatch_delay_mins': rail_dispatch_delay_mins,
        'eta_delay_minutes': eta_delay_minutes,
    })
    
    # Save to disk
    df.to_csv(output_path, index=False)
    print(f"Dataset successfully created and saved to {output_path}!")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Features: {list(df.columns[:11])}")
    print(f"Targets:  {list(df.columns[11:])}")
    return df

if __name__ == '__main__':
    # Make sure we run in the correct folder
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    generate_synthetic_dataset()
