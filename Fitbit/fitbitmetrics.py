from datetime import datetime

from flask import render_template
def display_heart_rate_data(heart_rate_data):
    """ Extract resting heart rate and heart rate zones for display """
    print("Original Heart Rate Data:", heart_rate_data)

    # Check if 'activities-heart' exists and has data
    if 'activities-heart' in heart_rate_data and len(heart_rate_data['activities-heart']) > 0:
        first_entry = heart_rate_data['activities-heart'][0]  # Access the first day's data
        
        resting_heart_rate = first_entry['value'].get('restingHeartRate', None)  # Extract resting heart rate
        heart_rate_zones = first_entry['value'].get('heartRateZones', [])  # Extract heart rate zones
    else:
        resting_heart_rate = None
        heart_rate_zones = []

    return render_template(
        'display_data.html', 
        resting_heart_rate=resting_heart_rate, 
        heart_rate_zones=heart_rate_zones
    )


def display_steps_data(steps_data):
    steps_list = []
    for entry in steps_data.get('activities-steps-intraday', {}).get('dataset', []):
        # Extract time and steps value, and format as necessary
        time_slot = entry.get('time', '')
        steps = entry.get('value', 0)
        steps_list.append({"time_slot": time_slot, "steps": steps})
    return steps_list


def display_real_time_heart_rate_data(real_time_data):
    """ Extract real-time heart rate data """
    real_time_list = []
    if 'activities-heart-intraday' in real_time_data and 'dataset' in real_time_data['activities-heart-intraday']:
        for entry in real_time_data['activities-heart-intraday']['dataset']:
            real_time_list.append({
                "time": entry["time"],
                "value": entry["value"]
            })
    
    return render_template('display_data.html', real_time_data=real_time_list)