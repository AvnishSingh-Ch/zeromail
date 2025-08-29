#!/usr/bin/env python3
"""
Configuration and User Input Module for Gmail IMAP Cleaner

Handles user input, configuration validation, and authentication guidance.
"""

import getpass
import datetime
import logging


def validate_date_format(date_string):
    """
    Validate that a date string is in the correct DD-MMM-YYYY format.
    
    Args:
        date_string (str): Date string to validate
        
    Returns:
        bool: True if format is valid, False otherwise
    """
    try:
        datetime.datetime.strptime(date_string, "%d-%b-%Y")
        return True
    except ValueError:
        return False


def show_authentication_help():
    """
    Display helpful information about Gmail authentication requirements.
    """
    print("\n" + "=" * 70)
    print("GMAIL AUTHENTICATION SETUP REQUIRED")
    print("=" * 70)
    print("Gmail requires an App Password for IMAP access. Here's how to set it up:")
    print()
    print("1. Enable 2-Factor Authentication on your Gmail account:")
    print("   - Go to: https://myaccount.google.com/security")
    print("   - Turn on 2-Step Verification")
    print()
    print("2. Generate an App Password:")
    print("   - Go to: https://myaccount.google.com/apppasswords")
    print("   - Select 'Mail' and your device")
    print("   - Copy the 16-character password (remove spaces)")
    print()
    print("3. Use the App Password (not your regular Gmail password)")
    print("   - The app password looks like: abcd efgh ijkl mnop")
    print("   - Enter it as: abcdefghijklmnop (no spaces)")
    print()
    print("4. Alternative: Enable 'Less Secure Apps' (not recommended)")
    print("   - Go to: https://myaccount.google.com/lesssecureapps")
    print("   - Turn on 'Allow less secure apps'")
    print()
    print("For more help: https://support.google.com/accounts/answer/185833")
    print("=" * 70)


def get_folder_selection(imap_conn=None):
    """
    Get user's folder selection for email operations.
    
    Args:
        imap_conn: IMAP connection object to discover actual folder names
    
    Returns:
        list: List of selected folder names
    """
    # Common Gmail folder name variations
    gmail_folders = {
        'all_mail': ['[Gmail]/All Mail', '[Google Mail]/All Mail', 'All Mail'],
        'trash': ['[Gmail]/Trash', '[Google Mail]/Bin', '[Gmail]/Bin', 'Trash'],
        'spam': ['[Gmail]/Spam', '[Google Mail]/Spam', 'Spam'],
        'sent': ['[Gmail]/Sent Mail', '[Google Mail]/Sent Mail', 'Sent'],
        'drafts': ['[Gmail]/Drafts', '[Google Mail]/Drafts', 'Drafts']
    }
    
    # Try to discover actual folder names if connection is available
    actual_folders = {}
    if imap_conn:
        try:
            available_folders = imap_conn.list_folders()
            logging.info(f"Available folders: {available_folders}")
            
            # Map common names to actual folder names
            for folder_type, possible_names in gmail_folders.items():
                for possible_name in possible_names:
                    if possible_name in available_folders:
                        actual_folders[folder_type] = possible_name
                        break
        except Exception as e:
            logging.warning(f"Could not discover folder names: {e}")
    
    print("\nSelect Gmail folders/labels to process:")
    print("1. INBOX (Primary inbox)")
    print(f"2. All Mail (All emails including archived) - {actual_folders.get('all_mail', '[Gmail]/All Mail')}")
    print(f"3. Trash (Deleted emails) - {actual_folders.get('trash', '[Gmail]/Trash')}")
    print(f"4. Spam (Spam emails) - {actual_folders.get('spam', '[Gmail]/Spam')}")
    print(f"5. Sent Mail (Sent emails) - {actual_folders.get('sent', '[Gmail]/Sent Mail')}")
    print("6. List all available folders")
    print("7. Custom folder/label")
    print("8. Multiple folders")
    
    while True:
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == '1':
            return ['INBOX']
        elif choice == '2':
            folder_name = actual_folders.get('all_mail', '[Gmail]/All Mail')
            print(f"\n⚠ WARNING: Gmail All Mail Behavior")
            print(f"⚠ Deleting from All Mail only removes the 'All Mail' label.")
            print(f"⚠ Emails may still exist in INBOX, Sent, and other folders.")
            print(f"⚠ For complete deletion, consider processing individual folders.")
            print(f"⚠ Continue with All Mail? (y/n): ", end="")
            confirm = input().strip().lower()
            if confirm not in ['y', 'yes']:
                print("Returning to folder selection...")
                return get_folder_selection(imap_connection)
            return [folder_name]
        elif choice == '3':
            folder_name = actual_folders.get('trash', '[Gmail]/Trash')
            return [folder_name]
        elif choice == '4':
            folder_name = actual_folders.get('spam', '[Gmail]/Spam')
            return [folder_name]
        elif choice == '5':
            folder_name = actual_folders.get('sent', '[Gmail]/Sent Mail')
            return [folder_name]
        elif choice == '6':
            if imap_conn:
                try:
                    folders = imap_conn.list_folders()
                    print("\nAvailable folders:")
                    for i, folder in enumerate(folders, 1):
                        print(f"{i:2d}. {folder}")
                    
                    folder_choice = input("\nEnter folder number or name: ").strip()
                    try:
                        folder_index = int(folder_choice) - 1
                        if 0 <= folder_index < len(folders):
                            return [folders[folder_index]]
                        else:
                            print("Invalid folder number.")
                    except ValueError:
                        if folder_choice in folders:
                            return [folder_choice]
                        else:
                            print("Folder not found.")
                except Exception as e:
                    print(f"Error listing folders: {e}")
            else:
                print("Cannot list folders - no connection available yet.")
                print("Folders will be validated after connecting to Gmail.")
                print("Common Gmail folders you can try:")
                print("  - INBOX")
                print("  - [Gmail]/All Mail")
                print("  - [Gmail]/Bin (Trash)")
                print("  - [Gmail]/Spam")
                print("  - [Gmail]/Sent Mail")
                print("  - [Gmail]/Drafts")
                
                custom_folder = input("\nEnter folder name to try: ").strip()
                if custom_folder:
                    return [custom_folder]
                else:
                    print("No folder entered.")
        elif choice == '7':
            custom_folder = input("Enter custom folder/label name: ").strip()
            if custom_folder:
                return [custom_folder]
            else:
                print("Folder name cannot be empty.")
        elif choice == '8':
            folders = []
            print("\nSelect multiple folders (enter numbers separated by commas, e.g., 1,2,4):")
            print("Available options: 1=INBOX, 2=All Mail, 3=Trash, 4=Spam, 5=Sent Mail")
            
            selections = input("Enter selections: ").strip()
            try:
                folder_map = {
                    '1': 'INBOX',
                    '2': actual_folders.get('all_mail', '[Gmail]/All Mail'),
                    '3': actual_folders.get('trash', '[Gmail]/Trash'),
                    '4': actual_folders.get('spam', '[Gmail]/Spam'),
                    '5': actual_folders.get('sent', '[Gmail]/Sent Mail')
                }
                
                for sel in selections.split(','):
                    sel = sel.strip()
                    if sel in folder_map:
                        folders.append(folder_map[sel])
                    else:
                        print(f"Invalid selection: {sel}")
                
                if folders:
                    return folders
                else:
                    print("No valid folders selected.")
            except:
                print("Invalid input format.")
        else:
            print("Please enter a number between 1-8.")


