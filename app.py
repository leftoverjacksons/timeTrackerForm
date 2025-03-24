from flask import Flask, render_template, request, redirect, url_for, jsonify
import gspread
import os
import pandas as pd
from datetime import datetime
from gspread.exceptions import WorksheetNotFound
import re
from difflib import get_close_matches

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

def normalize_text(text):
    """Normalize text for better fuzzy matching"""
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and extra spaces
    text = re.sub(r'[^\w\s]', '', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def find_close_match(input_project, existing_projects, threshold=0.7):
    """
    Find a close match for the input project in the existing projects list using fuzzy matching
    
    Parameters:
    input_project (str): The project name entered by the user
    existing_projects (list): List of existing project names
    threshold (float): The similarity threshold for considering a match (0.0 to 1.0)
    
    Returns:
    str or None: The matched existing project name or None if no match found
    """
    if not input_project:
        return None
        
    # Normalize input
    normalized_input = normalize_text(input_project)
    if not normalized_input:
        return None
    
    # Normalize existing projects
    normalized_projects = [normalize_text(p) for p in existing_projects if p]
    
    # Create a mapping from normalized names back to original names
    original_mapping = {normalize_text(p): p for p in existing_projects if p}
    
    # Try to find a direct match first (case-insensitive)
    for norm_proj, orig_proj in original_mapping.items():
        if norm_proj == normalized_input:
            return orig_proj
    
    # Try fuzzy matching
    matches = get_close_matches(normalized_input, normalized_projects, n=1, cutoff=threshold)
    
    if matches:
        # Return the original project name
        return original_mapping[matches[0]]
    
    return None

def add_project_to_backend(new_project, worksheet=None):
    """
    Add a new project to the backend data
    
    Parameters:
    new_project (str): The new project name to add
    worksheet (gspread.Worksheet, optional): The worksheet object
    
    Returns:
    bool: True if successful, False otherwise
    """
    if not new_project or new_project.strip() == "":
        return False
        
    # If no worksheet is provided, get a connection
    if worksheet is None:
        sh = get_gsheet_connection()
        if not sh:
            return False
        
        try:
            worksheet = sh.worksheet("BACKEND DATA FOR APP.PY")
        except Exception as e:
            print(f"Error accessing worksheet: {e}")
            return False
    
    try:
        # Get all projects from column 4
        all_projects = worksheet.col_values(4)[1:]  # Skip header
        
        # Check if the project already exists (exact match)
        if new_project in all_projects:
            print(f"Project already exists: {new_project}")
            return True  # Already exists, no need to add
        
        # Find the first empty cell in column 4 (project column)
        next_row = len(all_projects) + 2  # +2 because: +1 for header, +1 for 1-indexed
        
        # Update the cell with the new project
        worksheet.update_cell(next_row, 4, new_project)
        
        print(f"Added new project: {new_project}")
        return True
    except Exception as e:
        print(f"Error adding project to backend: {e}")
        return False

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
                              product_families=[],
                              projects=[],
                              all_product_families=[],
                              all_projects=[],
                              error="Could not connect to Google Sheets")
    
    try:
        # Access the worksheet by name
        worksheet = sh.worksheet("BACKEND DATA FOR APP.PY")

        # Fetch the data from the worksheet
        # Sort team members alphabetically before passing to the template
        team_members = sorted(worksheet.col_values(1)[1:])  # Skip header
        categories = sorted(list(set(worksheet.col_values(2)[1:])))  # Skip header and remove duplicates
        
        # Get all product families from column 3 (renamed from subfields)
        all_product_families = worksheet.col_values(3)[1:]  # Skip header
        
        # Get all projects from column 4
        all_projects = worksheet.col_values(4)[1:]  # Skip header
        
        # Filter out empty values and duplicates
        all_product_families = [pf for pf in all_product_families if pf.strip()]
        unique_product_families = sorted(list(set(all_product_families)))
        
        all_projects = [proj for proj in all_projects if proj.strip()]
        unique_projects = sorted(list(set(all_projects)))

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
                product_family_key = f'tasks[{idx}][product_family]'
                project_key = f'tasks[{idx}][project]'
                hours_key = f'tasks[{idx}][hours]'
                comment_key = f'tasks[{idx}][comment]'

                if category_key in form_data:
                    category = form_data[category_key][0]
                    product_family = form_data.get(product_family_key, [''])[0]
                    
                    # Process project field - handle typed input with fuzzy matching
                    project_input = form_data.get(project_key, [''])[0].strip()
                    
                    # If project input is provided
                    if project_input:
                        # Try to find a close match in existing projects
                        matched_project = find_close_match(project_input, unique_projects)
                        
                        if matched_project:
                            # Use the matched existing project
                            project = matched_project
                            print(f"Matched '{project_input}' to existing project '{matched_project}'")
                        else:
                            # This is a new project, add it to the backend
                            project = project_input
                            add_project_to_backend(project, worksheet)
                    else:
                        project = ""

                    # Get hours, handling empty or invalid values
                    hours = form_data.get(hours_key, [''])[0]
                    if not hours or hours.strip() == '':
                        # Calculate hours based on percentage if not explicitly set
                        # This is a fallback measure in case the JavaScript doesn't set hours properly
                        total_hours = float(form_data.get('hours', ['8'])[0])
                        task_count = len(task_indices)
                        hours = str(round(total_hours / task_count, 1))
                        print(f"Warning: Empty hours value for task {idx}, defaulting to {hours}")

                    comment = form_data.get(comment_key, [''])[0]

                    # Validate that both category and product family are filled out
                    if category and product_family:
                        tasks.append({
                            'category': category,
                            'product_family': product_family,
                            'project': project,
                            'hours': hours,
                            'comment': comment
                        })
                    elif category and not product_family:
                        error_message = f"Product Family is required for all tasks. Task {int(idx)+1} is missing a Product Family."
                        print(f"ERROR: {error_message}")
                        return render_template('form.html', 
                                          team_members=team_members, 
                                          categories=categories, 
                                          product_families=unique_product_families,
                                          projects=unique_projects,
                                          all_product_families=unique_product_families,
                                          all_projects=unique_projects,
                                          error_message=error_message)

            # Validate that at least one task has been added
            if not tasks:
                error_message = "At least one task with a category and product family must be added."
                print(f"ERROR: {error_message}")
                return render_template('form.html', 
                                  team_members=team_members, 
                                  categories=categories, 
                                  product_families=unique_product_families,
                                  projects=unique_projects,
                                  all_product_families=unique_product_families,
                                  all_projects=unique_projects,
                                  error_message=error_message)
            
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
                expected_headers = ['Date', 'Team Member', 'Category', 'Product Family', 'Project', 'Hours', 'Comments']
    
                # Check if first row is empty or doesn't match our headers
                if not first_row or set(expected_headers) != set(first_row):
                    needs_headers = True

            if needs_headers:
                # Clear any existing content from the first row
                if all_values:
                    log_worksheet.update('A1:G1', [['', '', '', '', '', '', '']])
    
                # Add the headers
                headers = ['Date', 'Team Member', 'Category', 'Product Family', 'Project', 'Hours', 'Comments']
                log_worksheet.update('A1:G1', [headers])
                print("Added headers to LOG sheet")

            # Write each task as a separate row
            for task in tasks:
                row_data = [
                    entry_date,
                    team_member,
                    task['category'],
                    task['product_family'],
                    task['project'],
                    task['hours'],
                    task['comment']
                ]
                log_worksheet.append_row(row_data)

            # Redirect to the same page to show the updated info or clear the form
            return redirect(url_for('form'))

        # Render the template, passing the team_members, categories, and other data
        return render_template('form.html', 
                            team_members=team_members, 
                            categories=categories, 
                            product_families=unique_product_families,
                            projects=unique_projects,
                            all_product_families=unique_product_families,
                            all_projects=unique_projects)

    except Exception as e:
        print(f"Error processing form data: {e}")
        return render_template('form.html', 
                            team_members=[],
                            categories=[],
                            product_families=[],
                            projects=[],
                            all_product_families=[],
                            all_projects=[])

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
        
        # Create breakdown of hours by team member and category
        # First create a cross-tabulation
        team_category_pivot = pd.pivot_table(
            df, 
            values='Hours', 
            index='Team Member', 
            columns='Category', 
            aggfunc='sum', 
            fill_value=0
        )
        
        # Convert to nested dictionary format
        team_category_data = {}
        for team_member in team_category_pivot.index:
            team_category_data[team_member] = team_category_pivot.loc[team_member].to_dict()
        
        # Create breakdown of hours by team member and project
        team_project_pivot = pd.pivot_table(
            df, 
            values='Hours', 
            index='Team Member', 
            columns='Project', 
            aggfunc='sum', 
            fill_value=0
        )
        
        # Convert to nested dictionary format
        team_project_data = {}
        for team_member in team_project_pivot.index:
            team_project_data[team_member] = team_project_pivot.loc[team_member].to_dict()
        
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
            'recent_entries': df.sort_values('Date', ascending=False).head(10).to_dict('records'),
            'by_team_member_category': team_category_data,
            'by_team_member_project': team_project_data
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

if __name__ == '__main__':
    #app.run()  # remove debug=true
    app.run(host='0.0.0.0', port=5000, debug=True)