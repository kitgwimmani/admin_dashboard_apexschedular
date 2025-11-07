from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
import os
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
    
    def set_token(self, token):
        self.token = token
    
    def get_headers(self):
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def login(self, email, password):
        url = f"{self.base_url}/api/auth/login"
        data = {
            'email': email,
            'password': password
        }
        try:
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Check if login was successful based on your API response
                if data.get('success'):
                    self.token = data.get('token')  # Note: it's 'token' not 'access_token'
                    return data
                return None
            else:
                #print(f"Login failed with status {response.status_code}: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Login request failed: {e}")
            return None
    
    def get_users(self):
        url = f"{self.base_url}/api/admin/users"
        try:
            headers = self.get_headers()
            #print(f"Request Headers: {headers}")  # Debug: Check if Authorization header is present
            #print(f"Token being used: {self.token}")  # Debug: Check the actual token
            
            response = requests.get(url, headers=headers, timeout=30)
            #print(f"Get Users Response Status: {response.status_code}")  # Debug
            #print(f"Get Users Response Headers: {response.headers}")  # Debug
            
            if response.status_code == 200:
                data = response.json()
                #print(f"Get Users Response Data: {data}")  # Debug
                if data.get('success'):
                    return data
                return None
            elif response.status_code == 401:
                #print("Unauthorized - Token might be invalid or expired")
                return None
            elif response.status_code == 403:
                #print("Forbidden - User doesn't have admin permissions")
                return None
            else:
                #print(f"Get users failed with status {response.status_code}: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Get users request failed: {e}")
            return None
    def get_user(self, user_id):
        url = f"{self.base_url}/api/admin/users/{user_id}"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data
                return None
            return None
        except requests.exceptions.RequestException as e:
            print(f"Get user request failed: {e}")
            return None
    
    def change_user_role(self, user_id, new_role):
        url = f"{self.base_url}/api/admin/users/{user_id}"  # Remove /role from the endpoint
        data = {'role': new_role}
        try:
            response = requests.put(url, headers=self.get_headers(), json=data, timeout=30)
            print(f"Change role response status: {response.status_code}")  # Debug
            print(f"Change role response: {response.text}")  # Debug
            return response
        except requests.exceptions.RequestException as e:
            print(f"Change role request failed: {e}")
            return None
    
    def activate_user(self, user_id):
        url = f"{self.base_url}/api/users/{user_id}/activate"
        try:
            response = requests.put(url, headers=self.get_headers(), timeout=30)
            return response
        except requests.exceptions.RequestException as e:
            print(f"Activate user request failed: {e}")
            return None
    
    def deactivate_user(self, user_id):
        url = f"{self.base_url}/api/users/{user_id}/deactivate"
        try:
            response = requests.put(url, headers=self.get_headers(), timeout=30)
            return response
        except requests.exceptions.RequestException as e:
            print(f"Deactivate user request failed: {e}")
            return None
    
    def get_profile(self):
        url = f"{self.base_url}/api/auth/me"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data
                return None
            return None
        except requests.exceptions.RequestException as e:
            print(f"Get profile request failed: {e}")
            return None
    
    def update_profile(self, data):
        url = f"{self.base_url}/api/auth/me"
        try:
            response = requests.put(url, headers=self.get_headers(), json=data, timeout=30)
            return response
        except requests.exceptions.RequestException as e:
            print(f"Update profile request failed: {e}")
            return None
        
    def get_activities(self):
        url = f"{self.base_url}/api/activities"
        try:
            headers = self.get_headers()
            response = requests.get(url, headers=headers, timeout=30)
            print(f"Get Activities Response Status: {response.status_code}")  # Debug
            
            if response.status_code == 200:
                data = response.json()
                print(f"Get Activities Response Data: {data}")  # Debug
                if data.get('success'):
                    return data
                return None
            else:
                print(f"Get activities failed with status {response.status_code}: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Get activities request failed: {e}")
            return None

    def get_activity_instances(self):
        url = f"{self.base_url}/api/activity-instances"
        try:
            headers = self.get_headers()
            response = requests.get(url, headers=headers, timeout=30)
            print(f"Get Activity Instances Response Status: {response.status_code}")  # Debug
            
            if response.status_code == 200:
                data = response.json()
                print(f"Get Activity Instances Response Data: {data}")  # Debug
                if data.get('success'):
                    return data
                return None
            else:
                print(f"Get activity instances failed with status {response.status_code}: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Get activity instances request failed: {e}")
            return None

