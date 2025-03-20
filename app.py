from flask import Flask, render_template, request, redirect, url_for, jsonify
import gspread
import os
import pandas as pd
from datetime import datetime
from gspread.exceptions import WorksheetNotFound

app = Flask(__name__)

def get_gsheet_connection():
    """Helper function to connect to Google Sheets"""
    # Path to the service account key
    key_file_path = os.path.join(app.root_path, 'keys', 'dt-resource-tracker-db3f71699674.json')
    
    try:
        # Connect to Google Sheets using the relative path
        gc = gspread.service_account(filename=key_file_path)
        
        # Use the actual key from your Google Sheet's URL
        sh = gc.open_by_key('1gmK-3cT9hdRfXdG8FV4YMti6mgKVIBLarufkLQDvzeA')
        
        return sh
    except Exception as e:
        print(f"Error connecting to Google Sheet: {e}")
        return None

def get_log_data():
    """Retrieve and process data from the LOG sheet"""
    sh = get_gsheet_connection()
    if not sh:
        return pd.DataFrame()
    
    try:
        # Get the LOG worksheet
        log_worksheet = sh.worksheet('LOG')
        
        # Get all values including headers
        data = log_worksheet.get_all_values()
        
        if not data:
            return pd.DataFrame()
            
        # Convert to DataFrame
        headers = data[0]
        records = data[1:]
        df = pd.DataFrame(records, columns=headers)
        
        # Convert date strings to datetime objects
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Convert hours to numeric
        df['Hours'] = pd.to_numeric(df['Hours'], errors='coerce')
        
        return df
    except Exception as e:
        print(f"Error retrieving log data: {e}")
        return pd.DataFrame()

@app.route('/')
def portal():
    """Main portal page"""
    return render_template('index.html')

@app.route('/form', methods=['GET', 'POST'])
def form():
    """Time entry form route"""
    sh = get_gsheet_connection()
    if not sh:
        return render_template('form.html', 
                              team_members=[], 
                              categories=[], 
                              npi_subfields=[],
                              sustaining_subfields=[],
                              all_subfields=[],
                              error="Could not connect to Google Sheets")
    
    try:
        # Access the worksheet by name
        worksheet = sh.worksheet("BACKEND DATA FOR APP.PY")

        # Fetch the data from the worksheet
        # Sort team members alphabetically before passing to the template
        team_members = sorted(worksheet.col_values(1)[1:])  # Skip header
        categories = sorted(list(set(worksheet.col_values(2)[1:])))  # Skip header and remove duplicates
        
        # Get all subfields from column 3
        all_subfields = worksheet.col_values(3)[1:]  # Assuming subfields start at the second row
        
        # Filter out empty values and duplicates
        all_subfields = [subfield for subfield in all_subfields if subfield.strip()]
        unique_subfields = list(set(all_subfields))
        
        # For now, we'll use the same subfields for both NPI and Sustaining
        npi_subfields = unique_subfields
        sustaining_subfields = unique_subfields

        # If the request method is POST, handle the form submission
        if request.method == 'POST':
            # Extract form data
            form_data = request.form.to_dict(flat=False)
            print('Form data received:', form_data)  # Log the form data
            
            team_member = form_data.get('team_member', [''])[0]
            total_hours = form_data.get('hours', ['8'])[0]
            
            # Use the user-selected date instead of the current timestamp
            entry_date = form_data.get('entry_date', [''])[0]
            if not entry_date:
                # Fallback to current date if not provided
                entry_date = datetime.now().strftime('%Y-%m-%d')
            
            # Extract tasks data
            tasks = []
            
            # Process tasks data from form_data
            task_indices = set()
            for key in form_data:
                if key.startswith('tasks[') and '][category]' in key:
                    # Extract the task index from the key (e.g., 'tasks[0][category]' -> '0')
                    task_index = key[key.find('[')+1:key.find(']')]
                    task_indices.add(task_index)
            
            for idx in task_indices:
                category_key = f'tasks[{idx}][category]'
                project_key = f'tasks[{idx}][project]'
                hours_key = f'tasks[{idx}][hours]'
                comment_key = f'tasks[{idx}][comment]'
                
                if category_key in form_data and hours_key in form_data:
                    category = form_data[category_key][0]
                    project = form_data.get(project_key, [''])[0]
                    hours = form_data[hours_key][0]
                    comment = form_data.get(comment_key, [''])[0]
                    
                    if category and hours:  # Only add tasks with both category and hours
                        tasks.append({
                            'category': category,
                            'project': project,
                            'hours': hours,
                            'comment': comment
                        })
            
            # Select the 'LOG' sheet or create it if it does not exist
            try:
                log_worksheet = sh.worksheet('LOG')
            except WorksheetNotFound:
                log_worksheet = sh.add_worksheet(title='LOG', rows="100", cols="20")

            # Check if headers need to be written
            all_values = log_worksheet.get_all_values()
            needs_headers = False

            if not all_values:
                # Sheet is completely empty
                needs_headers = True
            else:
                # Check if the first row contains our expected headers
                first_row = all_values[0]
                expected_headers = ['Date', 'Team Member', 'Category', 'Project', 'Hours', 'Comments']
    
                # Check if first row is empty or doesn't match our headers
                if not first_row or set(expected_headers) != set(first_row):
                    needs_headers = True

            if needs_headers:
                # Clear any existing content from the first row
                if all_values:
                    log_worksheet.update('A1:F1', [['', '', '', '', '', '']])
    
                # Add the headers
                headers = ['Date', 'Team Member', 'Category', 'Project', 'Hours', 'Comments']
                log_worksheet.update('A1:F1', [headers])
                print("Added headers to LOG sheet")

            # Write each task as a separate row
            for task in tasks:
                row_data = [
                    entry_date,
                    team_member,
                    task['category'],
                    task['project'],
                    task['hours'],
                    task['comment']
                ]
                log_worksheet.append_row(row_data)

            # Redirect to the same page to show the updated info or clear the form
            return redirect(url_for('form'))

    except Exception as e:
        print(f"Error processing form data: {e}")
        team_members = []
        categories = []
        npi_subfields = []
        sustaining_subfields = []
        unique_subfields = []

    # Render the template, passing the team_members, categories, and subfields
    return render_template('form.html', 
                          team_members=team_members, 
                          categories=categories, 
                          npi_subfields=npi_subfields, 
                          sustaining_subfields=sustaining_subfields,
                          all_subfields=unique_subfields)

