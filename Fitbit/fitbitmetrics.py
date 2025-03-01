from flask import render_template

def display_data(heart_rate_data, steps_data, real_time_heart_rate_data):
    """ Render all the health data in an HTML page """
    print("Rendering Heart Rate Data:", heart_rate_data)
    print("Rendering Steps Data:", steps_data)
    print("Rendering Real-Time Heart Rate Data:", real_time_heart_rate_data)
    
    return render_template('display_data.html', 
                           heart_rate_data=heart_rate_data, 
                           steps_data=steps_data, 
                           real_time_heart_rate_data=real_time_heart_rate_data)