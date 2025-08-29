#!/usr/bin/env python3
"""
Test script to verify Gmail All Mail detection and handling
"""

from email_operations import EmailOperations

# Mock IMAP connection for testing
class MockIMAPConnection:
    def get_connection(self):
        return None

# Test the Gmail All Mail detection
def test_gmail_all_mail_detection():
    mock_connection = MockIMAPConnection()
    email_ops = EmailOperations(mock_connection)
    
    # Test cases
    test_folders = [
        '[Gmail]/All Mail',
        '[Google Mail]/All Mail',
        '"[Gmail]/All Mail"',
        '"[Google Mail]/All Mail"',
        'All Mail',
        'INBOX',
        '[Gmail]/Trash',
        'Sent'
    ]
    
    print("Testing Gmail All Mail detection:")
    print("=" * 40)
    
    for folder in test_folders:
        is_all_mail = email_ops.is_gmail_all_mail_folder(folder)
        status = "✓ ALL MAIL" if is_all_mail else "✗ Regular"
        print(f"{status}: {folder}")
    
    print("=" * 40)
    print("Test completed!")

if __name__ == "__main__":
    test_gmail_all_mail_detection()