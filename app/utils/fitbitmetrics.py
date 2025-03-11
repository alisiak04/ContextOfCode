from datetime import datetime

def display_steps_data(steps_data):
    """Extracts step data from Fitbit API response, grouped into 15-minute intervals for the entire day."""
    try:
        # Ensure the dataset exists
        if 'activities-steps-intraday' not in steps_data:
            print("⚠️ No intraday steps data found, falling back to daily total.")
            return [{"time": "Today", "steps": int(steps_data['activities-steps'][0]['value'])}] if 'activities-steps' in steps_data else [{"time": "Today", "steps": 0}]

        dataset = steps_data['activities-steps-intraday'].get('dataset', [])

        if not dataset:
            print("⚠️ No step data found in intraday dataset.")
            return []

        # Extract all 15-min interval data for the whole day
        steps_with_time = [{"time": entry['time'], "steps": entry['value']} for entry in dataset]

       

        return steps_with_time

    except Exception as e:
        print("\n=== Steps Data Error ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print("Steps data structure:", steps_data)
        return []