def get_user_input():
    """
    Interactively get configuration from user with improved authentication guidance.
    
    Returns:
        dict: Configuration dictionary with user inputs, or None if cancelled
    """
    print("=" * 60)
    print("Gmail IMAP Cleaner - Configuration Setup")
    print("=" * 60)
    
    config = {}
    
    # Get email address
    while True:
        email = input("Enter your Gmail address: ").strip()
        if email and '@' in email and email.endswith(('@gmail.com', '@googlemail.com')):
            config['email'] = email
            break
        else:
            print("Please enter a valid Gmail address (must end with @gmail.com)")
    
    # Show authentication help
    show_auth_help = input("\nDo you need help setting up Gmail authentication? (y/n): ").lower().startswith('y')
    if show_auth_help:
        show_authentication_help()
        input("Press Enter to continue after setting up authentication...")
    
    # Get password securely with better guidance
    print("\nEnter your Gmail App Password (recommended) or regular password:")
    print("App Password: 16-character code from Google Account settings")
    print("Regular Password: Only works if 'Less Secure Apps' is enabled")
    
    while True:
        password = getpass.getpass("Password: ").strip()
        if password:
            config['password'] = password
            break
        else:
            print("Password cannot be empty.")
    
    # Get cutoff date
    while True:
        print(f"\nCurrent date: {datetime.datetime.now().strftime('%d-%b-%Y')}")
        cutoff_date = input("Enter cutoff date for old emails (DD-MMM-YYYY, e.g., 01-Jul-2023): ").strip()
        if validate_date_format(cutoff_date):
            config['cutoff_date'] = cutoff_date
            break
        else:
            print("Please enter date in DD-MMM-YYYY format (e.g., 01-Jul-2023).")
    
    # Get folder selection (will be refined after connection)
    config['folders'] = get_folder_selection()
    
    # Ask about operations to perform
    print("\nSelect operations to perform:")
    config['delete_old'] = input("Delete old emails? (y/n): ").lower().startswith('y')
    config['process_unsubscribe'] = input("Process unsubscribe emails? (y/n): ").lower().startswith('y')
    
    if config['delete_old']:
        config['dry_run'] = input("Perform dry run first (recommended)? (y/n): ").lower().startswith('y')
        config['fast_mode'] = input("Use fast deletion mode for large batches? (y/n): ").lower().startswith('y')
    else:
        config['dry_run'] = False
        config['fast_mode'] = False
    
    # Configuration summary
    print("\nConfiguration Summary:")
    print(f"Email: {config['email']}")
    print(f"Cutoff Date: {config['cutoff_date']}")
    print(f"Folders: {', '.join(config['folders'])}")
    print(f"Delete Old Emails: {'Yes' if config['delete_old'] else 'No'}")
    print(f"Process Unsubscribe: {'Yes' if config['process_unsubscribe'] else 'No'}")
    if config['delete_old']:
        print(f"Dry Run: {'Yes' if config['dry_run'] else 'No'}")
        print(f"Fast Mode: {'Yes' if config['fast_mode'] else 'No'}")
    
    confirm = input("\nProceed with these settings? (y/n): ").lower().startswith('y')
    if not confirm:
        print("Configuration cancelled.")
        return None
    
    return config


