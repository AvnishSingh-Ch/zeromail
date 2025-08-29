#!/usr/bin/env python3
"""
Test script to identify errors in gmail_session.py
"""

try:
    from gmail_session import GmailSession
    print("✅ Successfully imported GmailSession")
    
    # Try to create an instance
    session = GmailSession()
    print("✅ Successfully created GmailSession instance")
    
    # Test basic methods
    session.print_styled("Test message", "info")
    print("✅ print_styled method works")
    
    print("All basic tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()