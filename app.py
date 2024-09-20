from flask import Flask, render_template, request
import requests
from datetime import datetime
from requests.exceptions import RequestException, SSLError, ConnectionError

app = Flask(__name__)

# Your Google Apps Script URL
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyXPyQZhB6IcqVqDj-FfJ3OIrVqntQffPiu0xMaihvoaNRxqT66-Re-TCr5LwEW7XZOqQ/exec"

# Set the check-in start date
CHECKIN_START_DATE = datetime(2024, 9, 11, 9, 0)

@app.route('/checkin-by-barcode', methods=['GET', 'POST'])
def checkin_by_barcode():
    if request.method == 'GET':
        unique_id = request.args.get('unique_id')
        email = request.args.get('email')

        if not unique_id or not email:
            return "unique_id and email are required", 400

        current_date = datetime.now()
        if current_date < CHECKIN_START_DATE:
            return render_template('date_checkin.html'), 200

        try:
            response = requests.get(GOOGLE_SCRIPT_URL, params={'unique_id': unique_id, 'email': email, 'action': 'checkin'})
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text}")

            if response.status_code != 200:
                return f"Error: Received status code {response.status_code} from Apps Script", 500

            try:
                guest = response.json()
            except ValueError:
                return "Error: Unable to parse JSON response", 500

            if 'error' in guest:
                return render_template('guest_not_found.html'), 404

            # Color map to assign specific colors
            color_map = {
                'Planetary': '#334EAC',
                'Red': '#FF0000',
                'Orange': '#FFA500',
                'Green': '#008000',
            }

            # Assign the correct color, or default to guest.xn if not found in the map
            guest_color = color_map.get(guest.get('xn'), '#FFFFFF')  # Default color is white if not found

            # Check if the guest is already checked in
            if guest.get('time_checked_in'):
                return render_template('already_checkedin.html', guest=guest, guest_color=guest_color)

            return render_template('checkin.html', guest=guest, guest_color=guest_color)
        except (SSLError, ConnectionError) as e:
            return render_template('network_error.html', error_message=str(e)), 500
        except RequestException as e:
            return f"Error: {str(e)}", 500

    return render_template('email_checkin.html')



@app.route('/checkin-by-email', methods=['GET', 'POST'])
def checkin_by_email():
    if request.method == 'POST':
        email = request.form.get('email')

        current_date = datetime.now()
        if current_date < CHECKIN_START_DATE:
            return render_template('date_checkin.html'), 200

        try:
            response = requests.get(GOOGLE_SCRIPT_URL, params={'email': email, 'action': 'checkin'})
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text}")

            if response.status_code != 200:
                return f"Error: Received status code {response.status_code} from Apps Script", 500

            try:
                guest = response.json()
            except ValueError:
                return "Error: Unable to parse JSON response", 500

            if 'error' in guest:
                return render_template('guest_not_found.html'), 404
            
            color_map = {
                'Planetary': '#334EAC',
                'Red': '#FF0000',        
                'Orange': '#FFA500',     
                'Green': '#008000',      
            }

            # Assign the correct color, or default to guest.xn if not found in the map
            guest_color = color_map.get(guest.get('xn'), '#FFFFFF')  

            # Check if the guest is already checked in
            if guest.get('time_checked_in'):
                return render_template('already_checkedin.html', guest=guest)

            return render_template('checkin.html', guest=guest, guest_color=guest_color)
        except (SSLError, ConnectionError) as e:
            return render_template('network_error.html', error_message=str(e)), 500
        except RequestException as e:
            return f"Error: {str(e)}", 500

    return render_template('email_checkin.html')



@app.route('/static/css/checkin.css')
def css_test():
    return "Static file is accessible"

# Global error handler for network errors
@app.errorhandler(SSLError)
@app.errorhandler(ConnectionError)
def handle_network_error(e):
    return render_template('network_error.html', error_message=str(e)), 500

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True, port=5003)