@app.route('/analytics')
def analytics():
    """Analytics dashboard route"""
    return render_template('analytics.html')

@app.route('/api/time-data')
def time_data_api():
    """API endpoint to get time tracking data"""
    try:
        df = get_log_data()
        
        if df.empty:
            print("Warning: Log data is empty")
            # For debugging purposes, let's return sample data
            return jsonify({
                'success': True,
                'message': 'Note: Using sample data because the LOG sheet is empty',
                'summary': {
                    'total_hours': 40,
                    'total_entries': 5,
                    'team_members': 2,
                    'categories': 3,
                    'projects': 2,
                    'date_range': {
                        'start': '2025-03-10',
                        'end': '2025-03-17'
                    }
                },
                'by_category': {'Development': 20, 'Testing': 10, 'Meetings': 10},
                'by_team_member': {'John Doe': 25, 'Jane Smith': 15},
                'by_project': {'Project A': 30, 'Project B': 10},
                'by_date': {'2025-03-10': 8, '2025-03-11': 8, '2025-03-12': 8, '2025-03-13': 8, '2025-03-14': 8},
                'recent_entries': [
                    {'Date': '2025-03-14', 'Team Member': 'John Doe', 'Category': 'Development', 'Project': 'Project A', 'Hours': '8', 'Comments': 'Working on feature X'},
                    {'Date': '2025-03-13', 'Team Member': 'Jane Smith', 'Category': 'Testing', 'Project': 'Project A', 'Hours': '5', 'Comments': 'Testing feature X'},
                    {'Date': '2025-03-13', 'Team Member': 'Jane Smith', 'Category': 'Meetings', 'Project': 'Project B', 'Hours': '3', 'Comments': 'Planning meeting'},
                    {'Date': '2025-03-12', 'Team Member': 'John Doe', 'Category': 'Development', 'Project': 'Project A', 'Hours': '8', 'Comments': 'Working on feature Y'},
                    {'Date': '2025-03-11', 'Team Member': 'John Doe', 'Category': 'Development', 'Project': 'Project B', 'Hours': '8', 'Comments': 'Working on feature Z'}
                ]
            })
        
        # Apply date filters if provided
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            df = df[df['Date'] >= pd.to_datetime(start_date)]
        
        if end_date:
            df = df[df['Date'] <= pd.to_datetime(end_date)]
        
        # If filtering resulted in empty dataframe
        if df.empty:
            return jsonify({
                'success': False,
                'message': 'No data available for the selected date range'
            })
        
        # Generate timeline data (hours by date)
        timeline_data = df.groupby(df['Date'].dt.strftime('%Y-%m-%d'))['Hours'].sum().to_dict()
        
        # Process data for analytics
        data = {
            'success': True,
            'summary': {
                'total_hours': float(df['Hours'].sum()),
                'total_entries': len(df),
                'team_members': df['Team Member'].nunique(),
                'categories': df['Category'].nunique(),
                'projects': df['Project'].nunique(),
                'date_range': {
                    'start': df['Date'].min().strftime('%Y-%m-%d'),
                    'end': df['Date'].max().strftime('%Y-%m-%d')
                }
            },
            'by_category': df.groupby('Category')['Hours'].sum().to_dict(),
            'by_team_member': df.groupby('Team Member')['Hours'].sum().to_dict(),
            'by_project': df.groupby('Project')['Hours'].sum().to_dict(),
            'by_date': timeline_data,
            'recent_entries': df.sort_values('Date', ascending=False).head(10).to_dict('records')
        }
        
        return jsonify(data)
    except Exception as e:
        print(f"Error in API endpoint: {e}")
        # Return error with more details for debugging
        return jsonify({
            'success': False,
            'message': f'Error processing data: {str(e)}',
            'error_type': str(type(e).__name__)
        })
    
    return jsonify(data)

# if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    app.run()  # Remove debug=True