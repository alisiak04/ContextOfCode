from datetime import datetime, timedelta

def display_steps_data(steps_data):
    """Process and return steps data from Fitbit API response (only last 15 minutes)"""
    try:
        # Ensure the dataset exists
        if 'activities-steps-intraday' not in steps_data:
            print("⚠️ No intraday steps data found, falling back to daily total.")
            return [{'time': 'Today', 'value': int(steps_data['activities-steps'][0]['value'])}] if 'activities-steps' in steps_data else [{'time': 'Today', 'value': 0}]

        dataset = steps_data['activities-steps-intraday'].get('dataset', [])

        if not dataset:
            print("⚠️ No step data found in intraday dataset.")
            return [{'time': 'Last 15 min', 'value': 0}]

        # Get the current time and filter for last 15 minutes
        now = datetime.now()
        fifteen_minutes_ago = now - timedelta(minutes=15)

        filtered_steps = [
            entry for entry in dataset 
            if datetime.strptime(entry['time'], "%H:%M:%S") >= fifteen_minutes_ago
        ]

        # Sum up steps for the last 15 minutes
        total_steps_last_15 = sum(entry['value'] for entry in filtered_steps)

        print(f"🟢 Total steps in last 15 minutes: {total_steps_last_15}")

        return [{'time': 'Last 15 min', 'value': total_steps_last_15}]

    except Exception as e:
        print("\n=== Steps Data Error ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print("Steps data structure:", steps_data)
        return [{'time': 'Last 15 min', 'value': 0}]