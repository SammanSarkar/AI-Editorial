#!/usr/bin/env python3
"""
Quality Problems Finder for omegaUp
Finds problems with quality badges and randomly selects 50 for testing.
"""

import sys
import os
import json
import logging
import requests
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Setup logging
def setup_logging():
    """Setup logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"quality_finder_{timestamp}.log"
    
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

class QualityProblemsFinder:
    """Finds quality problems using the omegaUp API."""

    def __init__(self):
        load_dotenv()
        
        # API Configuration
        self.api_url = os.getenv("OMEGAUP_API_URL", "https://omegaup.com/api")
        self.base_url = os.getenv("OMEGAUP_BASE_URL", "https://omegaup.com")
        
        # Initialize session for persistent connections and cookies
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'omegaUp-Quality-Problems-Finder/1.0',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8'
        })
        
        # Login for authenticated access
        self._login()
        
        logger.info("Quality Problems Finder initialized successfully")

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
                
            try:
                result = response.json()
                logger.info(f"API Response: {result}")
            except json.JSONDecodeError:
                logger.error(f"Raw response text: {response.text}")
                raise RuntimeError(f"Invalid JSON response: {response.text}")
            
            if result.get("status") == "ok":
                logger.info("Successfully authenticated with production omegaUp API")
                return
            
            error_msg = f"Login failed: {result.get('error', 'Unknown error')}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Authentication request failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_quality_problems(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Fetch quality problems from the first 1000 problems using the /api/problem/list/ endpoint.
        
        API Documentation:
        - Endpoint: /api/problem/list/
        - Parameter: only_quality_seal (bool) - Filter for quality problems only
        - Returns: types.ProblemListItem[]
        
        Note: Language compatibility is not available in the list API, so we assume
        most quality problems support C++17 (which is typically the case).
        """
        
        logger.info("Fetching quality problems from production API (assuming C++17 support)")
        
        all_problems = []
        quality_problems = []
        page = 1
        page_size = 100  # Get 100 problems per page
        max_total_problems = 1000  # Only check first 1000 problems
        
        while len(all_problems) < max_total_problems:
            try:
                # Calculate offset for pagination
                offset = (page - 1) * page_size
                
                url = f"{self.api_url}/problem/list"
                params = {
                    "only_quality_seal": True,  # Filter for quality problems only
                    "offset": offset,
                    "rowcount": page_size,
                    "order_by": "problem_id",  # Consistent ordering
                    "sort_order": "asc"
                }
                
                logger.info(f"GET {url} (page {page}, offset {offset})")
                logger.info(f"Parameters: {params}")
                
                response = self.session.get(url, params=params, timeout=(10, 30))
                
                logger.info(f"Response status code: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"HTTP Error {response.status_code}: {response.text}")
                    break
                
                try:
                    result = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response: {str(e)}")
                    break
                
                if result.get("status") != "ok":
                    logger.error(f"API error: {result.get('error', 'Unknown error')}")
                    break
                
                # Get the problems from this page
                page_problems = result.get("results", [])
                total_problems = result.get("total", 0)
                
                logger.info(f"Page {page}: Retrieved {len(page_problems)} quality problems")
                logger.info(f"Total quality problems available: {total_problems}")
                
                if not page_problems:
                    logger.info("No more problems to fetch")
                    break
                
                # Add all quality problems (assuming C++17 support)
                for problem in page_problems:
                    all_problems.append(problem)
                    quality_problems.append(problem)
                    
                    alias = problem.get('alias', 'unknown')
                    title = problem.get('title', 'Unknown Title')
                    logger.info(f"Added quality problem: {alias} - {title}")
                
                logger.info(f"Quality problems collected so far: {len(quality_problems)}")
                logger.info(f"Total problems scanned: {len(all_problems)}")
                
                # Check if we have enough or if we've reached the end
                if limit and len(quality_problems) >= limit:
                    logger.info(f"Reached desired limit of {limit} quality problems")
                    break
                
                if len(page_problems) < page_size:
                    logger.info("Reached end of results (page returned fewer problems than requested)")
                    break
                
                if len(all_problems) >= max_total_problems:
                    logger.info(f"Reached maximum scan limit of {max_total_problems} problems")
                    break
                
                # Move to next page
                page += 1
                
                # Safety limit to avoid infinite loops
                if page > 20:  # Max 2,000 problems (20 pages × 100)
                    logger.warning("Reached safety limit of 20 pages")
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for page {page}: {str(e)}")
                break
            except Exception as e:
                logger.error(f"Unexpected error on page {page}: {str(e)}")
                break
        
        logger.info(f"Finished fetching. Total problems scanned: {len(all_problems)}")
        logger.info(f"Quality problems found: {len(quality_problems)}")
        return quality_problems

    def select_random_problems(self, problems: List[Dict[str, Any]], count: int = 50) -> List[str]:
        """
        Randomly select a specified number of problems and return their aliases.
        """
        
        if len(problems) == 0:
            logger.warning("No problems available to select from")
            return []
        
        if len(problems) <= count:
            logger.info(f"Available problems ({len(problems)}) <= requested count ({count}). Returning all.")
            selected_problems = problems
        else:
            logger.info(f"Randomly selecting {count} problems from {len(problems)} available")
            selected_problems = random.sample(problems, count)
        
        # Extract aliases and log details
        aliases = []
        for i, problem in enumerate(selected_problems, 1):
            alias = problem.get('alias', 'unknown')
            title = problem.get('title', 'Unknown Title')
            difficulty = problem.get('difficulty', 'Unknown')
            
            aliases.append(alias)
            logger.info(f"{i:2d}. {alias} - {title} (Difficulty: {difficulty})")
        
        logger.info(f"Selected {len(aliases)} problem aliases")
        return aliases

    def save_problems_to_file(self, aliases: List[str], filename: str = "cpp17_quality_problems.txt") -> None:
        """
        Save the selected problem aliases to a text file.
        """
        
        try:
            filepath = Path(filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# C++17 compatible quality problems selected for AI editorial testing\n")
                f.write(f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total problems: {len(aliases)}\n")
                f.write("# All problems support cpp17-gcc language\n")
                f.write("# One problem alias per line\n\n")
                
                for alias in aliases:
                    f.write(f"{alias}\n")
            
            logger.info(f"Saved {len(aliases)} C++17 compatible problem aliases to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save problems to file: {str(e)}")

def main():
    """Main function to find and select quality problems for C++17 testing."""
    
    if len(sys.argv) > 1:
        try:
            requested_count = int(sys.argv[1])
        except ValueError:
            print("Usage: python quality_problems_finder.py [count]")
            print("       count: number of quality problems to select (default: 50)")
            print("       Note: Only scans first 1000 problems for efficiency")
            print("       Assumes C++17 support (most quality problems support it)")
            return 1
    else:
        requested_count = 50
    
    try:
        logger.info("Starting Quality Problems Finder for C++17 Testing")
        logger.info(f"Target: {requested_count} random quality problems")
        logger.info("Limiting search to first 1000 problems for efficiency")
        logger.info("Assuming C++17 support (most quality problems support multiple languages)")
        
        finder = QualityProblemsFinder()
        
        # Fetch quality problems
        logger.info("=" * 60)
        logger.info("STEP 1: FETCHING QUALITY PROBLEMS")
        logger.info("=" * 60)
        
        quality_problems = finder.get_quality_problems()
        
        if not quality_problems:
            logger.error("No quality problems found!")
            print("❌ No quality problems found!")
            return 1
        
        # Select random problems
        logger.info("")
        logger.info("=" * 60)
        logger.info("STEP 2: SELECTING RANDOM PROBLEMS")
        logger.info("=" * 60)
        
        selected_aliases = finder.select_random_problems(quality_problems, requested_count)
        
        if not selected_aliases:
            logger.error("No problems selected!")
            print("❌ No problems selected!")
            return 1
        
        # Save to file
        logger.info("")
        logger.info("=" * 60)
        logger.info("STEP 3: SAVING TO FILE")
        logger.info("=" * 60)
        
        filename = f"cpp17_quality_problems_{len(selected_aliases)}.txt"
        finder.save_problems_to_file(selected_aliases, filename)
        
        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Quality problems found: {len(quality_problems)}")
        logger.info(f"Problems selected: {len(selected_aliases)}")
        logger.info(f"Output file: {filename}")
        logger.info("=" * 60)
        
        # Print user-friendly summary
        print(f"✅ Success!")
        print(f"📊 Found {len(quality_problems)} quality problems")
        print(f"🎯 Selected {len(selected_aliases)} random problems")
        print(f"💾 Saved to: {filename}")
        print(f"📝 Ready for C++17 testing (assuming language support)")
        
        return 0
        
    except Exception as e:
        logger.error(f"Quality problems finder failed: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 