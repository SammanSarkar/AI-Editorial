#!/usr/bin/env python3
"""
Production Editorial Updater for omegaUp
Updates problem editorials using the official /api/problem/updateSolution/ endpoint.
"""

import sys
import os
import time
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Setup logging
def setup_logging():
    """Setup logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"editorial_updater_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class ProductionEditorialUpdater:
    """Updates problem editorials using the official omegaUp APIs."""

    def __init__(self):
        load_dotenv()
        
        # API Configuration
        self.api_url = os.getenv("OMEGAUP_API_URL", "https://omegaup.com/api")
        self.base_url = os.getenv("OMEGAUP_BASE_URL", "https://omegaup.com")
        
        # Initialize session for persistent connections and cookies
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'omegaUp-Editorial-Updater-Production/1.0',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8'
        })
        
        # Login immediately
        self._login()
        
        logger.info("Production Editorial Updater initialized successfully")

    def _login(self) -> None:
        """
        Authenticate with omegaUp using the official /api/user/login/ endpoint.
        """
        username = os.getenv("OMEGAUP_USERNAME")
        password = os.getenv("OMEGAUP_PASSWORD")
        
        if not username or not password:
            error_msg = "OMEGAUP_USERNAME and OMEGAUP_PASSWORD must be set in .env file"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            logger.info(f"Authenticating with production API as: {username}")
            
            login_data = {
                'usernameOrEmail': username,
                'password': password
            }
            
            url = f"{self.api_url}/user/login"
            logger.info(f"POST {url}")
            
            response = self.session.post(url, data=login_data, timeout=(10, 30))
            
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"HTTP Error {response.status_code}: {response.text}")
                raise RuntimeError(f"Authentication failed with status {response.status_code}")
                
            result = response.json()
            logger.info(f"API Response: {result}")
            
            if result.get("status") == "ok":
                auth_token = result.get('auth_token')
                if auth_token:
                    logger.info(f"Received auth_token from API: {auth_token[:20]}...")
                
                # Log session cookies
                cookies = dict(self.session.cookies)
                if cookies:
                    logger.info(f"Session cookies: {list(cookies.keys())}")
                    for name, value in cookies.items():
                        logger.info(f"Cookie {name}: {value[:20]}..." if len(value) > 20 else f"Cookie {name}: {value}")
                
                logger.info("Successfully authenticated with production omegaUp API")
                return
            
            error_msg = f"Login failed: {result.get('error', 'Unknown error')}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Authentication request failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_problem_details(self, problem_alias: str) -> Dict[str, Any]:
        """Fetch problem details to verify we have access."""
        try:
            logger.info(f"[{problem_alias}] Fetching problem details to verify access")
            
            url = f"{self.api_url}/problem/details"
            params = {"problem_alias": problem_alias}
            
            logger.info(f"GET {url} with params: {params}")
            
            response = self.session.get(url, params=params, timeout=(10, 30))
            
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"HTTP Error {response.status_code}: {response.text}")
                raise RuntimeError(f"Failed to fetch problem details: HTTP {response.status_code}")
            
            result = response.json()
            
            if result.get("status") != "ok":
                error_msg = f"Failed to fetch problem details: {result.get('error', 'Unknown error')}"
                logger.error(f"[{problem_alias}] {error_msg}")
                raise RuntimeError(error_msg)
            
            title = result.get('title', problem_alias)
            visibility = result.get('visibility', 'unknown')
            
            logger.info(f"[{problem_alias}] Successfully verified access to: '{title}' (visibility: {visibility})")
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch problem details: {str(e)}"
            logger.error(f"[{problem_alias}] {error_msg}")
            raise RuntimeError(error_msg)

    def update_editorial(self, problem_alias: str, editorial_content: str, commit_message: str = None, language: str = "markdown") -> bool:
        """
        Update problem editorial using the official /api/problem/updateSolution/ endpoint.
        
        API Documentation:
        - Endpoint: /api/problem/updateSolution/
        - Required Parameters: problem_alias, solution, message
        - Optional Parameters: lang, and many others for full problem updates
        """
        try:
            logger.info(f"[{problem_alias}] Updating problem editorial")
            logger.info(f"[{problem_alias}] Editorial content length: {len(editorial_content)} chars")
            logger.info(f"[{problem_alias}] Language: {language}")
            
            if commit_message is None:
                commit_message = f"Updated editorial via Production Editorial Updater on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            logger.info(f"[{problem_alias}] Commit message: {commit_message}")
            
            # Prepare data for the API call
            data = {
                'problem_alias': problem_alias,
                'solution': editorial_content,
                'message': commit_message,
                'lang': language
            }
            
            url = f"{self.api_url}/problem/updateSolution"
            logger.info(f"POST {url}")
            
            # Log the data being sent (but truncate content for readability)
            log_data = data.copy()
            if len(log_data['solution']) > 200:
                log_data['solution'] = log_data['solution'][:200] + f"... (total {len(data['solution'])} chars)"
            logger.info(f"Request data: {log_data}")
            
            response = self.session.post(url, data=data, timeout=(10, 60))
            
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"HTTP Error {response.status_code}: {response.text}")
                return False
            
            try:
                result = response.json()
                logger.info(f"API Response: {result}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {response.text}")
                return False
            
            if result.get("status") == "ok":
                logger.info(f"[{problem_alias}] ✅ Editorial updated successfully!")
                return True
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"[{problem_alias}] ❌ Editorial update failed: {error_msg}")
                return False
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Editorial update request failed: {str(e)}"
            logger.error(f"[{problem_alias}] {error_msg}")
            return False

    def update_editorial_workflow(self, problem_alias: str, editorial_content: str, commit_message: str = None) -> bool:
        """Complete workflow to update a problem editorial."""
        
        logger.info("=" * 80)
        logger.info(f"[{problem_alias}] STARTING EDITORIAL UPDATE WORKFLOW")
        logger.info("=" * 80)
        logger.info(f"[{problem_alias}] Problem alias: {problem_alias}")
        logger.info(f"[{problem_alias}] Editorial length: {len(editorial_content)} characters")
        logger.info("=" * 80)
        
        try:
            # Step 1: Verify we have access to the problem
            logger.info(f"[{problem_alias}] STEP 1: VERIFYING PROBLEM ACCESS")
            logger.info("-" * 40)
            
            problem_data = self.get_problem_details(problem_alias)
            title = problem_data.get('title', problem_alias)
            
            # Step 2: Update the editorial
            logger.info("")
            logger.info(f"[{problem_alias}] STEP 2: UPDATING EDITORIAL")
            logger.info("-" * 40)
            
            success = self.update_editorial(problem_alias, editorial_content, commit_message)
            
            if success:
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"[{problem_alias}] EDITORIAL UPDATE COMPLETED SUCCESSFULLY")
                logger.info("=" * 80)
                logger.info(f"[{problem_alias}] SUMMARY:")
                logger.info(f"   Problem: {title}")
                logger.info(f"   Problem alias: {problem_alias}")
                logger.info(f"   Editorial length: {len(editorial_content)} characters")
                logger.info(f"   Commit message: {commit_message or 'Auto-generated'}")
                logger.info("=" * 80)
                return True
            else:
                logger.error("")
                logger.error("=" * 80)
                logger.error(f"[{problem_alias}] EDITORIAL UPDATE FAILED")
                logger.error("=" * 80)
                return False
                
        except Exception as e:
            logger.error(f"[{problem_alias}] Editorial update workflow failed: {str(e)}")
            return False

def get_dummy_editorial(problem_alias: str) -> str:
    """Generate dummy editorial content for testing."""
    return f"""# Editorial: {problem_alias}

