from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Your Google Apps Script URL
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxpsm_fUzUGOCWclZmshxcgBUC6WndS3S4zl7zYvIR9TIuxoVe_CLTC-3l4achAvB0avQ/exec"

@app.route('/checkin/<barcode>')
def checkin(barcode):
    try:
        # Send a request to the Apps Script web app with barcode
        response = requests.get(GOOGLE_SCRIPT_URL, params={'barcode': barcode})
        guest = response.json()

        if not guest:
            return render_template('guest_not_found.html'), 404

        # Render the guest information
        return render_template('checkin.html', guest=guest)

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/checkin-by-email', methods=['GET', 'POST'])
def checkin_by_email():
    if request.method == 'POST':
        email = request.form.get('email')

        # Send request to the Apps Script to search by email
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

            # Render the guest information
            return render_template('checkin.html', guest=guest)

        except Exception as e:
            return f"Error: {str(e)}", 500

    return render_template('email_checkin.html')

@app.route('/static/css/checkin.css')
def css_test():
    return "Static file is accessible"

if __name__ == '__main__':
    app.run(debug=True, port=5003)
