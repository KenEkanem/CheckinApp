from flask import Flask, render_template, request
import requests
from datetime import datetime

app = Flask(__name__)

# Your Google Apps Script URL
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwFYRcSvnTV4wBpc5-n4UqJ_OHPUa13zonEM0sCBS7ybEOnAve7sIAMGz8pvQ-705ZpUw/exec"

# Set the check-in start date
CHECKIN_START_DATE = datetime(2024, 9, 26, 9, 0)

@app.route('/checkin-by-barcode', methods=['GET', 'POST'])
def checkin_by_barcode():
    if request.method == 'GET':
        # Extract barcode and email from query parameters
        unique_id = request.args.get('unique_id')
        email = request.args.get('email')

        # Ensures both barcode and email are provided
        if not unique_id or not email:
            return "unique_id and email are required", 400

        # Check the current date
        current_date = datetime.now()
        if current_date < CHECKIN_START_DATE:
            return render_template('date_checkin.html'), 200

        # Sends request to the Apps Script to search by barcode and email
        try:
            response = requests.get(GOOGLE_SCRIPT_URL, params={'unique_id': unique_id, 'email': email})
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text}")

            if response.status_code != 200:
                return f"Error: Received status code {response.status_code} from Apps Script", 500

            if not response.text.strip():
                return "No data returned from Apps Script", 500

            guest = response.json()

            if not guest:
                return render_template('guest_not_found.html'), 404

            # Renders the guest information
            return render_template('checkin.html', guest=guest)
        except Exception as e:
            return f"Error: {str(e)}", 500

    # If not a GET request, return the form
    return render_template('email_checkin.html')

@app.route('/checkin-by-email', methods=['GET', 'POST'])
def checkin_by_email():
    if request.method == 'POST':
        email = request.form.get('email')

        # Check the current date
        current_date = datetime.now()
        if current_date < CHECKIN_START_DATE:
            return render_template('date_checkin.html'), 200

        # Sends request to the Apps Script to search by email
        try:
            # Construct the URL with the email parameter properly
            response = requests.get(GOOGLE_SCRIPT_URL, params={'email': email})
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text}")

            if not response.text.strip():
                return "No data returned from Apps Script", 500

            guest = response.json()

            if not guest:
                return render_template('guest_not_found.html'), 404

            # Renders the guest information
            return render_template('checkin.html', guest=guest)

        except Exception as e:
            return f"Error: {str(e)}", 500

    return render_template('email_checkin.html')

@app.route('/static/css/checkin.css')
def css_test():
    return "Static file is accessible"

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True, port=5003)
