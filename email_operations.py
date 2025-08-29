#!/usr/bin/env python3
"""
Email Operations Module for Gmail IMAP Cleaner

Handles email search, deletion, and metadata extraction operations.
"""

import email
import datetime
import logging
import imaplib
from email.header import decode_header
from email.utils import parsedate_tz, mktime_tz


class EmailOperations:
    """
    Email operations handler for search, deletion, and metadata extraction.
    """
    
    def __init__(self, imap_connection):
        self.imap_connection = imap_connection
        self.operation_summary = {
            'emails_deleted': 0,
            'unsubscribe_emails_found': 0,
            'unsubscribe_links_processed': 0,
            'successful_unsubscribes': 0,
            'failed_unsubscribes': 0
        }
    
    def parse_email_date(self, date_string):
        """Parse email date string from IMAP format to datetime object."""
        if not date_string:
            return None
        
        try:
            parsed_date = parsedate_tz(date_string)
            if parsed_date:
                timestamp = mktime_tz(parsed_date)
                return datetime.datetime.fromtimestamp(timestamp)
            else:
                logging.warning(f"Could not parse date string: {date_string}")
                return None
        except Exception as e:
            logging.warning(f"Error parsing date '{date_string}': {e}")
            return None
    
    def parse_cutoff_date(self, cutoff_date_str):
        """Parse the cutoff date string from configuration format to datetime object."""
        try:
            return datetime.datetime.strptime(cutoff_date_str, "%d-%b-%Y")
        except ValueError as e:
            logging.error(f"Invalid cutoff date format '{cutoff_date_str}': {e}")
            return None
    
    def format_date_for_imap_search(self, date_obj):
        """Format datetime object for IMAP BEFORE search command."""
        if date_obj is None:
            return None
        return date_obj.strftime("%d-%b-%Y")
    
    def search_old_emails(self, cutoff_date_str, folder_name=None):
        """Search for emails older than the cutoff date using IMAP BEFORE command."""
        connection = self.imap_connection.get_connection()
        if not connection:
            logging.error("No active IMAP connection for email search")
            return []
        
        # Select folder if specified
        if folder_name:
            if not self.imap_connection.select_folder(folder_name):
                logging.error(f"Failed to select folder: {folder_name}")
                return []
        
        try:
            cutoff_date = self.parse_cutoff_date(cutoff_date_str)
            if cutoff_date is None:
                logging.error("Failed to parse cutoff date for search")
                return []
            
            search_date = self.format_date_for_imap_search(cutoff_date)
            current_folder = folder_name or "current folder"
            logging.info(f"Searching for emails before {search_date} in {current_folder}")
            
            search_criteria = f'BEFORE {search_date}'
            result, email_ids = connection.search(None, search_criteria)
            
            if result != 'OK':
                logging.error(f"IMAP search failed: {email_ids}")
                return []
            
            if email_ids[0]:
                id_list = email_ids[0].split()
                logging.info(f"Found {len(id_list)} emails older than {cutoff_date_str} in {current_folder}")
                return [id.decode() for id in id_list]
            else:
                logging.info(f"No emails found older than {cutoff_date_str} in {current_folder}")
                return []
                
        except imaplib.IMAP4.error as e:
            logging.error(f"IMAP error during email search: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error during email search: {e}")
            return []
    
    def search_old_emails_multiple_folders(self, cutoff_date_str, folders):
        """Search for old emails across multiple folders."""
        all_email_ids = []
        folder_results = {}
        
        for folder in folders:
            logging.info(f"Processing folder: {folder}")
            folder_ids = self.search_old_emails(cutoff_date_str, folder)
            folder_results[folder] = len(folder_ids)
            all_email_ids.extend([(email_id, folder) for email_id in folder_ids])
        
        # Log summary
        logging.info("=" * 50)
        logging.info("FOLDER SEARCH SUMMARY")
        logging.info("=" * 50)
        for folder, count in folder_results.items():
            logging.info(f"{folder}: {count} emails")
        logging.info(f"Total emails found: {len(all_email_ids)}")
        logging.info("=" * 50)
        
        return all_email_ids
    
    def get_email_metadata(self, email_id):
        """Extract metadata (subject, sender, date) from an email."""
        connection = self.imap_connection.get_connection()
        if not connection:
            logging.error("No active IMAP connection for metadata extraction")
            return None
        
        try:
            result, email_data = connection.fetch(email_id, '(RFC822.HEADER)')
            
            if result != 'OK':
                logging.warning(f"Failed to fetch email {email_id}: {email_data}")
                return None
            
            email_message = email.message_from_bytes(email_data[0][1])
            
            # Extract subject
            subject = email_message.get('Subject', 'No Subject')
            if subject:
                decoded_subject = decode_header(subject)
                subject = ''.join([
                    part[0].decode(part[1] or 'utf-8') if isinstance(part[0], bytes) else part[0]
                    for part in decoded_subject
                ])
            
            # Extract sender
            sender = email_message.get('From', 'Unknown Sender')
            
            # Extract and parse date
            date_str = email_message.get('Date', '')
            email_date = self.parse_email_date(date_str)
            
            return {
                'id': email_id,
                'subject': subject[:100] + '...' if len(subject) > 100 else subject,
                'from': sender,
                'date': email_date,
                'date_str': date_str
            }
            
        except Exception as e:
            logging.warning(f"Error extracting metadata for email {email_id}: {e}")
            return None
    
    def delete_email(self, email_id):
        """Delete a single email by marking it for deletion."""
        connection = self.imap_connection.get_connection()
        if not connection:
            logging.error("No active IMAP connection for email deletion")
            return False
        
        try:
            result = connection.store(email_id, '+FLAGS', '\\Deleted')
            
            if result[0] != 'OK':
                logging.error(f"Failed to mark email {email_id} for deletion: {result[1]}")
                return False
            
            logging.debug(f"Email {email_id} marked for deletion")
            return True
            
        except imaplib.IMAP4.error as e:
            logging.error(f"IMAP error deleting email {email_id}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error deleting email {email_id}: {e}")
            return False
    
    def expunge_deleted_emails(self):
        """Permanently remove emails marked for deletion from the server."""
        connection = self.imap_connection.get_connection()
        if not connection:
            logging.error("No active IMAP connection for expunge operation")
            return False
        
        try:
            logging.info("Expunging deleted emails from server...")
            result = connection.expunge()
            
            if result[0] == 'OK':
                expunged_count = len([r for r in result[1] if r is not None])
                logging.info(f"Successfully expunged {expunged_count} emails from server")
                return True
            else:
                logging.error(f"Expunge operation failed: {result[1]}")
                return False
                
        except imaplib.IMAP4.error as e:
            logging.error(f"IMAP error during expunge: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during expunge: {e}")
            return False
    
    def delete_emails_bulk(self, email_ids):
        """Delete multiple emails efficiently using bulk operations."""
        connection = self.imap_connection.get_connection()
        if not connection:
            logging.error("No active IMAP connection for bulk email deletion")
            return 0
        
        if not email_ids:
            return 0
        
        try:
            # Convert email IDs to comma-separated string for bulk operation
            id_string = ','.join(email_ids)
            
            # Mark all emails for deletion in one command
            result = connection.store(id_string, '+FLAGS', '\\Deleted')
            
            if result[0] == 'OK':
                logging.info(f"✓ Successfully marked {len(email_ids)} emails for deletion")
                return len(email_ids)
            else:
                logging.error(f"Failed to mark emails for deletion: {result[1]}")
                return 0
                
        except imaplib.IMAP4.error as e:
            logging.error(f"IMAP error during bulk deletion: {e}")
            return 0
        except Exception as e:
            logging.error(f"Unexpected error during bulk deletion: {e}")
            return 0
    
    def delete_old_emails_with_logging(self, cutoff_date_str, folders, batch_size=500):
        """Optimized workflow to find, delete, and log old emails across multiple folders."""
        logging.info("=" * 50)
        logging.info("STARTING OLD EMAIL DELETION PROCESS")
        logging.info("=" * 50)
        
        if len(folders) == 1:
            # Single folder processing
            old_email_ids = self.search_old_emails(cutoff_date_str, folders[0])
            email_folder_pairs = [(email_id, folders[0]) for email_id in old_email_ids]
        else:
            # Multiple folder processing
            email_folder_pairs = self.search_old_emails_multiple_folders(cutoff_date_str, folders)
        
        if not email_folder_pairs:
            logging.info("No old emails found to delete")
            return 0
        
        logging.info(f"Found {len(email_folder_pairs)} emails to delete across {len(folders)} folder(s)")
        
        # Group emails by folder for efficient processing
        folder_groups = {}
        for email_id, folder in email_folder_pairs:
            if folder not in folder_groups:
                folder_groups[folder] = []
            folder_groups[folder].append(email_id)
        
        total_deleted = 0
        
        # Process each folder separately
        for folder, email_ids in folder_groups.items():
            logging.info(f"\nProcessing folder: {folder} ({len(email_ids)} emails)")
            
            # Select the folder
            if not self.imap_connection.select_folder(folder):
                logging.error(f"Failed to select folder {folder}, skipping...")
                continue
            
            # Show sample of emails that will be deleted (first 3 per folder)
            if len(email_ids) <= 6:
                logging.info(f"Emails to be deleted from {folder}:")
                for email_id in email_ids[:3]:
                    metadata = self.get_email_metadata(email_id)
                    if metadata:
                        logging.info(f"  - '{metadata['subject'][:60]}...' from {metadata['from']}")
            else:
                logging.info(f"Sample emails to be deleted from {folder}:")
                for email_id in email_ids[:3]:
                    metadata = self.get_email_metadata(email_id)
                    if metadata:
                        logging.info(f"  - '{metadata['subject'][:60]}...' from {metadata['from']}")
                logging.info(f"  ... and {len(email_ids) - 3} more emails")
            
            # Special handling for Gmail All Mail folder
            if self.is_gmail_all_mail_folder(folder):
                logging.warning(f"⚠ Gmail All Mail detected!")
                logging.warning(f"⚠ Auto-switching to True Gmail Deletion for permanent removal!")
                logging.info(f"This will delete emails from their source folders instead of just removing labels...")
                
                # Use true Gmail deletion for All Mail
                folder_deleted = self.delete_old_emails_true_gmail(cutoff_date_str)
                
                if folder_deleted > 0:
                    logging.info(f"✓ {folder_deleted} emails permanently deleted via True Gmail Deletion")
                else:
                    logging.error(f"Failed to delete emails via True Gmail Deletion")
            else:
                # Standard deletion for non-All Mail folders
                # Process emails in batches
                folder_deleted = 0
                total_batches = (len(email_ids) + batch_size - 1) // batch_size
                
                for i in range(0, len(email_ids), batch_size):
                    batch = email_ids[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    logging.info(f"Processing {folder} batch {batch_num}/{total_batches} ({len(batch)} emails)...")
                    
                    # Use bulk deletion for efficiency
                    batch_deleted = self.delete_emails_bulk(batch)
                    folder_deleted += batch_deleted
                    
                    if batch_deleted != len(batch):
                        logging.warning(f"Only {batch_deleted}/{len(batch)} emails deleted in batch {batch_num}")
                
                # Expunge deleted emails for this folder
                if folder_deleted > 0:
                    logging.info(f"Expunging {folder_deleted} deleted emails from {folder}...")
                    if self.expunge_deleted_emails():
                        logging.info(f"✓ {folder_deleted} emails permanently removed from {folder}")
                    else:
                        logging.warning(f"⚠ Some emails in {folder} may not have been permanently removed")
            
            total_deleted += folder_deleted
            logging.info(f"Completed {folder}: {folder_deleted}/{len(email_ids)} emails deleted")
        
        # Update operation summary
        self.operation_summary['emails_deleted'] = total_deleted
        
        logging.info("=" * 50)
        logging.info(f"OLD EMAIL DELETION COMPLETED: {total_deleted}/{len(email_folder_pairs)} emails deleted")
        logging.info("=" * 50)
        
        return total_deleted
    
    def is_gmail_all_mail_folder(self, folder_name):
        """Check if the folder is Gmail's All Mail folder."""
        gmail_all_mail_variations = [
            '[Gmail]/All Mail',
            '[Google Mail]/All Mail', 
            '"[Gmail]/All Mail"',
            '"[Google Mail]/All Mail"',
            'All Mail'
        ]
        return folder_name in gmail_all_mail_variations
    
    def handle_gmail_all_mail_deletion(self, email_ids):
        """
        Handle Gmail All Mail deletion by adding Gmail-specific labels.
        Gmail All Mail doesn't actually delete emails - it just removes the All Mail label.
        To truly delete, we need to add the \\Deleted flag AND remove from All Mail.
        """
        connection = self.imap_connection.get_connection()
        if not connection:
            logging.error("No active IMAP connection for Gmail All Mail deletion")
            return 0
        
        if not email_ids:
            return 0
        
        try:
            # Convert email IDs to comma-separated string
            id_string = ','.join(email_ids)
            
            # For Gmail All Mail, we need to:
            # 1. Add the \Deleted flag
            # 2. Remove the \All label (this is what makes it disappear from All Mail)
            
            # First, mark emails as deleted
            delete_result = connection.store(id_string, '+FLAGS', '\\Deleted')
            if delete_result[0] != 'OK':
                logging.error(f"Failed to mark emails for deletion: {delete_result[1]}")
                return 0
            
            # Try to remove the \All label (Gmail-specific)
            try:
                # Remove the \All label which is what keeps emails in All Mail
                all_result = connection.store(id_string, '-X-GM-LABELS', '\\All')
                if all_result[0] == 'OK':
                    logging.info(f"✓ Removed \\All label from {len(email_ids)} emails")
                else:
                    logging.warning(f"Could not remove \\All label: {all_result[1]}")
            except imaplib.IMAP4.error:
                # Gmail X-GM-LABELS extension might not be available
                logging.info("Gmail label extension not available, using standard deletion")
            
            # Expunge to apply changes
            expunge_result = connection.expunge()
            if expunge_result[0] == 'OK':
                expunged_count = len([r for r in expunge_result[1] if r is not None])
                logging.info(f"✓ Successfully processed {len(email_ids)} emails from All Mail")
                return len(email_ids)
            else:
                logging.error(f"Failed to expunge emails: {expunge_result[1]}")
                return 0
                
        except imaplib.IMAP4.error as e:
            logging.error(f"IMAP error handling Gmail All Mail deletion: {e}")
            return 0
        except Exception as e:
            logging.error(f"Unexpected error handling Gmail All Mail deletion: {e}")
            return 0
    
    def get_folder_email_count(self, folder_name):
        """Get the number of emails in a specific folder using fast STATUS command."""
        try:
            connection = self.imap_connection.get_connection()
            if not connection:
                return 0
            
            # Try fast STATUS command first (doesn't require selecting folder)
            try:
                result, data = connection.status(folder_name, '(MESSAGES)')
                if result == 'OK' and data:
                    # Parse response like: b'[Gmail]/All Mail (MESSAGES 11481)'
                    status_line = data[0].decode() if isinstance(data[0], bytes) else data[0]
                    # Extract number from parentheses
                    import re
                    match = re.search(r'MESSAGES (\d+)', status_line)
                    if match:
                        return int(match.group(1))
            except Exception as e:
                logging.debug(f"STATUS command failed for {folder_name}: {e}")
            
            # Fallback to SELECT method (slower but more reliable)
            if self.imap_connection.select_folder(folder_name):
                # Get count from SELECT response which is already available
                # The select_folder method logs "Total emails: X" - we can use that
                # But for now, let's use a quick search
                result, email_ids = connection.search(None, 'ALL')
                if result == 'OK' and email_ids[0]:
                    return len(email_ids[0].split())
            
            return 0
            
        except Exception as e:
            logging.debug(f"Error getting email count for {folder_name}: {e}")
            return 0
    
    def get_folders_with_counts(self, folders, timeout_per_folder=5):
        """Get folder names with their email counts with timeout protection."""
        import time
        folder_counts = {}
        
        for folder in folders:
            start_time = time.time()
            try:
                count = self.get_folder_email_count(folder)
                folder_counts[folder] = count
                elapsed = time.time() - start_time
                logging.debug(f"Folder {folder}: {count} emails ({elapsed:.1f}s)")
                
                # Skip remaining folders if this one took too long
                if elapsed > timeout_per_folder:
                    logging.warning(f"Folder counting is slow, skipping remaining folders")
                    # Set remaining folders to "?" or -1 to indicate unknown
                    remaining_folders = folders[folders.index(folder) + 1:]
                    for remaining in remaining_folders:
                        folder_counts[remaining] = -1
                    break
                    
            except Exception as e:
                logging.debug(f"Error counting emails in {folder}: {e}")
                folder_counts[folder] = -1  # Indicate error
        
        return folder_counts
    
    def get_gmail_source_folders(self):
        """Get list of Gmail folders where emails actually live (not All Mail)."""
        try:
            all_folders = self.imap_connection.list_folders()
            
            # Filter out All Mail and system folders, keep actual email folders
            source_folders = []
            
            # Always include INBOX
            if 'INBOX' in all_folders:
                source_folders.append('INBOX')
            
            # Include other Gmail folders where emails actually live
            gmail_source_patterns = [
                '[Gmail]/Sent Mail',
                '[Google Mail]/Sent Mail', 
                '[Gmail]/Drafts',
                '[Google Mail]/Drafts',
                '[Gmail]/Spam',
                '[Google Mail]/Spam'
            ]
            
            for pattern in gmail_source_patterns:
                if pattern in all_folders:
                    source_folders.append(pattern)
            
            # Include custom labels/folders (non-Gmail system folders)
            for folder in all_folders:
                if (not folder.startswith('[Gmail]') and 
                    not folder.startswith('[Google Mail]') and 
                    folder != 'INBOX' and
                    folder not in source_folders):
                    source_folders.append(folder)
            
            logging.info(f"Identified {len(source_folders)} source folders: {source_folders}")
            return source_folders
            
        except Exception as e:
            logging.error(f"Error getting Gmail source folders: {e}")
            return ['INBOX']  # Fallback to INBOX only
    
    def delete_old_emails_true_gmail(self, cutoff_date_str):
        """
        True Gmail deletion: Delete from source folders (INBOX, Sent, etc.) 
        instead of All Mail to achieve permanent deletion.
        """
        logging.info("=" * 60)
        logging.info("STARTING TRUE GMAIL DELETION")
        logging.info("This will delete emails from their source folders for permanent removal")
        logging.info("=" * 60)
        
        # Get Gmail source folders automatically
        source_folders = self.get_gmail_source_folders()
        
        # Search across all source folders
        logging.info(f"Scanning {len(source_folders)} source folders for old emails...")
        email_folder_pairs = self.search_old_emails_multiple_folders(cutoff_date_str, source_folders)
        
        if not email_folder_pairs:
            logging.info("No old emails found in source folders")
            return 0
        
        logging.info(f"Found {len(email_folder_pairs)} emails to permanently delete")
        
        # Group by folder and process
        folder_groups = {}
        for email_id, folder in email_folder_pairs:
            if folder not in folder_groups:
                folder_groups[folder] = []
            folder_groups[folder].append(email_id)
        
        total_deleted = 0
        
        # Process each source folder
        for folder, email_ids in folder_groups.items():
            logging.info(f"Permanently deleting {len(email_ids)} emails from {folder}...")
            
            # Select the folder
            if not self.imap_connection.select_folder(folder):
                logging.error(f"Failed to select folder {folder}, skipping...")
                continue
            
            # Delete emails (standard deletion works for source folders)
            deleted_count = self.delete_emails_bulk(email_ids)
            
            if deleted_count > 0:
                logging.info(f"Expunging {deleted_count} emails from {folder}...")
                if self.expunge_deleted_emails():
                    logging.info(f"✓ {folder}: {deleted_count} emails permanently deleted")
                else:
                    logging.warning(f"⚠ Expunge may have failed for {folder}")
            
            total_deleted += deleted_count
        
        self.operation_summary['emails_deleted'] = total_deleted
        
        logging.info("=" * 60)
        logging.info(f"TRUE GMAIL DELETION COMPLETED")
        logging.info(f"Permanently deleted {total_deleted} emails from {len(folder_groups)} source folders")
        logging.info(f"These emails will now disappear from All Mail as well")
        logging.info("=" * 60)
        
        return total_deleted
    
    def delete_old_emails_fast(self, cutoff_date_str, folders):
        """Ultra-fast email deletion with minimal logging across multiple folders."""
        logging.info("Starting fast email deletion...")
        
        # Check if user is trying to delete from All Mail only
        if len(folders) == 1 and self.is_gmail_all_mail_folder(folders[0]):
            logging.warning("=" * 60)
            logging.warning("GMAIL ALL MAIL DELETION DETECTED")
            logging.warning("=" * 60)
            logging.warning("⚠ You selected Gmail's All Mail folder.")
            logging.warning("⚠ To actually delete emails, we'll delete from their source folders instead.")
            logging.warning("💡 Auto-switching to True Gmail Deletion for permanent removal!")
            logging.warning("=" * 60)
            
            # Automatically use true deletion for All Mail
            return self.delete_old_emails_true_gmail(cutoff_date_str)
        
        if len(folders) == 1:
            # Single folder processing
            old_email_ids = self.search_old_emails(cutoff_date_str, folders[0])
            email_folder_pairs = [(email_id, folders[0]) for email_id in old_email_ids]
        else:
            # Multiple folder processing
            email_folder_pairs = self.search_old_emails_multiple_folders(cutoff_date_str, folders)
        
        if not email_folder_pairs:
            logging.info("No old emails found to delete")
            return 0
        
        logging.info(f"Deleting {len(email_folder_pairs)} emails in bulk across {len(folders)} folder(s)...")
        
        # Group emails by folder
        folder_groups = {}
        for email_id, folder in email_folder_pairs:
            if folder not in folder_groups:
                folder_groups[folder] = []
            folder_groups[folder].append(email_id)
        
        total_deleted = 0
        
        # Process each folder
        for folder, email_ids in folder_groups.items():
            logging.info(f"Fast deleting {len(email_ids)} emails from {folder}...")
            
            # Select the folder
            if not self.imap_connection.select_folder(folder):
                logging.error(f"Failed to select folder {folder}, skipping...")
                continue
            
            # Special handling for Gmail All Mail folder
            if self.is_gmail_all_mail_folder(folder):
                logging.warning(f"⚠ Gmail All Mail detected!")
                logging.warning(f"⚠ Note: Gmail's All Mail folder has special behavior.")
                logging.warning(f"⚠ Deleting from All Mail only removes the 'All Mail' label.")
                logging.warning(f"⚠ Emails may still exist in their original folders (INBOX, Sent, etc.)")
                logging.info(f"Attempting Gmail All Mail deletion for {len(email_ids)} emails...")
                
                deleted_count = self.handle_gmail_all_mail_deletion(email_ids)
                total_deleted += deleted_count
                
                if deleted_count > 0:
                    logging.info(f"✓ {folder}: {deleted_count} emails processed")
                    logging.info(f"💡 Tip: For complete deletion, consider processing INBOX, Sent, and other folders directly")
                else:
                    logging.error(f"Failed to process emails in {folder}")
            else:
                # Standard deletion for non-All Mail folders
                deleted_count = self.delete_emails_bulk(email_ids)
                
                if deleted_count > 0:
                    logging.info(f"Expunging {deleted_count} emails from {folder}...")
                    self.expunge_deleted_emails()
                
                total_deleted += deleted_count
                logging.info(f"✓ {folder}: {deleted_count} emails deleted")
        
        self.operation_summary['emails_deleted'] = total_deleted
        logging.info(f"Fast deletion completed: {total_deleted} emails deleted across all folders")
        
        return total_deleted
    
    def search_unsubscribe_emails(self):
        """Search for emails containing 'unsubscribe' in subject or body."""
        connection = self.imap_connection.get_connection()
        if not connection:
            logging.error("No active IMAP connection for unsubscribe email search")
            return []
        
        try:
            logging.info("Searching for emails containing 'unsubscribe'...")
            
            # Search for "unsubscribe" in subject
            result1, subject_ids = connection.search(None, 'SUBJECT', 'unsubscribe')
            
            # Search for "unsubscribe" in body text
            result2, body_ids = connection.search(None, 'BODY', 'unsubscribe')
            
            if result1 != 'OK' or result2 != 'OK':
                logging.error("Failed to search for unsubscribe emails")
                return []
            
            # Combine and deduplicate results
            all_ids = set()
            
            if subject_ids[0]:
                subject_list = subject_ids[0].split()
                all_ids.update(id.decode() for id in subject_list)
                logging.info(f"Found {len(subject_list)} emails with 'unsubscribe' in subject")
            
            if body_ids[0]:
                body_list = body_ids[0].split()
                all_ids.update(id.decode() for id in body_list)
                logging.info(f"Found {len(body_list)} emails with 'unsubscribe' in body")
            
            unique_ids = list(all_ids)
            logging.info(f"Total unique unsubscribe emails found: {len(unique_ids)}")
            
            return unique_ids
            
        except imaplib.IMAP4.error as e:
            logging.error(f"IMAP error searching for unsubscribe emails: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error searching for unsubscribe emails: {e}")
            return []
    
    def get_email_content(self, email_id):
        """Extract the full content of an email for link processing."""
        connection = self.imap_connection.get_connection()
        if not connection:
            logging.error("No active IMAP connection for content extraction")
            return ""
        
        try:
            result, email_data = connection.fetch(email_id, '(RFC822)')
            
            if result != 'OK':
                logging.warning(f"Failed to fetch email content for {email_id}")
                return ""
            
            email_message = email.message_from_bytes(email_data[0][1])
            
            content = ""
            
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    if content_type in ['text/plain', 'text/html']:
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                content += payload.decode('utf-8', errors='ignore') + "\n"
                        except Exception as e:
                            logging.debug(f"Error decoding email part: {e}")
            else:
                try:
                    payload = email_message.get_payload(decode=True)
                    if payload:
                        content = payload.decode('utf-8', errors='ignore')
                except Exception as e:
                    logging.debug(f"Error decoding email content: {e}")
            
            return content
            
        except Exception as e:
            logging.warning(f"Error extracting content for email {email_id}: {e}")
            return ""