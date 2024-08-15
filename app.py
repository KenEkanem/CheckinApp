from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Your Google Apps Script URL
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxpTbTcB20cG6Vv9oXNpxMyaOWlL-y6jPHuPctoeIzi_bgSHv62Zl61UZct5YAjyxkzfw/exec"

@app.route('/checkin/<barcode>')
def checkin(barcode):
    try:
        # Send a request to the Apps Script web app with barcode
        response = requests.get(f"{GOOGLE_SCRIPT_URL}?barcode={barcode}")
        guest = response.json()

        if not guest:
            return "Guest not found!", 404

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
            response = requests.get(f"{GOOGLE_SCRIPT_URL}?email={email}")
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text}")

            # Check if response content is empty
            if not response.text.strip():
                return "No data returned from Apps Script", 500

            guest = response.json()

            if not guest:
                return "Guest not found!", 404

            # Render the guest information
            return render_template('checkin.html', guest=guest)

        except Exception as e:
            return f"Error: {str(e)}", 500

    return render_template('email_checkin.html')

if __name__ == '__main__':
    # Run the Flask application with a specified port (e.g., 8080)
    app.run(debug=True, port=5004)