def refine_folder_selection(config, imap_conn):
    """
    Refine folder selection after IMAP connection is established.
    
    Args:
        config: Configuration dictionary
        imap_conn: IMAP connection object
        
    Returns:
        bool: True if folders are valid, False if user wants to change
    """
    # Try to validate current folder selection
    try:
        available_folders = imap_conn.list_folders()
        invalid_folders = []
        corrected_folders = []
        
        for folder in config['folders']:
            if folder in available_folders or folder == 'INBOX':
                corrected_folders.append(folder)
            else:
                # Try to find a match with Gmail folder variations
                found_match = False
                
                # Check for partial matches or common variations
                for available_folder in available_folders:
                    # Direct match
                    if folder.lower() == available_folder.lower():
                        corrected_folders.append(available_folder)
                        found_match = True
                        break
                    # Check if it's a Gmail folder variation
                    elif folder.lower() in ['bin', 'trash'] and 'bin' in available_folder.lower():
                        corrected_folders.append(available_folder)
                        found_match = True
                        break
                    elif folder.lower() in ['all mail', 'allmail'] and 'all mail' in available_folder.lower():
                        corrected_folders.append(available_folder)
                        found_match = True
                        break
                    elif folder.lower() == 'spam' and 'spam' in available_folder.lower():
                        corrected_folders.append(available_folder)
                        found_match = True
                        break
                    elif folder.lower() in ['sent', 'sent mail'] and 'sent' in available_folder.lower():
                        corrected_folders.append(available_folder)
                        found_match = True
                        break
                
                if not found_match:
                    invalid_folders.append(folder)
        
        if invalid_folders:
            print(f"\nWarning: The following folders were not found: {', '.join(invalid_folders)}")
            print("Available folders:")
            for i, folder in enumerate(available_folders, 1):
                print(f"{i:2d}. {folder}")
            
            change_selection = input("\nWould you like to change your folder selection? (y/n): ").lower().startswith('y')
            if change_selection:
                config['folders'] = get_folder_selection(imap_conn)
                return True
        else:
            # Update config with corrected folder names
            config['folders'] = corrected_folders
        
        return True
        
    except Exception as e:
        logging.warning(f"Could not validate folders: {e}")
        return True


def ask_continue_or_exit():
    """
    Ask user if they want to perform more operations or exit.
    
    Returns:
        str: 'continue', 'new_config', or 'exit'
    """
    print("\n" + "=" * 60)
    print("What would you like to do next?")
    print("=" * 60)
    print("1. Perform another operation with same settings")
    print("2. Change configuration and run again")
    print("3. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            return 'continue'
        elif choice == '2':
            return 'new_config'
        elif choice == '3':
            return 'exit'
        else:
            print("Please enter 1, 2, or 3.")


def handle_authentication_error():
    """
    Handle authentication errors with helpful guidance.
    
    Returns:
        bool: True if user wants to retry, False to exit
    """
    print("\n" + "!" * 70)
    print("AUTHENTICATION FAILED")
    print("!" * 70)
    print("The most common cause is using your regular Gmail password")
    print("instead of an App Password.")
    print()
    
    show_authentication_help()
    
    retry = input("\nWould you like to try again with different credentials? (y/n): ").lower().startswith('y')
    return retry


# Default configuration values
DEFAULT_CONFIG = {
    'imap_server': 'imap.gmail.com',
    'imap_port': 993,
    'request_delay': 1,
    'batch_size': 500,  # Increased for better performance
    'http_timeout': 10,
    'log_level': logging.INFO,
    'log_format': '%(asctime)s - %(levelname)s - %(message)s'
}