#!/usr/bin/env python3
"""
IMAP Connection Management Module for Gmail IMAP Cleaner

Handles Gmail IMAP connection, authentication, and session management.
"""

import imaplib
import ssl
import logging


class GmailIMAPConnection:
    """
    Gmail IMAP connection manager with automatic reconnection and error handling.
    """
    
    def __init__(self, email, password, server='imap.gmail.com', port=993):
        self.email = email
        self.password = password
        self.server = server
        self.port = port
        self.connection = None
    
    def connect(self):
        """
        Establish SSL IMAP connection to Gmail and authenticate.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logging.info(f"Connecting to Gmail IMAP server: {self.server}:{self.port}")
            
            # Create SSL context for secure connection
            ssl_context = ssl.create_default_context()
            
            # Establish IMAP SSL connection
            self.connection = imaplib.IMAP4_SSL(self.server, self.port, ssl_context=ssl_context)
            
            logging.info("SSL connection established successfully")
            
            # Authenticate with Gmail
            logging.info(f"Authenticating with email: {self.email}")
            result = self.connection.login(self.email, self.password)
            
            if result[0] == 'OK':
                logging.info("Authentication successful")
                
                # Initially select INBOX (will be changed later based on user selection)
                result = self.connection.select('INBOX')
                if result[0] == 'OK':
                    email_count = int(result[1][0])
                    logging.info(f"INBOX selected successfully. Total emails: {email_count}")
                    return True
                else:
                    logging.error(f"Failed to select INBOX: {result[1]}")
                    return False
            else:
                logging.error(f"Authentication failed: {result[1]}")
                return False
                
        except imaplib.IMAP4.error as e:
            logging.error(f"IMAP error during connection: {e}")
            return False
        except ssl.SSLError as e:
            logging.error(f"SSL error during connection: {e}")
            logging.error("This might indicate an issue with SSL/TLS configuration")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during connection: {e}")
            return False
    
    def disconnect(self):
        """
        Clean disconnection from Gmail IMAP server.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        if self.connection is None:
            logging.info("No active IMAP connection to disconnect")
            return True
        
        try:
            logging.info("Disconnecting from Gmail IMAP server")
            
            # Close the selected mailbox
            try:
                self.connection.close()
                logging.info("Mailbox closed successfully")
            except imaplib.IMAP4.error as e:
                logging.warning(f"Error closing mailbox (continuing with logout): {e}")
            
            # Logout from the server
            self.connection.logout()
            logging.info("Logged out from Gmail IMAP server successfully")
            
            self.connection = None
            return True
            
        except imaplib.IMAP4.error as e:
            logging.error(f"IMAP error during disconnection: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during disconnection: {e}")
            return False
    
    def ensure_connection(self):
        """
        Ensure that we have an active IMAP connection, reconnect if necessary.
        
        Returns:
            bool: True if connection is active, False otherwise
        """
        if self.connection is None:
            logging.info("No active connection, attempting to connect")
            return self.connect()
        
        try:
            # Test the connection with a simple NOOP command
            result = self.connection.noop()
            if result[0] == 'OK':
                return True
            else:
                logging.warning("Connection test failed, attempting to reconnect")
                self.disconnect()
                return self.connect()
        except Exception as e:
            logging.warning(f"Connection test error, attempting to reconnect: {e}")
            self.disconnect()
            return self.connect()
    
    def get_connection(self):
        """
        Get the active IMAP connection object.
        
        Returns:
            imaplib.IMAP4_SSL: Active connection object, or None if not connected
        """
        if self.ensure_connection():
            return self.connection
        return None
    
    def __enter__(self):
        """Context manager entry."""
        if self.connect():
            return self
        else:
            raise ConnectionError("Failed to establish IMAP connection")
    
    def select_folder(self, folder_name):
        """
        Select a specific Gmail folder/label with fallback options.
        
        Args:
            folder_name (str): Name of the folder to select
            
        Returns:
            bool: True if folder selection successful, False otherwise
        """
        if not self.ensure_connection():
            return False
        
        # Try the exact folder name first
        try:
            result = self.connection.select(folder_name)
            if result[0] == 'OK':
                email_count = int(result[1][0])
                logging.info(f"Selected folder '{folder_name}' successfully. Total emails: {email_count}")
                return True
        except Exception as e:
            logging.debug(f"Failed to select '{folder_name}': {e}")
        
        # If exact name fails, try common variations for Gmail folders
        folder_variations = {
            '[Gmail]/All Mail': ['[Google Mail]/All Mail', '"[Gmail]/All Mail"', 'All Mail'],
            '[Gmail]/Trash': ['[Google Mail]/Bin', '[Gmail]/Bin', '"[Gmail]/Trash"', 'Trash'],
            '[Gmail]/Spam': ['[Google Mail]/Spam', '"[Gmail]/Spam"', 'Spam'],
            '[Gmail]/Sent Mail': ['[Google Mail]/Sent Mail', '"[Gmail]/Sent Mail"', 'Sent'],
            '[Gmail]/Drafts': ['[Google Mail]/Drafts', '"[Gmail]/Drafts"', 'Drafts']
        }
        
        variations_to_try = folder_variations.get(folder_name, [])
        
        for variation in variations_to_try:
            try:
                result = self.connection.select(variation)
                if result[0] == 'OK':
                    email_count = int(result[1][0])
                    logging.info(f"Selected folder '{variation}' (requested: '{folder_name}') successfully. Total emails: {email_count}")
                    return True
            except Exception as e:
                logging.debug(f"Failed to select variation '{variation}': {e}")
        
        logging.error(f"Failed to select folder '{folder_name}' and all variations")
        return False
    
    def list_folders(self):
        """
        List all available folders/labels in the Gmail account.
        
        Returns:
            list: List of folder names, or empty list if failed
        """
        if not self.ensure_connection():
            return []
        
        try:
            result, folders = self.connection.list()
            if result == 'OK':
                folder_list = []
                for folder in folders:
                    # Parse folder name from IMAP response
                    folder_str = folder.decode('utf-8')
                    
                    # Gmail IMAP LIST response format: (flags) "delimiter" "folder_name"
                    # Example: (\HasNoChildren) "/" "INBOX"
                    # Example: (\HasNoChildren \All) "/" "[Gmail]/All Mail"
                    
                    # Find the last quoted string which is the folder name
                    import re
                    matches = re.findall(r'"([^"]*)"', folder_str)
                    if matches:
                        folder_name = matches[-1]  # Last quoted string is the folder name
                        folder_list.append(folder_name)
                    else:
                        # Fallback: try to extract folder name without quotes
                        parts = folder_str.split()
                        if len(parts) >= 3:
                            folder_name = parts[-1]
                            folder_list.append(folder_name)
                
                # Sort folders with INBOX first, then Gmail folders, then others
                def sort_key(folder):
                    if folder == 'INBOX':
                        return (0, folder)
                    elif folder.startswith('[Gmail]') or folder.startswith('[Google Mail]'):
                        return (1, folder)
                    else:
                        return (2, folder)
                
                folder_list.sort(key=sort_key)
                return folder_list
            else:
                logging.error(f"Failed to list folders: {folders}")
                return []
        except Exception as e:
            logging.error(f"Error listing folders: {e}")
            return []
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()