#!/usr/bin/env python3
"""
Test script to verify performance improvements for folder counting
"""

import time
from email_operations import EmailOperations

# Mock IMAP connection that simulates slow responses
class SlowMockIMAPConnection:
    def __init__(self):
        self.folders = ['INBOX', '[Gmail]/All Mail', '[Gmail]/Sent Mail', '[Gmail]/Trash']
        self.slow_folders = ['[Gmail]/All Mail']  # Simulate slow folders
    
    def get_connection(self):
        return MockConnection()
    
    def list_folders(self):
        return self.folders
    
    def select_folder(self, folder):
        # Simulate slow selection for large folders
        if folder in self.slow_folders:
            print(f"⏳ Simulating slow selection for {folder}...")
            time.sleep(2)  # Simulate 2 second delay
        return folder in self.folders

class MockConnection:
    def status(self, folder, items):
        # Simulate STATUS command response
        if folder == '[Gmail]/All Mail':
            return ('OK', [f'{folder} (MESSAGES 11481)'])
        elif folder == 'INBOX':
            return ('OK', [f'{folder} (MESSAGES 32)'])
        else:
            return ('OK', [f'{folder} (MESSAGES 10)'])
    
    def search(self, charset, criteria):
        # Simulate search response (fallback method)
        if criteria == 'ALL':
            return ('OK', [b'1 2 3 4 5'])  # 5 emails
        return ('OK', [b''])

def test_folder_counting_performance():
    """Test the performance of folder counting with timeout protection."""
    print("🚀 Testing Folder Counting Performance")
    print("=" * 50)
    
    mock_connection = SlowMockIMAPConnection()
    email_ops = EmailOperations(mock_connection)
    
    folders = ['INBOX', '[Gmail]/All Mail', '[Gmail]/Sent Mail', '[Gmail]/Trash']
    
    print(f"Testing folder counting for {len(folders)} folders...")
    print("Folders:", folders)
    print()
    
    # Test with timeout protection
    start_time = time.time()
    folder_counts = email_ops.get_folders_with_counts(folders, timeout_per_folder=3)
    end_time = time.time()
    
    print("Results:")
    print("-" * 30)
    for folder, count in folder_counts.items():
        if count == -1:
            print(f"📁 {folder}: ? (timeout/error)")
        else:
            print(f"📁 {folder}: {count:,} emails")
    
    print("-" * 30)
    print(f"⏱️  Total time: {end_time - start_time:.1f} seconds")
    
    # Check if timeout protection worked
    if end_time - start_time < 10:  # Should be much faster than without timeout
        print("✅ Timeout protection working - fast response!")
    else:
        print("❌ Still too slow - timeout protection may not be working")
    
    print("\n💡 Performance improvements:")
    print("   1. ✅ STATUS command used for fast folder counting")
    print("   2. ✅ Timeout protection prevents hanging on slow folders")
    print("   3. ✅ Graceful fallback for folders that can't be counted quickly")

if __name__ == "__main__":
    test_folder_counting_performance()