# Initialize API client
api_client = APIClient(app.config['API_BASE_URL'])

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html')
        
        result = api_client.login(email, password)
        
        if result and result.get('success'):
            # Store user data from the nested structure
            session['user'] = result['data']['user']  # Access nested user data
            session['token'] = result['data']['token']  # Token is at root level
            api_client.set_token(result['data']['token'])
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            error_msg = result.get('message', 'Invalid credentials or unable to connect to server.') if result else 'Unable to connect to server.'
            flash(error_msg, 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Get users data for dashboard statistics
    api_client.set_token(session['token'])
    users_data = api_client.get_users()
    
    # Calculate statistics
    total_users = 0
    active_users = 0
    admin_users = 0
    
    if users_data and users_data.get('success'):
        users_list = users_data['data']
        total_users = len(users_list)
        active_users = sum(1 for user in users_list if user.get('isActive'))
        admin_users = sum(1 for user in users_list if user.get('role') == 'admin')
    
    # Get activities data
    total_activities = 0
    activities_data = api_client.get_activities()
    if activities_data and activities_data.get('success'):
        if 'data' in activities_data and isinstance(activities_data['data'], list):
            total_activities = len(activities_data['data'])
        elif 'activities' in activities_data:
            total_activities = len(activities_data['activities'])
    
    # Get activity instances (schedules) data
    total_schedules = 0
    schedules_data = api_client.get_activity_instances()
    if schedules_data and schedules_data.get('success'):
        if 'data' in schedules_data and isinstance(schedules_data['data'], list):
            total_schedules = len(schedules_data['data'])
        elif 'activity_instances' in schedules_data:
            total_schedules = len(schedules_data['activity_instances'])
    
    return render_template('dashboard.html', 
                         user=session['user'],
                         total_users=total_users,
                         active_users=active_users,
                         admin_users=admin_users,
                         total_activities=total_activities,
                         total_schedules=total_schedules)

@app.route('/users')
def users():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Ensure we have the token in session
    if 'token' not in session:
        flash('Please login again.', 'error')
        return redirect(url_for('login'))
    
    # Set the token in the API client
    api_client.set_token(session['token'])
    
    users_data = api_client.get_users()
    
    if users_data is None:
        flash('Failed to fetch users. Please check your connection or permissions.', 'error')
        return redirect(url_for('dashboard'))
    
    # Handle the response structure based on your API response
    # Your API returns: {"success": true, "data": [{user1}, {user2}, ...]}
    users_list = []
    if users_data.get('success'):
        if 'data' in users_data and isinstance(users_data['data'], list):
            users_list = users_data['data']  # Users are directly in the 'data' array
        elif 'users' in users_data:
            users_list = users_data['users']  # Alternative structure
        elif 'data' in users_data and 'users' in users_data['data']:
            users_list = users_data['data']['users']  # Nested structure
    
    #print(f"✅ Users list length: {len(users_list)}")  # Debug
    
    return render_template('users.html', users=users_list, current_user=session['user'])

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    api_client.set_token(session['token'])
    
    if request.method == 'POST':
        data = {
            'username': request.form.get('username'),
            'email': request.form.get('email')
        }
        
        response = api_client.update_profile(data)
        if response and response.status_code == 200:
            # Update session data - check for nested structure
            profile_data = api_client.get_profile()
            if profile_data and profile_data.get('success'):
                session['user'] = profile_data['data']['user']  # Assuming similar structure
            flash('Profile updated successfully!', 'success')
        else:
            error_message = 'Failed to update profile: '
            if response:
                try:
                    error_data = response.json()
                    error_message += error_data.get('message', 'Unknown error')
                except:
                    error_message += 'Server error'
            else:
                error_message += 'Cannot connect to server'
            flash(error_message, 'error')
        
        return redirect(url_for('profile'))
    
    profile_data = api_client.get_profile()
    if profile_data and profile_data.get('success'):
        return render_template('profile.html', user=profile_data['data']['user'])
    
    flash('Failed to load profile data. Please check your connection.', 'error')
    return redirect(url_for('dashboard'))
@app.route('/change_role/<string:user_id>', methods=['POST'])
def change_role(user_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    api_client.set_token(session['token'])
    new_role = request.form.get('role')
    
    response = api_client.change_user_role(user_id, new_role)
    
    if response and response.status_code == 200:
        flash(f'User role updated to {new_role}!', 'success')
    else:
        error_message = 'Failed to update role: '
        if response:
            try:
                error_data = response.json()
                error_message += error_data.get('message', 'Unknown error')
            except:
                error_message += 'Server error'
        else:
            error_message += 'Cannot connect to server'
        flash(error_message, 'error')
    
    return redirect(url_for('users'))

@app.route('/toggle_user_status/<string:user_id>', methods=['POST'])
def toggle_user_status(user_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    api_client.set_token(session['token'])
    action = request.form.get('action')
    
    if action == 'activate':
        response = api_client.activate_user(user_id)
        message = 'User activated successfully!'
    else:
        response = api_client.deactivate_user(user_id)
        message = 'User deactivated successfully!'
    
    if response and response.status_code == 200:
        flash(message, 'success')
    else:
        error_message = 'Failed to update user status: '
        if response:
            try:
                error_data = response.json()
                error_message += error_data.get('message', 'Unknown error')
            except:
                error_message += 'Server error'
        else:
            error_message += 'Cannot connect to server'
        flash(error_message, 'error')
    
    return redirect(url_for('users'))
@app.route('/activities')
def activities():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    api_client.set_token(session['token'])
    activities_data = api_client.get_activities()
    
    activities_list = []
    if activities_data and activities_data.get('success'):
        if 'data' in activities_data and isinstance(activities_data['data'], list):
            activities_list = activities_data['data']
        elif 'activities' in activities_data:
            activities_list = activities_data['activities']
    
    return render_template('activities.html', 
                         activities=activities_list,
                         current_user=session['user'])
@app.route('/schedules')
def schedules():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    api_client.set_token(session['token'])
    instances_data = api_client.get_activity_instances()
    
    instances_list = []
    if instances_data and instances_data.get('success'):
        if 'data' in instances_data and isinstance(instances_data['data'], list):
            instances_list = instances_data['data']
        elif 'activity_instances' in instances_data:
            instances_list = instances_data['activity_instances']
    
    return render_template('schedules.html', 
                         activity_instances=instances_list,
                         current_user=session['user'])
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])