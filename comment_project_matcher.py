import pandas as pd
import gspread
import os
from difflib import get_close_matches
import re
from pprint import pprint

class CommentProjectMatcher:
    def __init__(self, google_sheet_key='1gmK-3cT9hdRfXdG8FV4YMti6mgKVIBLarufkLQDvzeA', 
                 service_account_path='keys/dt-resource-tracker-db3f71699674.json'):
        """
        Initialize the Comment Project Matcher
        
        Parameters:
        google_sheet_key (str): The key of the Google Sheet containing the LOG data
        service_account_path (str): Path to the Google service account credentials file
        """
        self.google_sheet_key = google_sheet_key
        self.service_account_path = service_account_path
        self.projects = []
        self.log_data = None
        self.updated_rows = 0
        self.fuzzy_match_threshold = 0.8  # Threshold for fuzzy matching (0.0 to 1.0)
        
    def normalize_text(self, text):
        """Normalize text for better fuzzy matching"""
        if not text or not isinstance(text, str):
            return ""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and extra spaces
        text = re.sub(r'[^\w\s]', '', text)
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
        
    def find_project_in_comment(self, comment, projects):
        """
        Look for a project name in a comment using fuzzy matching
        
        Parameters:
        comment (str): The comment text to search in
        projects (list): List of project names to search for
        
        Returns:
        str or None: The matched project name or None if no match found
        """
        if not comment or not isinstance(comment, str) or comment.strip() == "":
            return None
            
        # Normalize comment
        normalized_comment = self.normalize_text(comment)
        if not normalized_comment:
            return None
            
        # Normalize project names
        normalized_projects = {self.normalize_text(p): p for p in projects if p and isinstance(p, str)}
        
        # First try direct substring matching (case-insensitive)
        for norm_proj, orig_proj in normalized_projects.items():
            if norm_proj and norm_proj in normalized_comment:
                print(f"Direct match found: '{orig_proj}' in '{comment}'")
                return orig_proj
        
        # If no direct substring match, try word-level fuzzy matching
        comment_words = normalized_comment.split()
        for word in comment_words:
            if len(word) < 3:  # Skip very short words
                continue
                
            # Try fuzzy matching with word
            matches = get_close_matches(word, normalized_projects.keys(), n=1, cutoff=self.fuzzy_match_threshold)
            if matches:
                matched_proj = normalized_projects[matches[0]]
                print(f"Fuzzy match found: '{word}' → '{matched_proj}' in '{comment}'")
                return matched_proj
                
        # If still no match, try matching against multi-word phrases in the comment
        for phrase_length in range(2, min(5, len(comment_words) + 1)):
            for i in range(len(comment_words) - phrase_length + 1):
                phrase = ' '.join(comment_words[i:i+phrase_length])
                
                # Try fuzzy matching with phrase
                matches = get_close_matches(phrase, normalized_projects.keys(), n=1, cutoff=self.fuzzy_match_threshold)
                if matches:
                    matched_proj = normalized_projects[matches[0]]
                    print(f"Phrase fuzzy match found: '{phrase}' → '{matched_proj}' in '{comment}'")
                    return matched_proj
        
        return None
    
    def connect_to_gsheet(self):
        """Connect to the Google Sheet and return the worksheet"""
        try:
            print(f"Connecting to Google Sheet with key: {self.google_sheet_key}")
            gc = gspread.service_account(filename=self.service_account_path)
            sh = gc.open_by_key(self.google_sheet_key)
            return sh
        except Exception as e:
            print(f"Error connecting to Google Sheet: {e}")
            return None
    
    def load_projects(self):
        """Load project list from the backend data worksheet"""
        sh = self.connect_to_gsheet()
        if not sh:
            print("Failed to connect to Google Sheet. Cannot load projects.")
            return False
            
        try:
            # Access the worksheet with project data
            worksheet = sh.worksheet("BACKEND DATA FOR APP.PY")
            
            # Get all projects from column 4
            all_projects = worksheet.col_values(4)[1:]  # Skip header
            
            # Filter out empty values and duplicates
            self.projects = [proj for proj in all_projects if proj and proj.strip()]
            self.projects = list(set(self.projects))  # Remove duplicates
            
            print(f"Loaded {len(self.projects)} projects")
            
            # Print the first few projects for verification
            if self.projects:
                print("Sample projects:")
                for i, proj in enumerate(self.projects[:5]):
                    print(f"  {i+1}. {proj}")
                
                if len(self.projects) > 5:
                    print(f"  ... and {len(self.projects) - 5} more")
            
            return True
        except Exception as e:
            print(f"Error loading projects: {e}")
            return False
    
    def load_log_data(self):
        """Load all log data from the LOG worksheet"""
        sh = self.connect_to_gsheet()
        if not sh:
            print("Failed to connect to Google Sheet. Cannot load log data.")
            return False
            
        try:
            # Access the LOG worksheet
            log_worksheet = sh.worksheet('LOG')
            
            # Get all values including headers
            data = log_worksheet.get_all_values()
            
            if not data:
                print("LOG sheet is empty")
                return False
                
            # Convert to DataFrame
            headers = data[0]
            records = data[1:]
            self.log_data = pd.DataFrame(records, columns=headers)
            
            # Print summary information
            print(f"Loaded {len(self.log_data)} log entries")
            print(f"Columns: {', '.join(self.log_data.columns)}")
            
            # Print the first few rows for verification
            if not self.log_data.empty:
                print("\nSample data:")
                print(self.log_data.head(2).to_string())
            
            return True
        except Exception as e:
            print(f"Error loading log data: {e}")
            return False
    
    def process_log_entries(self, dry_run=True):
        """
        Process log entries to update empty project fields based on comments
        
        Parameters:
        dry_run (bool): If True, only shows what would be updated without making changes
        
        Returns:
        bool: True if successful, False otherwise
        """
        if not self.projects:
            print("No projects loaded. Call load_projects() first.")
            return False
            
        if self.log_data is None or self.log_data.empty:
            print("No log data loaded. Call load_log_data() first.")
            return False
        
        # Prepare a project column index
        project_col_index = None
        for i, col in enumerate(self.log_data.columns):
            if col.strip().lower() == 'project':
                project_col_index = i
                break
                
        if project_col_index is None:
            print("Project column not found in log data")
            return False
            
        # Prepare a comments column index
        comments_col_index = None
        comments_col_names = ['Comments', 'Comment', 'comments', 'comment']
        for i, col in enumerate(self.log_data.columns):
            if col in comments_col_names:
                comments_col_index = i
                break
                
        if comments_col_index is None:
            print("Comments column not found in log data")
            return False
            
        # Process each row
        updated_entries = []
        updates_by_project = {}
        
        for index, row in self.log_data.iterrows():
            # Skip rows that already have a project
            project = str(row.iloc[project_col_index]).strip()
            if project:
                continue
                
            # Get the comment
            comment = str(row.iloc[comments_col_index])
            
            # Skip rows without comments
            if not comment or comment.strip() == "":
                continue
                
            # Try to find a project in the comment
            matched_project = self.find_project_in_comment(comment, self.projects)
            
            if matched_project:
                # Store the update for later
                updated_entries.append({
                    'index': index,
                    'row_index': index + 2,  # +2 because 0-indexing and header row
                    'old_project': project,
                    'new_project': matched_project,
                    'comment': comment,
                    'team_member': row.iloc[1] if len(row) > 1 else "",  # Team Member is usually in column 2
                    'category': row.iloc[2] if len(row) > 2 else "",     # Category is usually in column 3
                    'date': row.iloc[0] if len(row) > 0 else ""          # Date is usually in column 1
                })
                
                # Update count by project
                if matched_project not in updates_by_project:
                    updates_by_project[matched_project] = 0
                updates_by_project[matched_project] += 1
        
        # Print summary of proposed updates
        if updated_entries:
            print(f"\nFound {len(updated_entries)} entries to update")
            
            print("\nUpdates by project:")
            for project, count in sorted(updates_by_project.items(), key=lambda x: x[1], reverse=True):
                print(f"  {project}: {count} entries")
                
            print("\nSample updates:")
            for i, update in enumerate(updated_entries[:5]):
                print(f"\n  {i+1}. Row {update['row_index']} - {update['date']} - {update['team_member']}")
                print(f"     Category: {update['category']}")
                print(f"     Comment: {update['comment'][:50]}{'...' if len(update['comment']) > 50 else ''}")
                print(f"     Project: '{update['old_project']}' → '{update['new_project']}'")
                
            if len(updated_entries) > 5:
                print(f"\n  ... and {len(updated_entries) - 5} more updates")
            
            # If not a dry run, apply the updates
            if not dry_run:
                print("\nApplying updates...")
                self.apply_updates(updated_entries, project_col_index)
            else:
                print("\nDRY RUN MODE: No changes applied. Run with dry_run=False to apply changes.")
        else:
            print("No entries found that need updating")
            
        self.updated_rows = len(updated_entries)
        return True
    
    def apply_updates(self, updates, project_col_index):
        """
        Apply the updates to the Google Sheet
        
        Parameters:
        updates (list): List of update dictionaries
        project_col_index (int): Index of the project column
        
        Returns:
        bool: True if successful, False otherwise
        """
        sh = self.connect_to_gsheet()
        if not sh:
            print("Failed to connect to Google Sheet. Cannot apply updates.")
            return False
            
        try:
            # Access the LOG worksheet
            log_worksheet = sh.worksheet('LOG')
            
            # Process updates in smaller batches to avoid API limits
            batch_size = 10  # Smaller batch size to reduce likelihood of errors
            total_updated = 0
            
            print(f"Applying updates in batches of {batch_size}...")
            
            # Process updates in batches
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i+batch_size]
                
                for update in batch:
                    row = update['row_index']
                    col = project_col_index + 1  # +1 because gspread uses 1-indexing for columns
                    new_project = update['new_project']
                    
                    # Update cell one at a time
                    log_worksheet.update_cell(row, col, new_project)
                    total_updated += 1
                
                print(f"  Progress: {total_updated}/{len(updates)} entries updated")
                
                # Add a small delay between batches to avoid rate limiting
                if i + batch_size < len(updates):
                    import time
                    time.sleep(1)
            
            print(f"Successfully updated {total_updated} entries")
            return True
        except Exception as e:
            print(f"Error applying updates: {e}")
            return False
    
    def run(self, dry_run=True):
        """
        Run the complete process
        
        Parameters:
        dry_run (bool): If True, only shows what would be updated without making changes
        
        Returns:
        bool: True if successful, False otherwise
        """
        print("=== Comment to Project Matcher ===")
        
        # Load projects
        print("\n1. Loading projects...")
        if not self.load_projects():
            print("Failed to load projects. Aborting.")
            return False
            
        # Load log data
        print("\n2. Loading log data...")
        if not self.load_log_data():
            print("Failed to load log data. Aborting.")
            return False
            
        # Process log entries
        print("\n3. Processing log entries...")
        result = self.process_log_entries(dry_run=dry_run)
        
        print("\n=== Process Complete ===")
        print(f"Total entries processed: {len(self.log_data) if self.log_data is not None else 0}")
        print(f"Entries updated: {self.updated_rows}")
        
        return result

# Example usage
if __name__ == "__main__":
    # Create the matcher
    matcher = CommentProjectMatcher()
    
    # Ask if it's a dry run
    response = input("Run in dry mode (no changes will be made)? (y/n, default: y): ").strip().lower()
    dry_run = response != 'n'
    
    # Set fuzzy match threshold
    threshold_input = input("Enter fuzzy match threshold (0.0-1.0, default: 0.8): ").strip()
    if threshold_input and threshold_input.replace('.', '', 1).isdigit():
        threshold = float(threshold_input)
        if 0 <= threshold <= 1:
            matcher.fuzzy_match_threshold = threshold
    
    print(f"Using fuzzy match threshold: {matcher.fuzzy_match_threshold}")
    
    # Run the matcher
    matcher.run(dry_run=dry_run)