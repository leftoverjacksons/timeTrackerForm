from flask import Flask, render_template, request, redirect, url_for
import gspread
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Path to the service account key
    key_file_path = os.path.join(app.root_path, 'keys', 'dt-resource-tracker-db3f71699674.json')

    try:
        # Connect to Google Sheets using the relative path
        gc = gspread.service_account(filename=key_file_path)

        # Use the actual key from your Google Sheet's URL
        sh = gc.open_by_key('1gmK-3cT9hdRfXdG8FV4YMti6mgKVIBLarufkLQDvzeA')  
        # Access the worksheet by name
        worksheet = sh.worksheet("BACKEND DATA FOR APP.PY")

        # Fetch the data from the worksheet
        # Sort team members alphabetically before passing to the template
        team_members = sorted(worksheet.col_values(1)[1:])  # Skip header
        categories = list(set(worksheet.col_values(2)[1:]))  # Skip header and remove duplicates

        # If the request method is POST, handle the form submission (not shown)
        if request.method == 'POST':
            # Process the form data (not implemented)
            # For example: form_data = request.form
            # Save or process your form data here

            # Redirect to the same page to show the updated info or clear the form
            return redirect(url_for('index'))

    except gspread.exceptions.GSpreadException as e:
        print("Error accessing Google Sheet:", e)
        # Handle the error as you see fit (maybe pass an error message to the template)
        team_members = []
        categories = []

    # Calculate the number of categories for slider initialization
    num_categories = len(categories) if categories else 1  # Avoid division by zero

    # Render the template, passing the team_members and categories
    return render_template('form.html', team_members=team_members, categories=categories, num_categories=num_categories)

if __name__ == '__main__':
    app.run(debug=True)
