#!/usr/bin/env python3
"""
Enhanced Configuration Module for Gmail IMAP Cleaner

Supports environment variables, encrypted credential storage, and advanced configuration options.
"""

import os
import getpass
import datetime
import logging
import json
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# Try to import optional dependencies
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class CleanerConfig:
    """Configuration data class for type safety and validation."""
    email: str
    password: str
    cutoff_date: str
    folders: list
    dry_run: bool = False
    backup_before_delete: bool = True
    max_batch_size: int = 500
    request_delay: int = 1
    http_timeout: int = 10
    enable_analytics: bool = True
    log_level: str = "INFO"


class CredentialManager:
    """Secure credential storage with optional encryption."""
    
    def __init__(self, storage_path: str = "./credentials"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.key_file = self.storage_path / "key.key"
        self.cred_file = self.storage_path / "credentials.enc"
    
    def _get_or_create_key(self) -> bytes:
        """Get existing encryption key or create a new one."""
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography library required for encrypted credentials")
        
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
            return key
    
    def store_credentials(self, email: str, password: str, encrypt: bool = True) -> bool:
        """Store credentials securely."""
        try:
            credentials = {"email": email, "password": password}
            
            if encrypt and CRYPTO_AVAILABLE:
                key = self._get_or_create_key()
                fernet = Fernet(key)
                
                cred_json = json.dumps(credentials)
                encrypted_data = fernet.encrypt(cred_json.encode())
                
                with open(self.cred_file, 'wb') as f:
                    f.write(encrypted_data)
                
                os.chmod(self.cred_file, 0o600)
                logging.info("Credentials stored with encryption")
            else:
                # Store as plain JSON (not recommended for production)
                with open(self.cred_file.with_suffix('.json'), 'w') as f:
                    json.dump(credentials, f, indent=2)
                
                os.chmod(self.cred_file.with_suffix('.json'), 0o600)
                logging.warning("Credentials stored without encryption")
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to store credentials: {e}")
            return False
    
    def load_credentials(self) -> Optional[Dict[str, str]]:
        """Load stored credentials."""
        try:
            # Try encrypted file first
            if self.cred_file.exists() and CRYPTO_AVAILABLE:
                key = self._get_or_create_key()
                fernet = Fernet(key)
                
                with open(self.cred_file, 'rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = fernet.decrypt(encrypted_data)
                credentials = json.loads(decrypted_data.decode())
                
                logging.info("Loaded encrypted credentials")
                return credentials
            
            # Fallback to plain JSON
            json_file = self.cred_file.with_suffix('.json')
            if json_file.exists():
                with open(json_file, 'r') as f:
                    credentials = json.load(f)
                
                logging.info("Loaded plain text credentials")
                return credentials
            
            return None
            
        except Exception as e:
            logging.error(f"Failed to load credentials: {e}")
            return None
    
    def delete_credentials(self) -> bool:
        """Delete stored credentials."""
        try:
            files_to_delete = [self.key_file, self.cred_file, self.cred_file.with_suffix('.json')]
            deleted_count = 0
            
            for file_path in files_to_delete:
                if file_path.exists():
                    file_path.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logging.info(f"Deleted {deleted_count} credential files")
                return True
            else:
                logging.info("No credential files found to delete")
                return False
                
        except Exception as e:
            logging.error(f"Failed to delete credentials: {e}")
            return False


class EnhancedConfigManager:
    """Enhanced configuration manager with multiple sources."""
    
    def __init__(self):
        self.load_environment()
        self.credential_manager = CredentialManager()
        
    def load_environment(self):
        """Load environment variables from .env file if available."""
        if DOTENV_AVAILABLE:
            env_file = Path('.env')
            if env_file.exists():
                load_dotenv()
                logging.info("Loaded configuration from .env file")
            else:
                logging.info("No .env file found, using system environment variables")
        else:
            logging.info("python-dotenv not available, using system environment variables only")
    
    def get_config_from_env(self) -> Optional[CleanerConfig]:
        """Get configuration from environment variables."""
        try:
            email = os.getenv('GMAIL_EMAIL')
            password = os.getenv('GMAIL_PASSWORD')
            
            if not email or not password:
                return None
            
            config = CleanerConfig(
                email=email,
                password=password,
                cutoff_date=os.getenv('DEFAULT_CUTOFF_DATE', '01-Jan-2023'),
                folders=[os.getenv('DEFAULT_FOLDER', 'INBOX')],
                dry_run=os.getenv('DRY_RUN', 'false').lower() == 'true',
                backup_before_delete=os.getenv('BACKUP_BEFORE_DELETE', 'true').lower() == 'true',
                max_batch_size=int(os.getenv('DEFAULT_BATCH_SIZE', '500')),
                request_delay=int(os.getenv('REQUEST_DELAY', '1')),
                http_timeout=int(os.getenv('HTTP_TIMEOUT', '10')),
                enable_analytics=os.getenv('ENABLE_ANALYTICS', 'true').lower() == 'true',
                log_level=os.getenv('LOG_LEVEL', 'INFO')
            )
            
            logging.info("Configuration loaded from environment variables")
            return config
            
        except Exception as e:
            logging.error(f"Failed to load environment configuration: {e}")
            return None
    
    def get_config_from_stored_credentials(self) -> Optional[CleanerConfig]:
        """Get configuration from stored credentials."""
        credentials = self.credential_manager.load_credentials()
        if not credentials:
            return None
        
        try:
            config = CleanerConfig(
                email=credentials['email'],
                password=credentials['password'],
                cutoff_date=os.getenv('DEFAULT_CUTOFF_DATE', '01-Jan-2023'),
                folders=[os.getenv('DEFAULT_FOLDER', 'INBOX')]
            )
            
            logging.info("Configuration loaded from stored credentials")
            return config
            
        except Exception as e:
            logging.error(f"Failed to load stored credential configuration: {e}")
            return None
    
    def save_credentials_interactive(self) -> bool:
        """Interactively save credentials with encryption option."""
        print("\n" + "="*60)
        print("CREDENTIAL STORAGE SETUP")
        print("="*60)
        print("Store your credentials securely for future use.")
        
        if CRYPTO_AVAILABLE:
            print("✅ Encryption available - credentials will be encrypted")
            encrypt = True
        else:
            print("⚠️  Encryption not available - install 'cryptography' for encrypted storage")
            encrypt = input("Store credentials without encryption? (y/n): ").lower().startswith('y')
            if not encrypt:
                return False
        
        email = input("Enter your Gmail address: ").strip()
        if not email:
            print("Email address cannot be empty")
            return False
        
        print("\nNote: Use App Password (recommended) or regular password")
        password = getpass.getpass("Enter your Gmail password: ").strip()
        if not password:
            print("Password cannot be empty")
            return False
        
        return self.credential_manager.store_credentials(email, password, encrypt)
    
    def get_comprehensive_config(self) -> CleanerConfig:
        """Get configuration from multiple sources with fallback priority."""
        # Priority order: CLI args > environment variables > stored credentials > interactive input
        
        # Try environment variables first
        config = self.get_config_from_env()
        if config:
            return config
        
        # Try stored credentials
        config = self.get_config_from_stored_credentials()
        if config:
            return config
        
        # Fall back to interactive input
        return self.get_interactive_config()
    
    def get_interactive_config(self) -> CleanerConfig:
        """Get configuration through interactive prompts."""
        print("\n" + "="*60)
        print("GMAIL IMAP CLEANER - INTERACTIVE CONFIGURATION")
        print("="*60)
        
        # Ask if user wants to store credentials
        store_creds = input("Do you want to store credentials for future use? (y/n): ").lower().startswith('y')
        
        if store_creds:
            if self.save_credentials_interactive():
                config = self.get_config_from_stored_credentials()
                if config:
                    # Still need to get other settings interactively
                    cutoff_date = input(f"Enter cutoff date [{config.cutoff_date}]: ").strip()
                    if cutoff_date:
                        config.cutoff_date = cutoff_date
                    
                    folder = input(f"Enter folder [{config.folders[0]}]: ").strip()
                    if folder:
                        config.folders = [folder]
                    
                    return config
        
        # Manual input for everything
        email = input("Enter your Gmail address: ").strip()
        password = getpass.getpass("Enter your Gmail password: ").strip()
        cutoff_date = input("Enter cutoff date (DD-MMM-YYYY) [01-Jan-2023]: ").strip() or "01-Jan-2023"
        folder = input("Enter folder [INBOX]: ").strip() or "INBOX"
        
        dry_run = input("Perform dry run? (y/n) [n]: ").lower().startswith('y')
        backup = input("Backup emails before deletion? (y/n) [y]: ").lower()
        backup_before_delete = not backup.startswith('n')  # Default to True
        
        return CleanerConfig(
            email=email,
            password=password,
            cutoff_date=cutoff_date,
            folders=[folder],
            dry_run=dry_run,
            backup_before_delete=backup_before_delete
        )


def load_yaml_rules(rules_path: str = "./rules.yaml") -> Optional[Dict[str, Any]]:
    """Load email processing rules from YAML file."""
    if not YAML_AVAILABLE:
        logging.warning("PyYAML not available - YAML rules not supported")
        return None
    
    rules_file = Path(rules_path)
    if not rules_file.exists():
        logging.info(f"No rules file found at {rules_path}")
        return None
    
    try:
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
        
        logging.info(f"Loaded rules configuration from {rules_path}")
        return rules
        
    except Exception as e:
        logging.error(f"Failed to load rules from {rules_path}: {e}")
        return None


def create_default_rules_file(rules_path: str = "./rules.yaml"):
    """Create a default rules configuration file."""
    if not YAML_AVAILABLE:
        logging.warning("PyYAML not available - cannot create rules file")
        return False
    
    default_rules = {
        "email_rules": {
            "auto_delete": [
                {
                    "name": "Delete old newsletters",
                    "condition": {
                        "age_days": 30,
                        "categories": ["newsletter", "marketing"]
                    },
                    "action": "delete"
                },
                {
                    "name": "Delete old promotions", 
                    "condition": {
                        "age_days": 7,
                        "subject_keywords": ["sale", "offer", "discount", "deal"]
                    },
                    "action": "delete"
                }
            ],
            "auto_archive": [
                {
                    "name": "Archive old receipts",
                    "condition": {
                        "age_days": 90,
                        "subject_keywords": ["receipt", "invoice", "order"]
                    },
                    "action": "archive"
                }
            ],
            "auto_unsubscribe": [
                {
                    "name": "Unsubscribe from marketing emails",
                    "condition": {
                        "sender_domains": ["marketing.example.com", "newsletter.example.com"],
                        "has_unsubscribe_link": True
                    },
                    "action": "unsubscribe"
                }
            ]
        },
        "sender_rules": {
            "whitelist": [
                "important@company.com",
                "@bank.com",
                "@family-domain.com"
            ],
            "blacklist": [
                "@spam-domain.com",
                "noreply@casino"
            ],
            "trusted_domains": [
                "github.com",
                "stackoverflow.com", 
                "google.com"
            ]
        },
        "size_limits": {
            "large_email_threshold_mb": 10,
            "attachment_size_threshold_mb": 25
        },
        "performance": {
            "max_concurrent_operations": 5,
            "timeout_per_folder_seconds": 30,
            "bulk_operation_threshold": 100
        }
    }
    
    try:
        with open(rules_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_rules, f, default_flow_style=False, indent=2)
        
        logging.info(f"Created default rules file at {rules_path}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to create rules file: {e}")
        return False


class EnhancedConfig:
    """Enhanced configuration system with multiple data sources."""
    
    def __init__(self):
        self.config_manager = EnhancedConfigManager()
        self.rules = None
        
        # Load rules if available
        rules_path = os.getenv('RULES_CONFIG_PATH', './rules.yaml')
        self.rules = load_yaml_rules(rules_path)
        
        # Create default rules file if none exists
        if not self.rules and YAML_AVAILABLE:
            if input("Create default rules file? (y/n): ").lower().startswith('y'):
                create_default_rules_file(rules_path)
                self.rules = load_yaml_rules(rules_path)
    
    def get_config(self, use_env: bool = True, use_stored: bool = True) -> CleanerConfig:
        """Get configuration with flexible source selection."""
        if use_env:
            config = self.config_manager.get_config_from_env()
            if config:
                return config
        
        if use_stored:
            config = self.config_manager.get_config_from_stored_credentials()
            if config:
                return config
        
        return self.config_manager.get_interactive_config()
    
    def get_rule(self, rule_type: str, rule_name: str = None) -> Optional[Dict[str, Any]]:
        """Get specific rule from rules configuration."""
        if not self.rules:
            return None
        
        try:
            rules_section = self.rules.get('email_rules', {}).get(rule_type, [])
            
            if rule_name:
                for rule in rules_section:
                    if rule.get('name') == rule_name:
                        return rule
                return None
            else:
                return rules_section
                
        except Exception as e:
            logging.error(f"Error getting rule {rule_type}.{rule_name}: {e}")
            return None
    
    def validate_config(self, config: CleanerConfig) -> bool:
        """Validate configuration values."""
        try:
            # Validate email format
            if not config.email or '@' not in config.email:
                logging.error("Invalid email address format")
                return False
            
            # Validate date format
            try:
                datetime.datetime.strptime(config.cutoff_date, "%d-%b-%Y")
            except ValueError:
                logging.error(f"Invalid date format: {config.cutoff_date}. Use DD-MMM-YYYY")
                return False
            
            # Validate numeric values
            if config.max_batch_size <= 0:
                logging.error("Batch size must be positive")
                return False
            
            if config.request_delay < 0:
                logging.error("Request delay cannot be negative")
                return False
            
            logging.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logging.error(f"Configuration validation error: {e}")
            return False


# Backward compatibility functions
def get_user_input():
    """Backward compatible function for existing code."""
    config_manager = EnhancedConfig()
    config = config_manager.get_config()
    
    # Convert to old format for compatibility
    return {
        'email': config.email,
        'password': config.password,
        'cutoff_date': config.cutoff_date,
        'folders': config.folders,
        'delete_old': True,
        'process_unsubscribe': True,
        'dry_run': config.dry_run,
        'fast_mode': False
    }


def handle_authentication_error():
    """Enhanced authentication error handler."""
    print("\n" + "="*70)
    print("GMAIL AUTHENTICATION ERROR")
    print("="*70)
    print("Common solutions:")
    print("1. Generate App Password: https://myaccount.google.com/apppasswords")
    print("2. Enable 2-Factor Authentication first")
    print("3. Check email address spelling")
    print("4. Verify password/app password is correct")
    print("5. Check network connectivity")
    print("\nWould you like to:")
    print("a) Try different credentials")
    print("b) Get help setting up App Password")
    print("c) Exit")
    
    choice = input("\nEnter choice (a/b/c): ").lower()
    
    if choice == 'a':
        return True
    elif choice == 'b':
        show_authentication_help()
        return input("\nTry again with new credentials? (y/n): ").lower().startswith('y')
    else:
        return False


def show_authentication_help():
    """Display enhanced authentication help with step-by-step guide."""
    help_text = """
╔══════════════════════════════════════════════════════════════════════╗
║                     GMAIL APP PASSWORD SETUP GUIDE                  ║
╚══════════════════════════════════════════════════════════════════════╝

🔐 Gmail requires an App Password for IMAP access. Follow these steps:

📋 STEP 1: Enable 2-Factor Authentication
   🔗 Go to: https://myaccount.google.com/security
   ✅ Turn on "2-Step Verification" 
   📱 Set up phone number or authenticator app

📋 STEP 2: Generate App Password
   🔗 Go to: https://myaccount.google.com/apppasswords
   📧 Select "Mail" for app type
   💻 Select your device type
   🔑 Copy the 16-character password (example: abcd efgh ijkl mnop)

📋 STEP 3: Use App Password in This Tool
   ✏️  Enter email: your.email@gmail.com
   🔑 Enter password: abcdefghijklmnop (remove spaces)
   🚀 Run the email cleaner!

💡 TROUBLESHOOTING TIPS:
   • Remove all spaces from the app password
   • Don't use your regular Gmail password
   • Make sure 2FA is enabled before creating app password
   • Try waiting a few minutes after creating the app password

🔒 SECURITY NOTE:
   This tool can store your credentials encrypted on your local machine
   for convenience and security.
"""
    print(help_text)


def ask_continue_or_exit():
    """Enhanced continuation prompt."""
    print("\n" + "="*50)
    print("What would you like to do next?")
    print("1. Continue with another operation (same configuration)")
    print("2. Change configuration (email/date/folder)")
    print("3. Exit")
    
    while True:
        choice = input("Enter choice (1-3): ").strip()
        if choice == '1':
            return 'continue'
        elif choice == '2':
            return 'new_config'
        elif choice == '3':
            return 'exit'
        else:
            print("Please enter 1, 2, or 3")


# Enhanced default configuration with new features
DEFAULT_CONFIG = {
    'imap_server': 'imap.gmail.com',
    'imap_port': 993,
    'request_delay': 1,
    'http_timeout': 10,
    'batch_size': 500,
    'log_format': '%(asctime)s - %(levelname)s - %(message)s',
    'backup_format': 'mbox',
    'enable_analytics': True,
    'enable_backup': True,
    'enable_encryption': True,
    'max_preview_emails': 10,
    'auto_create_backups': True
}


if __name__ == "__main__":
    # Test the enhanced configuration system
    print("🧪 Testing Enhanced Configuration System")
    print("="*50)
    
    config_manager = EnhancedConfig()
    
    # Test environment loading
    print("📧 Environment variables available:")
    env_vars = ['GMAIL_EMAIL', 'GMAIL_PASSWORD', 'DEFAULT_CUTOFF_DATE']
    for var in env_vars:
        value = os.getenv(var, 'Not set')
        print(f"  {var}: {'***' if 'PASSWORD' in var and value != 'Not set' else value}")
    
    print(f"\n📁 Available features:")
    print(f"  Environment files (.env): {'✅' if DOTENV_AVAILABLE else '❌'}")
    print(f"  Encrypted credentials: {'✅' if CRYPTO_AVAILABLE else '❌'}")
    print(f"  YAML rules: {'✅' if YAML_AVAILABLE else '❌'}")
    
    print("\n🚀 Enhanced configuration system ready!")
