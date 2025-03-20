import pandas as pd
import requests
from datetime import datetime
import time

def process_excel_time_entries(excel_file_path):
    """
    Process time entries from Excel file and submit them to the time tracking application
    
    Parameters:
    excel_file_path (str): Path to the Excel file containing time entries
    """
    # Load the Excel file
    print(f"Loading Excel file: {excel_file_path}")
    df = pd.read_excel(excel_file_path)
    
    # Rename columns to standardize (based on the provided example)
    column_mapping = {
        'Date': 'Date',
        'Person': 'Team Member',
        'Hours (Fractional)': 'Hours',
        'Comment': 'Comment',
        'Category': 'Category'
    }
    
    # Create a new DataFrame with only the columns we need
    processed_df = pd.DataFrame()
    for excel_col, app_col in column_mapping.items():
        if excel_col in df.columns:
            processed_df[app_col] = df[excel_col]
    
    # Ensure dates are in the correct format (YYYY-MM-DD)
    processed_df['Date'] = pd.to_datetime(processed_df['Date']).dt.strftime('%Y-%m-%d')
    
    # Group entries by date and team member
    grouped = processed_df.groupby(['Date', 'Team Member'])
    
    # Process each group (date + team member combination)
    total_submitted = 0
    
    for (date, team_member), group in grouped:
        # Calculate total hours for this date/person
        total_hours = round(group['Hours'].sum(), 1)
        
        # Prepare the task data
        tasks = []
        for idx, row in group.iterrows():
            task = {
                'category': row['Category'],
                'project': '',  # No project mapping provided in Excel
                'hours': row['Hours'],
                'comment': row['Comment'] if not pd.isna(row['Comment']) else ''
            }
            tasks.append(task)
        
        # Submit this group's entries
        success = submit_time_entry(date, team_member, total_hours, tasks)
        if success:
            total_submitted += 1
            print(f"Successfully submitted entry for {team_member} on {date}")
        else:
            print(f"Failed to submit entry for {team_member} on {date}")
        
        # Add a small delay to avoid overwhelming the server
        time.sleep(0.5)
    
    print(f"\nComplete! Successfully submitted {total_submitted} time entry groups.")

def submit_time_entry(date, team_member, total_hours, tasks):
    """
    Submit a time entry to the application via POST request
    
    Parameters:
    date (str): Date in YYYY-MM-DD format
    team_member (str): Name of team member
    total_hours (float): Total hours for this entry
    tasks (list): List of task dictionaries with category, project, hours, and comment
    
    Returns:
    bool: True if submission was successful, False otherwise
    """
    # URL for the form submission (assuming the app is running locally)
    url = "http://localhost:5000/form"
    
    # Prepare the form data
    form_data = {
        'entry_date': date,
        'team_member': team_member,
        'hours': str(total_hours),
        'time_balance': 'on'  # Checkbox is checked
    }
    
    # Add the tasks data
    for i, task in enumerate(tasks):
        form_data[f'tasks[{i}][category]'] = task['category']
        form_data[f'tasks[{i}][project]'] = task['project']
        form_data[f'tasks[{i}][hours]'] = str(task['hours'])
        form_data[f'tasks[{i}][comment]'] = task['comment']
    
    try:
        # Send POST request to the form
        response = requests.post(url, data=form_data)
        return response.status_code == 200 or response.status_code == 302  # 302 is redirect after success
    except Exception as e:
        print(f"Error submitting entry: {e}")
        return False

if __name__ == "__main__":
    # Example usage
    excel_file_path = "time_entries.xlsx"
    
    # Ask for file path if not hardcoded
    if excel_file_path == "time_entries.xlsx":
        excel_file_path = input("Enter the path to your Excel file: ")
    
    process_excel_time_entries(excel_file_path)