## Problem Understanding

This is a **dummy editorial** generated for testing the production editorial updater.

The problem "{problem_alias}" requires understanding the following concepts:
- Basic programming logic
- Input/output handling
- Algorithm implementation

## Solution Approach

### Algorithm
1. Read the input carefully
2. Process the data according to the problem requirements
3. Output the result in the specified format

### Implementation Strategy
- Use appropriate data structures
- Handle edge cases
- Optimize for time and space complexity

## Code Implementation

```python
# Sample solution code
def solve():
    # Read input
    n = int(input())
    
    # Process
    result = n * 2  # Example operation
    
    # Output
    print(result)

solve()
```

## Complexity Analysis

- **Time Complexity**: O(1) - Constant time operation
- **Space Complexity**: O(1) - Constant space usage

## Important Notes

- This is a **test editorial** created by the Production Editorial Updater
- Replace this content with the actual problem editorial
- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
*Editorial generated by omegaUp Production Editorial Updater*
"""

def main():
    """Main function to update problem editorial."""
    
    if len(sys.argv) < 2:
        print("Usage: python editorial_updater.py <problem_alias> [custom_editorial_file]")
        print("Example: python editorial_updater.py sumas")
        print("Example: python editorial_updater.py aplusb my_editorial.md")
        print("")
        print("This will:")
        print("  1. Verify access to the problem")
        print("  2. Update the problem editorial using production API")
        print("  3. Use dummy content if no editorial file provided")
        return 1
    
    problem_alias = sys.argv[1]
    
    # Check if custom editorial file is provided
    editorial_content = None
    if len(sys.argv) > 2:
        editorial_file = sys.argv[2]
        try:
            with open(editorial_file, 'r', encoding='utf-8') as f:
                editorial_content = f.read()
            logger.info(f"Loaded editorial content from file: {editorial_file} ({len(editorial_content)} chars)")
        except FileNotFoundError:
            print(f"Error: Editorial file '{editorial_file}' not found")
            return 1
        except Exception as e:
            print(f"Error reading editorial file: {str(e)}")
            return 1
    else:
        # Use dummy content
        editorial_content = get_dummy_editorial(problem_alias)
        logger.info(f"Using dummy editorial content ({len(editorial_content)} chars)")
    
    try:
        logger.info("Starting Production Editorial Updater")
        logger.info(f"Target problem: {problem_alias}")
        
        updater = ProductionEditorialUpdater()
        success = updater.update_editorial_workflow(problem_alias, editorial_content)
        
        if success:
            logger.info("Editorial update completed successfully!")
            print(f"✅ Successfully updated editorial for problem: {problem_alias}")
            return 0
        else:
            logger.error("Editorial update failed")
            print(f"❌ Failed to update editorial for problem: {problem_alias}")
            return 1
            
    except Exception as e:
        logger.error(f"Editorial updater failed: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 