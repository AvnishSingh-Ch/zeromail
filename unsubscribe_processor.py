#!/usr/bin/env python3
"""
Unsubscribe Processing Module for Gmail IMAP Cleaner

Handles unsubscribe link extraction and HTTP request processing.
"""

import re
import time
import logging
import requests


class UnsubscribeProcessor:
    """
    Unsubscribe link processor for extraction and HTTP request handling.
    """
    
    def __init__(self, email_operations, request_delay=1, http_timeout=10):
        self.email_operations = email_operations
        self.request_delay = request_delay
        self.http_timeout = http_timeout
        self.unsubscribe_regex = r'https?://[^\s<>"]+unsubscribe[^\s<>"]*'
    
    def extract_unsubscribe_links(self, email_content):
        """Extract unsubscribe URLs from email content using regex."""
        if not email_content:
            return []
        
        try:
            matches = re.findall(self.unsubscribe_regex, email_content, re.IGNORECASE)
            
            unique_links = []
            seen_links = set()
            
            for match in matches:
                cleaned_url = match.rstrip('.,;!?)')
                
                if self.is_valid_unsubscribe_url(cleaned_url) and cleaned_url not in seen_links:
                    unique_links.append(cleaned_url)
                    seen_links.add(cleaned_url)
            
            return unique_links
            
        except Exception as e:
            logging.warning(f"Error extracting unsubscribe links: {e}")
            return []
    
    def is_valid_unsubscribe_url(self, url):
        """Validate that a URL is a proper unsubscribe link."""
        if not url or len(url) < 10:
            return False
        
        if not url.lower().startswith(('http://', 'https://')):
            return False
        
        if 'unsubscribe' not in url.lower():
            return False
        
        suspicious_patterns = ['javascript:', 'data:', 'file:', 'ftp:']
        if any(pattern in url.lower() for pattern in suspicious_patterns):
            return False
        
        return True
    
    def extract_links_from_email(self, email_id):
        """Extract unsubscribe links from a specific email."""
        metadata = self.email_operations.get_email_metadata(email_id)
        if not metadata:
            logging.warning(f"Could not get metadata for email {email_id}")
            return None
        
        content = self.email_operations.get_email_content(email_id)
        if not content:
            logging.warning(f"Could not get content for email {email_id}")
            return {
                'email_id': email_id,
                'subject': metadata.get('subject', 'Unknown'),
                'from': metadata.get('from', 'Unknown'),
                'links': []
            }
        
        links = self.extract_unsubscribe_links(content)
        
        return {
            'email_id': email_id,
            'subject': metadata.get('subject', 'Unknown'),
            'from': metadata.get('from', 'Unknown'),
            'links': links,
            'content_length': len(content)
        }
    
    def process_unsubscribe_links(self, email_ids):
        """Process multiple emails to extract all unsubscribe links."""
        results = {
            'emails_processed': 0,
            'emails_with_links': 0,
            'total_links_found': 0,
            'unique_links': set(),
            'email_details': []
        }
        
        if not email_ids:
            logging.info("No emails to process for unsubscribe links")
            return results
        
        logging.info(f"Extracting unsubscribe links from {len(email_ids)} emails...")
        
        for email_id in email_ids:
            try:
                email_data = self.extract_links_from_email(email_id)
                
                if email_data:
                    results['emails_processed'] += 1
                    
                    if email_data['links']:
                        results['emails_with_links'] += 1
                        results['total_links_found'] += len(email_data['links'])
                        
                        for link in email_data['links']:
                            results['unique_links'].add(link)
                        
                        logging.info(f"Email '{email_data['subject'][:50]}...' from {email_data['from']}: {len(email_data['links'])} links")
                        for link in email_data['links']:
                            logging.info(f"  → {link}")
                    else:
                        logging.debug(f"No unsubscribe links found in email {email_id}")
                    
                    results['email_details'].append(email_data)
                
            except Exception as e:
                logging.error(f"Error processing email {email_id} for links: {e}")
        
        results['unique_links'] = list(results['unique_links'])
        
        logging.info(f"Link extraction completed:")
        logging.info(f"  Emails processed: {results['emails_processed']}")
        logging.info(f"  Emails with links: {results['emails_with_links']}")
        logging.info(f"  Total links found: {results['total_links_found']}")
        logging.info(f"  Unique links: {len(results['unique_links'])}")
        
        return results
    
    def send_unsubscribe_request(self, url):
        """Send a GET request to an unsubscribe URL."""
        result = {
            'url': url,
            'success': False,
            'status_code': None,
            'error': None,
            'response_time': None
        }
        
        try:
            start_time = time.time()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=self.http_timeout,
                allow_redirects=True,
                verify=True
            )
            
            end_time = time.time()
            result['response_time'] = round(end_time - start_time, 2)
            result['status_code'] = response.status_code
            
            if 200 <= response.status_code < 400:
                result['success'] = True
                logging.info(f"✓ Unsubscribe request successful: {url} (Status: {response.status_code})")
            else:
                result['error'] = f"HTTP {response.status_code}"
                logging.warning(f"✗ Unsubscribe request failed: {url} (Status: {response.status_code})")
            
        except requests.exceptions.Timeout:
            result['error'] = "Request timeout"
            logging.warning(f"✗ Unsubscribe request timed out: {url}")
        except requests.exceptions.ConnectionError:
            result['error'] = "Connection error"
            logging.warning(f"✗ Connection error for unsubscribe request: {url}")
        except requests.exceptions.SSLError:
            result['error'] = "SSL error"
            logging.warning(f"✗ SSL error for unsubscribe request: {url}")
        except requests.exceptions.RequestException as e:
            result['error'] = str(e)
            logging.warning(f"✗ Request error for unsubscribe: {url} - {e}")
        except Exception as e:
            result['error'] = f"Unexpected error: {e}"
            logging.error(f"✗ Unexpected error sending unsubscribe request to {url}: {e}")
        
        return result
    
    def send_unsubscribe_requests_batch(self, urls):
        """Send unsubscribe requests to multiple URLs with rate limiting."""
        results = {
            'total_requests': len(urls),
            'successful_requests': 0,
            'failed_requests': 0,
            'request_details': [],
            'errors': {}
        }
        
        if not urls:
            logging.info("No unsubscribe URLs to process")
            return results
        
        logging.info(f"Sending unsubscribe requests to {len(urls)} URLs...")
        logging.info(f"Request delay: {self.request_delay} seconds between requests")
        
        for i, url in enumerate(urls, 1):
            logging.info(f"Processing unsubscribe request {i}/{len(urls)}: {url}")
            
            request_result = self.send_unsubscribe_request(url)
            results['request_details'].append(request_result)
            
            if request_result['success']:
                results['successful_requests'] += 1
            else:
                results['failed_requests'] += 1
                
                error_type = request_result['error'] or 'Unknown error'
                if error_type not in results['errors']:
                    results['errors'][error_type] = 0
                results['errors'][error_type] += 1
            
            if i < len(urls):
                logging.debug(f"Waiting {self.request_delay} seconds before next request...")
                time.sleep(self.request_delay)
        
        logging.info("=" * 50)
        logging.info("UNSUBSCRIBE REQUEST SUMMARY")
        logging.info("=" * 50)
        logging.info(f"Total requests sent: {results['total_requests']}")
        logging.info(f"Successful requests: {results['successful_requests']}")
        logging.info(f"Failed requests: {results['failed_requests']}")
        
        if results['errors']:
            logging.info("Error breakdown:")
            for error_type, count in results['errors'].items():
                logging.info(f"  {error_type}: {count}")
        
        logging.info("=" * 50)
        
        return results
    
    def confirm_unsubscribe_requests(self, urls):
        """Ask user for confirmation before sending unsubscribe requests."""
        if not urls:
            return False
        
        print("\n" + "=" * 60)
        print("UNSUBSCRIBE REQUEST CONFIRMATION")
        print("=" * 60)
        print(f"Found {len(urls)} unsubscribe links to process:")
        
        for i, url in enumerate(urls[:5], 1):
            print(f"{i:2d}. {url}")
        
        if len(urls) > 5:
            print(f"    ... and {len(urls) - 5} more URLs")
        
        print("\nWARNING: This will send HTTP GET requests to these URLs.")
        print("This action cannot be undone.")
        print(f"Requests will be sent with {self.request_delay} second delays between them.")
        
        while True:
            response = input("\nProceed with sending unsubscribe requests? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    def validate_and_clean_links(self, links):
        """Validate and clean a list of unsubscribe links."""
        cleaned_links = []
        
        for link in links:
            if self.is_valid_unsubscribe_url(link):
                cleaned_link = link.strip()
                
                # Remove common tracking parameters
                tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']
                
                if '?' in cleaned_link:
                    base_url, params = cleaned_link.split('?', 1)
                    param_pairs = params.split('&')
                    filtered_params = []
                    
                    for param in param_pairs:
                        if '=' in param:
                            param_name = param.split('=')[0]
                            if param_name not in tracking_params:
                                filtered_params.append(param)
                    
                    if filtered_params:
                        cleaned_link = base_url + '?' + '&'.join(filtered_params)
                    else:
                        cleaned_link = base_url
                
                cleaned_links.append(cleaned_link)
            else:
                logging.warning(f"Invalid unsubscribe URL filtered out: {link}")
        
        return cleaned_links