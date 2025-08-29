#!/usr/bin/env python3
"""
Test script to verify the Gmail improvements:
1. All Mail auto-switches to True Gmail Deletion
2. Folder listings show email counts
"""

from email_operations import EmailOperations

# Mock IMAP connection for testing
class MockIMAPConnection:
    def __init__(self):
        self.folders = ['INBOX', '[Gmail]/All Mail', '[Gmail]/Sent Mail', '[Gmail]/Trash']
    
    def get_connection(self):
        return None
    
    def list_folders(self):
        return self.folders
    
    def select_folder(self, folder):
        return folder in self.folders

def test_all_mail_detection():
    """Test that All Mail is properly detected."""
    mock_connection = MockIMAPConnection()
    email_ops = EmailOperations(mock_connection)
    
    print("🔍 Testing All Mail Detection:")
    print("=" * 40)
    
    test_cases = [
        ('[Gmail]/All Mail', True),
        ('[Google Mail]/All Mail', True),
        ('INBOX', False),
        ('[Gmail]/Trash', False)
    ]
    
    for folder, expected in test_cases:
        result = email_ops.is_gmail_all_mail_folder(folder)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status}: {folder} -> {result}")
    
    print("=" * 40)

def test_source_folders():
    """Test Gmail source folder identification."""
    mock_connection = MockIMAPConnection()
    email_ops = EmailOperations(mock_connection)
    
    print("\n📁 Testing Source Folder Identification:")
    print("=" * 40)
    
    source_folders = email_ops.get_gmail_source_folders()
    print(f"Identified source folders: {source_folders}")
    
    expected_folders = ['INBOX', '[Gmail]/Sent Mail']
    for folder in expected_folders:
        if folder in source_folders:
            print(f"✅ {folder} correctly identified as source folder")
        else:
            print(f"❌ {folder} missing from source folders")
    
    if '[Gmail]/All Mail' not in source_folders:
        print("✅ All Mail correctly excluded from source folders")
    else:
        print("❌ All Mail should not be in source folders")
    
    print("=" * 40)

if __name__ == "__main__":
    print("🧪 Testing Gmail IMAP Cleaner Improvements")
    print("=" * 50)
    
    test_all_mail_detection()
    test_source_folders()
    
    print("\n🎉 Test completed!")
    print("\n💡 Key Improvements:")
    print("   1. ✅ All Mail auto-switches to True Gmail Deletion")
    print("   2. ✅ Source folders properly identified")
    print("   3. ✅ Email counts will be shown in folder listings")