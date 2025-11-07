from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
import os
from config import Config

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(Config)

# -------------------- API CLIENT -------------------- #
class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
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
        data = {'email': email, 'password': password}
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Login request failed: {e}")
            return {'success': False, 'message': 'Unable to connect to API server.'}

    def get_users(self):
        url = f"{self.base_url}/api/admin/users"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            print(f"Get users request failed: {e}")
            return None

    def get_activities(self):
        url = f"{self.base_url}/api/activities"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            print(f"Get activities request failed: {e}")
            return None

    def get_activity_instances(self):
        url = f"{self.base_url}/api/activity-instances"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            print(f"Get activity instances request failed: {e}")
            return None

# ---------------------------------------------------- #
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
            session['user'] = result['data']['user']
            session['token'] = result['data']['token']
            api_client.set_token(result['data']['token'])
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(result.get('message', 'Invalid credentials or server error.'), 'error')
    
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
    
    api_client.set_token(session['token'])

    users_data = api_client.get_users()
    total_users = len(users_data.get('data', [])) if users_data and users_data.get('success') else 0
    active_users = sum(1 for u in users_data.get('data', []) if u.get('isActive')) if users_data else 0
    admin_users = sum(1 for u in users_data.get('data', []) if u.get('role') == 'admin') if users_data else 0

    activities_data = api_client.get_activities()
    total_activities = len(activities_data.get('data', [])) if activities_data and activities_data.get('success') else 0

    schedules_data = api_client.get_activity_instances()
    total_schedules = len(schedules_data.get('data', [])) if schedules_data and schedules_data.get('success') else 0
    
    return render_template(
        'dashboard.html',
        user=session['user'],
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users,
        total_activities=total_activities,
        total_schedules=total_schedules
    )

# Optional health check for Railway
@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200


# -------------------- ENTRY POINT -------------------- #
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
