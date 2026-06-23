import pandas as pd
import numpy as np
import os

def generate_synthetic_dataset(num_samples=5000, output_path='port_operations_dataset.csv'):
    print(f"Generating {num_samples} synthetic port operations records...")
    
    # Seed for reproducibility
    np.random.seed(42)
    
    # 1. Generate Input Feature Variables (Independent variables)
    # Wind speed in m/s (heavy right-skew, standard maritime distribution)
    wind_speed = np.random.exponential(scale=5.0, size=num_samples)
    wind_speed = np.clip(wind_speed, 0, 32) # clip at storm level
    
    # Visibility in meters (fog representation)
    visibility = np.random.choice(
        [10000, 8000, 5000, 2000, 800, 300], 
        size=num_samples, 
        p=[0.75, 0.12, 0.07, 0.03, 0.02, 0.01]
    )
    # Add minor noise to visibility
    visibility = np.clip(visibility + np.random.normal(0, 100, num_samples), 100, 10000)
    
    # Precipitation in mm/hour
    precipitation = np.random.exponential(scale=0.5, size=num_samples)
    precipitation = np.where(np.random.rand(num_samples) > 0.8, precipitation, 0) # 80% dry days
    
    # Temperature in Celsius
    temperature = np.random.normal(loc=18.0, scale=12.0, size=num_samples)
    temperature = np.clip(temperature, -10, 45)
    
    # Congestion metrics
    vessel_queue = np.random.poisson(lam=3.0, size=num_samples)
    vessel_queue = np.clip(vessel_queue, 0, 15)
    
    yard_occupancy = np.random.uniform(low=30.0, high=95.0, size=num_samples)
    
    is_holiday = np.random.choice([0, 1], size=num_samples, p=[0.88, 0.12])
    
    # 2. Define Output Target Variables (Dependent variables using causal operations equations)
    # Target A: Crane Efficiency (TEUs/hour handling speed)
    # Base crane efficiency is 42 TEUs/hour
    base_crane_speed = 42.0
    
    crane_efficiency = []
    turnaround_time_hours = []
    rail_dispatch_delay_mins = []
    
    for i in range(num_samples):
        w_speed = wind_speed[i]
        vis = visibility[i]
        precip = precipitation[i]
        temp = temperature[i]
        v_queue = vessel_queue[i]
        yard_occ = yard_occupancy[i]
        holiday = is_holiday[i]
        
        # Calculate Crane Handling Speed (TEUs/hour)
        speed = base_crane_speed
        
        # Wind effect (Critical safety lockout at high wind speeds)
        if w_speed > 22.0:
            speed = 0.0 # Full operations halt
        elif w_speed > 14.0:
            speed *= 0.65 # 35% speed reduction
        elif w_speed > 9.0:
            speed *= 0.85 # 15% speed reduction
            
        # Fog/Visibility effect
        if speed > 0:
            if vis < 1000:
                speed *= 0.50 # 50% slow down due to zero visibility
            elif vis < 3000:
                speed *= 0.80 # 20% slow down
                
        # Rain/Precipitation effect
        if speed > 0:
            if precip > 6.0:
                speed *= 0.70 # 30% reduction in heavy downpours
            elif precip > 1.5:
                speed *= 0.88 # 12% reduction
                
        # Temperature extremes effect
        if speed > 0:
            if temp > 40.0 or temp < -5.0:
                speed *= 0.90 # 10% reduction in extreme heat/cold (crew fatigue)
                
        # Add random operational noise (crane mechanics variance)
        if speed > 0:
            speed += np.random.normal(0, 1.5)
            speed = np.clip(speed, 5, 50)
            
        crane_efficiency.append(round(speed, 2))
        
        # Calculate Vessel Turnaround Time (hours)
        # Base ship servicing takes 14 hours
        vessel_time = 14.0
        
        # Influenced by crane efficiency
        if speed > 0:
            # Slower crane speeds increase turnaround times exponentially
            vessel_time += (base_crane_speed / speed) * 8.0 - 8.0
        else:
            vessel_time += 24.0 # 24-hour baseline delay if cranes are locked out due to wind
            
        # Influenced by port congestion & yard storage capacity
        vessel_time += (v_queue * 1.8) # waiting in queue
        vessel_time += (yard_occ / 100.0) * 6.0 # yard congestion delays cargo layout
        
        # Holiday delays
        if holiday == 1:
            vessel_time += 4.5
            
        # Add normal terminal handling variance
        vessel_time += np.random.normal(0, 2.0)
        vessel_time = max(4.0, vessel_time) # Minimum 4 hours
        turnaround_time_hours.append(round(vessel_time, 2))
        
        # Calculate Rail Dispatch Delay (minutes)
        # Base dispatch delay is 15 minutes
        rail_delay = 15.0
        
        # Yard occupancy delay (trucks blocking tracks, container sorting taking time)
        if yard_occ > 80.0:
            rail_delay += (yard_occ - 80.0) * 1.5
            
        # Weather delay (wet tracks require slower speeds)
        if precip > 2.0:
            rail_delay += (precip * 3.5)
        if vis < 1500:
            rail_delay += 12.0
            
        # Add random scheduling variance
        rail_delay += np.random.normal(0, 3.0)
        rail_delay = max(2.0, rail_delay)
        rail_dispatch_delay_mins.append(round(rail_delay, 2))
        
    # Create DataFrame
    df = pd.DataFrame({
        'wind_speed': np.round(wind_speed, 2),
        'visibility': np.round(visibility, 2),
        'precipitation': np.round(precipitation, 2),
        'temperature': np.round(temperature, 2),
        'vessel_queue': vessel_queue,
        'yard_occupancy': np.round(yard_occupancy, 2),
        'is_holiday': is_holiday,
        'crane_efficiency': crane_efficiency,
        'turnaround_time_hours': turnaround_time_hours,
        'rail_dispatch_delay_mins': rail_dispatch_delay_mins
    })
    
    # Save to disk
    df.to_csv(output_path, index=False)
    print(f"Dataset successfully created and saved to {output_path}!")
    return df

if __name__ == '__main__':
    # Make sure we run in the correct folder
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    generate_synthetic_dataset()
