from flask import Flask, render_template, request, redirect, url_for
import gspread
import os
from datetime import datetime
from gspread.exceptions import WorksheetNotFound

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
        categories = sorted(list(set(worksheet.col_values(2)[1:])))  # Skip header and remove duplicates
        npi_subfields = worksheet.col_values(3)[1:]  # Assuming subfields start at the second row
        sustaining_subfields = worksheet.col_values(3)[1:]  # Assuming subfields start at the second row

        # If the request method is POST, handle the form submission
        if request.method == 'POST':
            # Extract form data
            form_data = request.form.to_dict()
            print('Form data received:', form_data)  # Add this line to log the form data

            team_member = form_data.pop('team_member')
            total_hours = form_data.pop('hours')
            date_now = str(datetime.now())

            # Select the 'LOG' sheet or create it if it does not exist
            try:
                log_worksheet = sh.worksheet('LOG')
            except WorksheetNotFound:
                log_worksheet = sh.add_worksheet(title='LOG', rows="100", cols="20")

            # Check if headers need to be written
            if not log_worksheet.get_all_values():
                # The first row is empty, so we need to write the headers
                headers = ['Date', 'Team Member', 'Total Hours'] + \
                          [f"{category} Hours" for category in categories] + \
                          [f"{category} Subfield" for category in categories if category in ['NPI', 'Sustaining']] + \
                          ['Comments']
                log_worksheet.append_row(headers)

            # Prepare the data to be written
            # Inside your POST request handling
            row_data = [date_now, team_member, total_hours]
            for category in categories:
                hours_field = f"{category.lower()}_hours"
                category_hours = form_data.get(hours_field, "0")
                row_data.append(category_hours)
                if category in ['NPI', 'Sustaining']:
                    subfield_field = f"{category.lower()}_subfield"
                    category_subfield = form_data.get(subfield_field, "N/A")
                    row_data.append(category_subfield)


            # Append the data to the sheet
            log_worksheet.append_row(row_data)



            # Redirect to the same page to show the updated info or clear the form
            return redirect(url_for('index'))

    except gspread.exceptions.GSpreadException as e:
        print("Error accessing Google Sheet:", e)
        # Handle the error as you see fit (maybe pass an error message to the template)
        team_members = []
        categories = []
        npi_subfields = []
        sustaining_subfields = []

    # Calculate the number of categories for slider initialization
    num_categories = len(categories) if categories else 1  # Avoid division by zero

    # Render the template, passing the team_members, categories, and subfields
    return render_template('form.html', team_members=team_members, categories=categories, num_categories=num_categories, npi_subfields=npi_subfields, sustaining_subfields=sustaining_subfields)

if __name__ == '__main__':
    app.run(debug=True)
