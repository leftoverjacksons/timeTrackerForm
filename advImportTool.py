import pandas as pd
import requests
from datetime import datetime
import time
import re
import json
import os

class TimeEntryImporter:
    def __init__(self, app_url="http://localhost:5000"):
        self.app_url = app_url
        self.project_mappings = {}
        self.load_project_mappings()
    
    def load_project_mappings(self):
        """Load project mappings from a JSON file if it exists, otherwise create an empty mapping"""
        mapping_file = "project_mappings.json"
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r') as f:
                    self.project_mappings = json.load(f)
                print(f"Loaded {len(self.project_mappings)} project mappings")
            except Exception as e:
                print(f"Error loading project mappings: {e}")
                self.project_mappings = {}
        else:
            print("No project mappings file found. Will create one when needed.")
            self.project_mappings = {}
    
    def save_project_mappings(self):
        """Save the project mappings to a JSON file"""
        try:
            with open("project_mappings.json", 'w') as f:
                json.dump(self.project_mappings, f, indent=2)
            print("Project mappings saved")
        except Exception as e:
            print(f"Error saving project mappings: {e}")
    
    def parse_time(self, time_str):
        """
        Parse time string in format like '7:00' or '0:30' to decimal hours
        """
        if pd.isna(time_str):
            return 0.0
            
        # If it's already a float/number, return it
        if isinstance(time_str, (int, float)):
            return float(time_str)
        
        # If we have a string with a colon (time format)
        if isinstance(time_str, str) and ':' in time_str:
            try:
                hours, minutes = time_str.split(':')
                return float(hours) + float(minutes) / 60
            except:
                return 0.0
        
        # Try to convert directly to float
        try:
            return float(time_str)
        except:
            return 0.0
    
    def ask_for_project(self, comment, category):
        """
        Ask the user to provide a project name for a specific comment/category
        """
        # Create a key for the project mapping
        mapping_key = f"{comment}|{category}"
        
        # Check if we already have a mapping
        if mapping_key in self.project_mappings:
            return self.project_mappings[mapping_key]
        
        # Ask for the project name
        print(f"\nTask: {comment}")
        print(f"Category: {category}")
        project = input("Enter project name (or press Enter to leave blank): ").strip()
        
        # Save mapping for future use
        self.project_mappings[mapping_key] = project
        self.save_project_mappings()
        
        return project
    
    def fetch_available_team_members_and_categories(self):
        """
        Fetch available team members and categories from the app
        """
        try:
            # Make a GET request to the form page
            response = requests.get(f"{self.app_url}/form")
            
            # Check if request was successful
            if response.status_code != 200:
                print(f"Failed to fetch form data: Status code {response.status_code}")
                return [], []
            
            # Extract team members and categories using regex
            html = response.text
            
            # Find team members
            team_members_pattern = r'option value="([^"]+)"'
            team_members_matches = re.findall(team_members_pattern, html)
            
            # Find categories
            categories_pattern = r'value="([^"]+)">([^<]+)</option>'
            categories_matches = re.findall(categories_pattern, html)
            
            # Extract unique values
            unique_team_members = list(set(team_members_matches))
            unique_categories = list(set([m[0] for m in categories_matches if m[0]]))
            
            return unique_team_members, unique_categories
            
        except Exception as e:
            print(f"Error fetching form data: {e}")
            return [], []
    
    def validate_team_member(self, team_member, available_members):
        """
        Validate and possibly correct team member names
        """
        if not available_members:
            return team_member
            
        if team_member in available_members:
            return team_member
            
        # Try to find a close match
        for member in available_members:
            if team_member.lower() in member.lower() or member.lower() in team_member.lower():
                return member
                
        # Ask user to select a team member
        print(f"\nTeam member '{team_member}' not found in the system.")
        print("Available team members:")
        for i, member in enumerate(available_members):
            print(f"{i+1}. {member}")
            
        selection = input(f"Select a team member for '{team_member}' (number or name): ").strip()
        
        # Parse the input
        try:
            # If it's a number
            idx = int(selection) - 1
            if 0 <= idx < len(available_members):
                return available_members[idx]
        except:
            # If it's a name
            if selection in available_members:
                return selection
                
        # If all else fails, return the original
        print(f"Using original team member name: {team_member}")
        return team_member
    
    def validate_category(self, category, available_categories):
        """
        Validate and possibly correct category names
        """
        if not available_categories:
            return category
            
        if category in available_categories:
            return category
            
        # Try to find a close match
        for cat in available_categories:
            if category.lower() in cat.lower() or cat.lower() in category.lower():
                return cat
                
        # Ask user to select a category
        print(f"\nCategory '{category}' not found in the system.")
        print("Available categories:")
        for i, cat in enumerate(available_categories):
            print(f"{i+1}. {cat}")
            
        selection = input(f"Select a category for '{category}' (number or name): ").strip()
        
        # Parse the input
        try:
            # If it's a number
            idx = int(selection) - 1
            if 0 <= idx < len(available_categories):
                return available_categories[idx]
        except:
            # If it's a name
            if selection in available_categories:
                return selection
                
        # If all else fails, return the original
        print(f"Using original category: {category}")
        return category
    
    def process_excel_file(self, excel_file_path, interactive=True):
        """
        Process Excel file containing time entries
        
        Parameters:
        excel_file_path (str): Path to the Excel file
        interactive (bool): Whether to interactively ask for missing information
        """
        # Load the Excel file
        print(f"Loading Excel file: {excel_file_path}")
        try:
            # Try with the engine parameter explicitly set to handle older .xls files
            if excel_file_path.lower().endswith('.xls'):
                print("Detected .xls file, using xlrd engine...")
                df = pd.read_excel(excel_file_path, engine='xlrd')
            else:
                df = pd.read_excel(excel_file_path)
            
            # Show the first few rows to confirm loading
            print("\nFirst few rows of the Excel file:")
            print(df.head(2).to_string())
            print(f"Total rows: {len(df)}\n")
            
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            print("\nTroubleshooting tips:")
            print("1. Make sure the file path is correct")
            print("2. For .xls files, install xlrd: pip install xlrd")
            print("3. For .xlsx files, install openpyxl: pip install openpyxl")
            print("4. Try removing any quotes from the file path")
            return False
        
        # Fetch available team members and categories
        team_members, categories = self.fetch_available_team_members_and_categories()
        if team_members:
            print(f"Available team members: {', '.join(team_members)}")
        if categories:
            print(f"Available categories: {', '.join(categories)}")
        
        # Check required columns
        required_columns = ['Date', 'Person', 'Category', 'Comment']
        time_columns = ['Hours', 'Hours (Fractional)']
        
        # Verify required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Missing required columns: {', '.join(missing_columns)}")
            return False
        
        # Verify at least one time column exists
        if not any(col in df.columns for col in time_columns):
            print(f"Missing time columns. Need at least one of: {', '.join(time_columns)}")
            return False
        
        # Process each row
        processed_rows = []
        
        for idx, row in df.iterrows():
            # Get date
            try:
                date = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
            except:
                print(f"Error converting date in row {idx+1}: {row['Date']}")
                continue
            
            # Get team member and validate
            team_member = str(row['Person']).strip()
            if interactive:
                team_member = self.validate_team_member(team_member, team_members)
            
            # Get category and validate
            category = str(row['Category']).strip()
            if interactive:
                category = self.validate_category(category, categories)
            
            # Get hours (try both columns)
            hours = 0.0
            if 'Hours (Fractional)' in df.columns and not pd.isna(row['Hours (Fractional)']):
                hours = self.parse_time(row['Hours (Fractional)'])
            elif 'Hours' in df.columns and not pd.isna(row['Hours']):
                hours = self.parse_time(row['Hours'])
            
            if hours <= 0:
                print(f"Invalid hours in row {idx+1}: {hours}")
                continue
            
            # Get comment
            comment = str(row['Comment']) if not pd.isna(row['Comment']) else ''
            
            # Get project (interactive)
            project = ""
            if interactive:
                project = self.ask_for_project(comment, category)
            
            # Add processed row
            processed_rows.append({
                'Date': date,
                'Team Member': team_member,
                'Category': category,
                'Project': project,
                'Hours': hours,
                'Comment': comment
            })
        
        # Group entries by date and team member
        df_processed = pd.DataFrame(processed_rows)
        grouped = df_processed.groupby(['Date', 'Team Member'])
        
        # Process each group
        total_submitted = 0
        
        for (date, team_member), group in grouped:
            # Calculate total hours
            total_hours = round(group['Hours'].sum(), 1)
            
            # Prepare tasks
            tasks = []
            for _, task_row in group.iterrows():
                task = {
                    'category': task_row['Category'],
                    'project': task_row['Project'],
                    'hours': task_row['Hours'],
                    'comment': task_row['Comment']
                }
                tasks.append(task)
            
            # Submit entry
            print(f"Submitting entry for {team_member} on {date} ({total_hours} hours, {len(tasks)} tasks)")
            success = self.submit_time_entry(date, team_member, total_hours, tasks)
            
            if success:
                total_submitted += 1
                print(f"✓ Successfully submitted")
            else:
                print(f"✗ Failed to submit")
            
            # Add delay
            time.sleep(0.5)
        
        print(f"\nComplete! Successfully submitted {total_submitted} time entry groups.")
        return True
    
    def submit_time_entry(self, date, team_member, total_hours, tasks):
        """
        Submit a time entry to the application
        
        Parameters:
        date (str): Date in YYYY-MM-DD format
        team_member (str): Team member name
        total_hours (float): Total hours
        tasks (list): List of task dictionaries
        
        Returns:
        bool: True if successful, False otherwise
        """
        # URL for the form submission
        url = f"{self.app_url}/form"
        
        # Prepare form data
        form_data = {
            'entry_date': date,
            'team_member': team_member,
            'hours': str(total_hours),
            'time_balance': 'on'
        }
        
        # Add tasks
        for i, task in enumerate(tasks):
            form_data[f'tasks[{i}][category]'] = task['category']
            form_data[f'tasks[{i}][project]'] = task['project']
            form_data[f'tasks[{i}][hours]'] = str(task['hours'])
            form_data[f'tasks[{i}][comment]'] = task['comment']
        
        try:
            # Send POST request
            response = requests.post(url, data=form_data)
            return response.status_code == 200 or response.status_code == 302
        except Exception as e:
            print(f"Error submitting entry: {e}")
            return False

if __name__ == "__main__":
    # Get app URL
    app_url = input("Enter the app URL (default: http://localhost:5000): ").strip()
    if not app_url:
        app_url = "http://localhost:5000"
    
    # Create importer
    importer = TimeEntryImporter(app_url)
    
    # Get Excel file path and handle quoted paths
    excel_file_path = input("Enter the path to your Excel file: ").strip()
    
    # Remove quotes if they exist
    if (excel_file_path.startswith('"') and excel_file_path.endswith('"')) or \
       (excel_file_path.startswith("'") and excel_file_path.endswith("'")):
        excel_file_path = excel_file_path[1:-1]
    
    # Ask if interactive mode
    interactive = input("Run in interactive mode to map projects? (y/n, default: y): ").strip().lower() != 'n'
    
    # Process file
    importer.process_excel_file(excel_file_path, interactive)