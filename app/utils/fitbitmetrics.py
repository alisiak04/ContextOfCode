def display_steps_data(steps_data):
    """Process and return steps data from Fitbit API response"""
    try:
    
        total_steps = 0
        
        # First try to get the total from activities-steps
        if 'activities-steps' in steps_data and steps_data['activities-steps']:
            total_steps = int(steps_data['activities-steps'][0]['value'])
            print(f"Total steps from activities-steps: {total_steps}")
            return [{'time': 'Today', 'value': total_steps}]
        
        # If no total, sum up the intraday data
        elif 'activities-steps-intraday' in steps_data:
            dataset = steps_data['activities-steps-intraday'].get('dataset', [])
            total_steps = sum(entry['value'] for entry in dataset)
            print(f"Total steps calculated from intraday data: {total_steps}")
            return [{'time': 'Today', 'value': total_steps}]
        
        # Check for direct value
        elif isinstance(steps_data, (int, str)):
            total_steps = int(steps_data)
            print(f"Total steps from direct value: {total_steps}")
            return [{'time': 'Today', 'value': total_steps}]
        
        # If no steps data is found
        print("No recognized steps data format found")
        print("Available keys:", steps_data.keys() if isinstance(steps_data, dict) else "Not a dictionary")
        return [{'time': 'Today', 'value': 0}]
        
    except Exception as e:
        print("\n=== Steps Data Error ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print("Steps data structure:", steps_data)
        return [{'time': 'Today', 'value': 0}] 