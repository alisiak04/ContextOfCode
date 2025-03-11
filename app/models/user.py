class FitbitUser:
    def __init__(self, user_data):
        self.profile = user_data.get('profile', {})
        self.heart_rate = user_data.get('heart_rate', {})
        self.real_time_heart_rate = user_data.get('real_time_heart_rate', {})
        self.steps = user_data.get('steps', {})

    @property
    def display_name(self):
        return self.profile.get('user', {}).get('displayName')

    @property
    def resting_heart_rate(self):
        try:
            return self.heart_rate['activities-heart'][0]['value'].get('restingHeartRate')
        except (KeyError, IndexError):
            return None

    @property
    def heart_rate_zones(self):
        try:
            return self.heart_rate['activities-heart'][0]['value'].get('heartRateZones', [])
        except (KeyError, IndexError):
            return []

    @property
    def real_time_heart_rate_data(self):
        dataset =  self.real_time_heart_rate.get('activities-heart-intraday', {}).get('dataset', []) 
        return dataset