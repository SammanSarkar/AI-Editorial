#!/usr/bin/env python3
"""
Production Editorial Generator for omegaUp
Uses official omegaUp APIs as documented in the API documentation.
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

# Add parent directory to path to import prompts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts import (
    get_code_generation_prompt,
    get_editorial_generation_prompt,
    get_code_system_prompt,
    get_editorial_system_prompt,
    get_mock_code_template,
    get_mock_editorial_template
)

# Setup logging
def setup_logging():
    """Setup logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"prod_demo_{timestamp}.log"
    
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

class ProductionOmegaUpAPI:
    """Production-ready omegaUp API client using official documented endpoints."""

    def __init__(self):
        load_dotenv()
        
        # API Configuration
        self.api_url = os.getenv("OMEGAUP_API_URL", "https://omegaup.com/api")
        self.base_url = os.getenv("OMEGAUP_BASE_URL", "https://omegaup.com")
        
        # Initialize session for persistent connections and cookies
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'omegaUp-Editorial-Generator-Production/1.0',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8'
        })
        
        # Login immediately
        self._login()
        
        logger.info("Production omegaUp API client initialized successfully")

    def _login(self) -> None:
        """
        Authenticate with omegaUp using the official /api/user/login/ endpoint.
        
        API Documentation:
        - Endpoint: /api/user/login/
        - Parameters: usernameOrEmail (string), password (string)
        - Returns: auth_token (string)
        """
        username = os.getenv("OMEGAUP_USERNAME")
        password = os.getenv("OMEGAUP_PASSWORD")
        
        if not username or not password:
            error_msg = "OMEGAUP_USERNAME and OMEGAUP_PASSWORD must be set in .env file"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            logger.info(f"Authenticating with production API as: {username}")
            
            # Use exact parameters as documented in API
            login_data = {
                'usernameOrEmail': username,
                'password': password
            }
            
            # Use official API endpoint
            url = f"{self.api_url}/user/login"
            logger.info(f"POST {url}")
            
            response = self.session.post(url, data=login_data, timeout=(10, 30))
            
            # Log the response details for debugging
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
                # omegaUp uses session-based authentication, not Bearer tokens
                # The auth_token might be for different purposes, but session cookies handle API auth
                auth_token = result.get('auth_token')
                if auth_token:
                    logger.info(f"Received auth_token from API: {auth_token[:20]}...")
                    # DON'T add Authorization header - omegaUp uses session cookies
                    # self.session.headers['Authorization'] = f'token {auth_token}'
                    logger.info("Auth token received but using session cookies for API authentication")
                else:
                    logger.info("No explicit auth_token received - using session cookies")
                
                # Log session cookies for debugging
                cookies = dict(self.session.cookies)
                if cookies:
                    logger.info(f"Session cookies: {list(cookies.keys())}")
                    # Show the actual cookie values for debugging
                    for name, value in cookies.items():
                        logger.info(f"Cookie {name}: {value[:20]}..." if len(value) > 20 else f"Cookie {name}: {value}")
                else:
                    logger.warning("No session cookies received")
                
                logger.info("Successfully authenticated with production omegaUp API")
                return
            
            # If not successful, try to handle different response formats
            if "error" in result:
                error_msg = f"Login failed: {result['error']}"
            else:
                error_msg = f"Login failed: Unexpected response format: {result}"
            
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Authentication request failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response during authentication: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_problem_details(self, problem_alias: str) -> Dict[str, Any]:
        """
        Fetch problem details using the official /api/problem/details/ endpoint.
        
        API Documentation:
        - Endpoint: /api/problem/details/
        - Required Parameters: problem_alias (string)
        - Optional Parameters: contest_alias, lang, prevent_problemset_open, 
          problemset_id, show_solvers, statement_type
        - Returns: types.ProblemDetails
        """
        try:
            logger.info(f"[{problem_alias}] Fetching problem details from production API")
            
            # Use official API endpoint with exact parameter names from documentation
            url = f"{self.api_url}/problem/details"
            params = {
                "problem_alias": problem_alias,
                # Optional: can add other parameters as needed
                # "lang": "es",  # Language for statement
                # "show_solvers": True,  # Include solver information
                # "statement_type": "markdown"  # Statement format
            }
            
            logger.info(f"GET {url} with params: {params}")
            
            # Log current session state for debugging
            logger.info(f"Session headers: {dict(self.session.headers)}")
            cookies = dict(self.session.cookies)
            if cookies:
                logger.info(f"Session cookies: {list(cookies.keys())}")
            
            response = self.session.get(url, params=params, timeout=(10, 30))
            
            # Log response details for debugging 401 issues
            logger.info(f"Response status code: {response.status_code}")
            if response.status_code == 401:
                logger.error(f"401 UNAUTHORIZED response")
                logger.error(f"Response headers: {dict(response.headers)}")
                logger.error(f"Response text: {response.text}")
                
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[{problem_alias}] API Response Status: {result.get('status', 'unknown')}")
            
            if result.get("status") != "ok":
                error_msg = f"Failed to fetch problem details: {result.get('error', 'Unknown error')}"
                logger.error(f"[{problem_alias}] {error_msg}")
                raise RuntimeError(error_msg)
            
            # Log successful fetch with key details
            title = result.get('title', problem_alias)
            visibility = result.get('visibility', 'unknown')
            source = result.get('source', 'unknown')
            
            logger.info(f"[{problem_alias}] Successfully fetched: '{title}'")
            logger.info(f"[{problem_alias}] Visibility: {visibility}")
            logger.info(f"[{problem_alias}] Source: {source}")
            
            # Log available languages if present
            if 'languages' in result:
                languages = result['languages']
                logger.info(f"[{problem_alias}] Available languages: {languages}")
            
            # Log statement information
            if 'statement' in result:
                statement = result['statement']
                if isinstance(statement, dict):
                    statement_languages = list(statement.keys())
                    logger.info(f"[{problem_alias}] Statement languages: {statement_languages}")
                    
                    # Log actual statement content for each language
                    for lang, content in statement.items():
                        if lang == 'markdown' and content:
                            logger.info(f"[{problem_alias}] Statement ({lang}):")
                            logger.info("=" * 60)
                            logger.info(content)
                            logger.info("=" * 60)
                        elif content and len(str(content)) > 0:
                            logger.info(f"[{problem_alias}] Statement ({lang}): {len(str(content))} chars")
                            if len(str(content)) < 500:  # Show short content directly
                                logger.info(f"[{problem_alias}] {lang} content: {content}")
                            else:  # Show preview for long content
                                preview = str(content)[:200] + "..." if len(str(content)) > 200 else str(content)
                                logger.info(f"[{problem_alias}] {lang} content preview: {preview}")
                        else:
                            logger.info(f"[{problem_alias}] Statement ({lang}): empty")
                            
                elif isinstance(statement, str):
                    logger.info(f"[{problem_alias}] Statement content:")
                    logger.info("=" * 60)
                    logger.info(statement)
                    logger.info("=" * 60)
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch problem details: {str(e)}"
            logger.error(f"[{problem_alias}] {error_msg}")
            raise RuntimeError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response when fetching problem details: {str(e)}"
            logger.error(f"[{problem_alias}] {error_msg}")
            raise RuntimeError(error_msg)

class ProductionAI:
    """AI component for code and editorial generation in production."""

    def __init__(self):
        load_dotenv()
        
        # Try to import OpenAI
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.info("Using mock AI generation (no OpenAI API key)")
                self.client = None
            else:
                logger.info("Using OpenAI for code and editorial generation")
                self.client = OpenAI(api_key=api_key)
                
        except ImportError:
            logger.info("OpenAI library not installed, using mock AI generation")
            self.client = None
            
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def generate_solution_code(self, problem_data: dict, language: str = "py3", error_feedback: str = None) -> str:
        """Generate solution code for the problem."""
        
        problem_alias = problem_data.get('alias', 'unknown')
        title = problem_data.get('title', 'Unknown Problem')
        statement = problem_data.get('statement', {}).get('markdown', '')
        
        logger.info(f"[{problem_alias}] Generating solution code")
        logger.info(f"[{problem_alias}] Problem: {title}")
        logger.info(f"[{problem_alias}] Language: {language}")
        
        # Log problem details
        self._log_problem_details(problem_data)
        
        if error_feedback:
            logger.info(f"[{problem_alias}] Error feedback provided:")
            logger.info(f"   {error_feedback}")
        
        if self.client is None:
            return self._generate_mock_code(problem_alias, title, language)
        else:
            return self._generate_openai_code(problem_alias, title, statement, language, error_feedback)

    def _log_problem_details(self, problem_data: dict) -> None:
        """Log detailed problem information."""
        problem_alias = problem_data.get('alias', 'unknown')
        
        title = problem_data.get('title', 'Unknown')
        
        logger.info(f"[{problem_alias}] Title: {title}")
        
        # Log statement with proper multi-line formatting
        statement = problem_data.get('statement', {})
        markdown = statement.get('markdown', '')
        if markdown:
            logger.info(f"[{problem_alias}] Problem Statement ({len(markdown)} chars):")
            logger.info("=" * 60)
            # Split by lines and log each line separately to ensure proper display
            for line in markdown.split('\n'):
                logger.info(line)
            logger.info("=" * 60)
        
        # Log settings
        settings = problem_data.get('settings', {})
        if 'memory_limit' in settings:
            logger.info(f"[{problem_alias}] Memory Limit: {settings['memory_limit']} MB")
        if 'time_limit' in settings:
            logger.info(f"[{problem_alias}] Time Limit: {settings['time_limit']} ms")

    def _generate_mock_code(self, problem_alias: str, title: str, language: str) -> str:
        """Generate mock code for demonstration."""
        code = get_mock_code_template(title, language)
        
        logger.info(f"[{problem_alias}] Generated mock solution code ({len(code)} chars)")
        logger.info(f"[{problem_alias}] Generated code:")
        logger.info("=" * 60)
        # Log code line by line to ensure proper display
        for line in code.split('\n'):
            logger.info(line)
        logger.info("=" * 60)
        
        return code

    def _generate_openai_code(self, problem_alias: str, title: str, statement: str, language: str, error_feedback: str) -> str:
        """Generate code using OpenAI API."""
        
        prompt = get_code_generation_prompt(title, statement, language, error_feedback)

        try:
            logger.info(f"[{problem_alias}] Requesting code generation from OpenAI")
            logger.info(f"[{problem_alias}] Prompt ({len(prompt)} chars):")
            logger.info("=" * 60)
            # Log prompt line by line to ensure proper display
            for line in prompt.split('\n'):
                logger.info(line)
            logger.info("=" * 60)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": get_code_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            code = response.choices[0].message.content.strip()
            
            # Clean up the code (remove markdown formatting if present)
            if "```" in code:
                lines = code.split('\n')
                code_lines = []
                in_code = False
                for line in lines:
                    if line.startswith('```'):
                        in_code = not in_code
                        continue
                    if in_code:
                        code_lines.append(line)
                code = '\n'.join(code_lines)
            
            logger.info(f"[{problem_alias}] Generated OpenAI solution code ({len(code)} chars)")
            logger.info(f"[{problem_alias}] Generated code:")
            logger.info("=" * 60)
            # Log code line by line to ensure proper display
            for line in code.split('\n'):
                logger.info(line)
            logger.info("=" * 60)
            
            return code
            
        except Exception as e:
            logger.error(f"[{problem_alias}] OpenAI code generation failed: {str(e)}")
            return self._generate_mock_code(problem_alias, title, language)

    def generate_editorial(self, problem_data: dict, solution_code: str, verdict: str, score: float, language: str = "py3") -> str:
        """Generate editorial based on working solution."""
        
        problem_alias = problem_data.get('alias', 'unknown')
        title = problem_data.get('title', 'Unknown Problem')
        statement = problem_data.get('statement', {}).get('markdown', '')
        
        logger.info(f"[{problem_alias}] Generating editorial")
        logger.info(f"[{problem_alias}] Problem: {title}")
        logger.info(f"[{problem_alias}] Solution verdict: {verdict}")
        logger.info(f"[{problem_alias}] Solution score: {score}")
        logger.info(f"[{problem_alias}] Code length: {len(solution_code)} chars")
        
        if self.client is None:
            return self._generate_mock_editorial(problem_alias, title, solution_code, verdict, language)
        else:
            return self._generate_openai_editorial(problem_alias, title, statement, solution_code, verdict, language)

    def _generate_mock_editorial(self, problem_alias: str, title: str, solution_code: str, verdict: str, language: str) -> str:
        """Generate mock editorial."""
        editorial = get_mock_editorial_template(title, solution_code, verdict, language)
        
        logger.info(f"[{problem_alias}] Generated mock editorial ({len(editorial)} chars)")
        logger.info(f"[{problem_alias}] Generated editorial:")
        logger.info("=" * 60)
        # Log editorial line by line to ensure proper display
        for line in editorial.split('\n'):
            logger.info(line)
        logger.info("=" * 60)
        
        return editorial

    def _generate_openai_editorial(self, problem_alias: str, title: str, statement: str, solution_code: str, verdict: str, language: str) -> str:
        """Generate editorial using OpenAI API."""
        
        prompt = get_editorial_generation_prompt(title, statement, solution_code, verdict, language)

        try:
            logger.info(f"[{problem_alias}] Requesting editorial generation from OpenAI")
            logger.info(f"[{problem_alias}] Editorial prompt ({len(prompt)} chars):")
            logger.info("=" * 60)
            # Log prompt line by line to ensure proper display
            for line in prompt.split('\n'):
                logger.info(line)
            logger.info("=" * 60)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": get_editorial_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            editorial = response.choices[0].message.content.strip()
            
            logger.info(f"[{problem_alias}] Generated OpenAI editorial ({len(editorial)} chars)")
            logger.info(f"[{problem_alias}] Generated editorial:")
            logger.info("=" * 60)
            # Log editorial line by line to ensure proper display
            for line in editorial.split('\n'):
                logger.info(line)
            logger.info("=" * 60)
            
            return editorial
            
        except Exception as e:
            logger.error(f"[{problem_alias}] OpenAI editorial generation failed: {str(e)}")
            return self._generate_mock_editorial(problem_alias, title, solution_code, verdict, language)

class ProductionGrader:
    """Grader component for testing solutions using official omegaUp APIs."""

    def __init__(self, api):
        self.api = api

    def test_solution(self, problem_alias: str, code: str, language: str = "py3") -> dict:
        """
        Test solution using the official /api/run/create/ and /api/run/status/ endpoints.
        
        API Documentation:
        - /api/run/create/ - Submit code for testing
        - /api/run/status/ - Check submission status
        """
        
        logger.info(f"[{problem_alias}] Testing solution with production grader")
        logger.info(f"[{problem_alias}] Language: {language}")
        logger.info(f"[{problem_alias}] Code length: {len(code)} chars")
        
        try:
            # Submit solution using official API
            data = {
                'problem_alias': problem_alias,
                'language': language,
                'source': code
            }
            
            url = f"{self.api.api_url}/run/create"
            logger.info(f"[{problem_alias}] Submitting to production grader: {url}")
            
            response = self.api.session.post(url, data=data, timeout=(10, 30))
            
            logger.info(f"[{problem_alias}] Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"[{problem_alias}] HTTP Error {response.status_code}: {response.text}")
                return {}
            
            result = response.json()
            logger.info(f"[{problem_alias}] Submission response: {result}")
            
            if result.get("status") != "ok":
                logger.error(f"[{problem_alias}] Submission failed: {result.get('error', 'Unknown error')}")
                return {}
            
            guid = result.get('guid')
            logger.info(f"[{problem_alias}] Submission successful")
            logger.info(f"[{problem_alias}] GUID: {guid}")
            submit_delay = result.get('submit_delay', 0)
            if submit_delay > 0:
                logger.info(f"[{problem_alias}] Submit delay: {submit_delay} minutes")
            
            # Wait for result
            return self._wait_for_result(problem_alias, guid)
            
        except Exception as e:
            logger.error(f"[{problem_alias}] Solution testing failed: {str(e)}")
            return {}

    def _wait_for_result(self, problem_alias: str, run_guid: str, max_wait_time: int = 60) -> dict:
        """
        Wait for grading result using the official /api/run/status/ endpoint.
        
        API Documentation:
        - Endpoint: /api/run/status/
        - Parameter: run_alias (string) - The GUID of the run
        - Returns: Run status information
        """
        
        logger.info(f"[{problem_alias}] Waiting for grading result...")
        start_time = time.time()
        last_status = ""
        
        while time.time() - start_time < max_wait_time:
            try:
                url = f"{self.api.api_url}/run/status"
                params = {'run_alias': run_guid}
                
                logger.info(f"[{problem_alias}] Checking status: {url} with params: {params}")
                
                response = self.api.session.get(url, params=params, timeout=(10, 20))
                
                if response.status_code != 200:
                    logger.warning(f"[{problem_alias}] Status check HTTP {response.status_code}: {response.text}")
                    time.sleep(3)
                    continue
                
                result = response.json()
                
                if 'guid' in result and result['guid'] == run_guid:
                    status = result.get('status', 'unknown')
                    verdict = result.get('verdict', 'unknown')
                    
                    # Log status changes
                    if status != last_status:
                        logger.info(f"[{problem_alias}] Status: {status} | Verdict: {verdict}")
                        last_status = status
                    
                    if status in ['ready', 'done']:
                        logger.info(f"[{problem_alias}] Grading completed")
                        logger.info(f"[{problem_alias}] Final Verdict: {verdict}")
                        logger.info(f"[{problem_alias}] Score: {result.get('score', 0.0)}")
                        
                        runtime = result.get('runtime', 0)
                        memory = result.get('memory', 0)
                        if runtime > 0:
                            logger.info(f"[{problem_alias}] Runtime: {runtime}ms")
                        if memory > 0:
                            logger.info(f"[{problem_alias}] Memory: {memory}KB")
                        
                        execution = result.get('execution', '')
                        if execution:
                            logger.info(f"[{problem_alias}] Execution: {execution}")
                        output = result.get('output', '')
                        if output:
                            logger.info(f"[{problem_alias}] Output: {output}")
                        
                        return result
                    
                    if status in ['error', 'compile_error']:
                        logger.error(f"[{problem_alias}] Grading error")
                        logger.error(f"[{problem_alias}] Status: {status}")
                        logger.error(f"[{problem_alias}] Verdict: {verdict}")
                        
                        execution = result.get('execution', '')
                        if execution:
                            logger.error(f"[{problem_alias}] Execution: {execution}")
                        output = result.get('output', '')
                        if output:
                            logger.error(f"[{problem_alias}] Output: {output}")
                        
                        return result
                else:
                    logger.warning(f"[{problem_alias}] Status response doesn't match GUID: {result}")
                
                time.sleep(3)
                
            except Exception as e:
                logger.warning(f"[{problem_alias}] Status check failed: {str(e)}")
                time.sleep(3)
        
        logger.warning(f"[{problem_alias}] Grading timeout - no result received after {max_wait_time}s")
        return {}

class ProductionDemo:
    """Production demo orchestrator using official APIs."""

    def __init__(self):
        logger.info("Initializing Production Editorial Generator")
        self.api = ProductionOmegaUpAPI()
        self.ai = ProductionAI()
        self.grader = ProductionGrader(self.api)
        logger.info("Production Editorial Generator ready")

    def run_solution_workflow(self, problem_alias: str, language: str = "py3") -> bool:
        """Complete workflow: fetch problem, generate code, test with grader, generate editorial, and upload editorial."""
        
        logger.info("=" * 80)
        logger.info(f"[{problem_alias}] STARTING COMPLETE EDITORIAL WORKFLOW")
        logger.info("=" * 80)
        logger.info(f"[{problem_alias}] Problem alias: {problem_alias}")
        logger.info(f"[{problem_alias}] Language: {language}")
        logger.info("=" * 80)
        
        try:
            # Step 1: Fetch problem details
            logger.info(f"[{problem_alias}] STEP 1: FETCHING PROBLEM DETAILS")
            logger.info("-" * 40)
            
            problem_data = self.api.get_problem_details(problem_alias)
            
            if not problem_data:
                logger.error(f"[{problem_alias}] Failed to fetch problem details")
                return False
            
            # Step 2: Generate solution code
            logger.info("")
            logger.info(f"[{problem_alias}] STEP 2: GENERATING SOLUTION CODE")
            logger.info("-" * 40)
            
            solution_code = self.ai.generate_solution_code(problem_data, language)
            
            if not solution_code:
                logger.error(f"[{problem_alias}] Failed to generate solution code")
                return False
            
            # Step 3: Test solution with grader
            logger.info("")
            logger.info(f"[{problem_alias}] STEP 3: TESTING SOLUTION WITH GRADER")
            logger.info("-" * 40)
            
            test_result = self.grader.test_solution(problem_alias, solution_code, language)
            
            if not test_result:
                logger.error(f"[{problem_alias}] Failed to test solution with grader")
                return False
                
            verdict = test_result.get('verdict', 'Unknown')
            score = test_result.get('score', 0)
            
            # Step 4: Handle result
            if verdict == 'AC':
                logger.info("")
                logger.info(f"[{problem_alias}] 🎉 SOLUTION ACCEPTED!")
                logger.info("-" * 40)
                logger.info(f"[{problem_alias}] Solution accepted on first try")
                
                # Step 5: Generate editorial based on AC solution
                logger.info("")
                logger.info(f"[{problem_alias}] STEP 4: GENERATING EDITORIAL")
                logger.info("-" * 40)
                
                editorial = self.ai.generate_editorial(problem_data, solution_code, verdict, score, language)
                
                if not editorial:
                    logger.error(f"[{problem_alias}] Failed to generate editorial")
                    return False
                
                # Step 6: Upload editorial to omegaUp
                logger.info("")
                logger.info(f"[{problem_alias}] STEP 5: UPLOADING EDITORIAL")
                logger.info("-" * 40)
                
                upload_success = self.upload_editorial(problem_alias, editorial)
                
                if upload_success:
                    logger.info("")
                    logger.info("=" * 80)
                    logger.info(f"[{problem_alias}] COMPLETE WORKFLOW SUCCESS!")
                    logger.info("=" * 80)
                    logger.info(f"[{problem_alias}] FINAL SUMMARY:")
                    logger.info(f"   Problem: {problem_data.get('title', problem_alias)}")
                    logger.info(f"   Final verdict: {verdict}")
                    logger.info(f"   Final score: {score}")
                    logger.info(f"   Code length: {len(solution_code)} characters")
                    logger.info(f"   Editorial length: {len(editorial)} characters")
                    logger.info(f"   Editorial uploaded: ✅ SUCCESS")
                    logger.info("=" * 80)
                    return True
                else:
                    logger.error(f"[{problem_alias}] Editorial upload failed")
                    return False
                
            else:
                logger.warning(f"[{problem_alias}] Solution not accepted: {verdict}")
                logger.info(f"[{problem_alias}] Attempting to regenerate with feedback...")
                
                # Step 4b: Try regenerating with error feedback
                error_feedback = f"Previous solution got verdict: {verdict} with score: {score}"
                retry_code = self.ai.generate_solution_code(problem_data, language, error_feedback)
                
                if retry_code:
                    logger.info(f"[{problem_alias}] Testing regenerated solution...")
                    retry_result = self.grader.test_solution(problem_alias, retry_code, language)
                    
                    if retry_result:
                        retry_verdict = retry_result.get('verdict', 'Unknown')
                        retry_score = retry_result.get('score', 0)
                        
                        # Use the better solution
                        if retry_verdict == 'AC':
                            logger.info("")
                            logger.info(f"[{problem_alias}] 🎉 RETRY SOLUTION ACCEPTED!")
                            logger.info("-" * 40)
                            logger.info(f"[{problem_alias}] Solution accepted after regeneration")
                            
                            # Generate editorial based on AC retry solution
                            logger.info("")
                            logger.info(f"[{problem_alias}] STEP 4: GENERATING EDITORIAL")
                            logger.info("-" * 40)
                            
                            editorial = self.ai.generate_editorial(problem_data, retry_code, retry_verdict, retry_score, language)
                            
                            if editorial:
                                # Upload editorial to omegaUp
                                logger.info("")
                                logger.info(f"[{problem_alias}] STEP 5: UPLOADING EDITORIAL")
                                logger.info("-" * 40)
                                
                                upload_success = self.upload_editorial(problem_alias, editorial)
                                
                                if upload_success:
                                    logger.info("")
                                    logger.info("=" * 80)
                                    logger.info(f"[{problem_alias}] COMPLETE WORKFLOW SUCCESS!")
                                    logger.info("=" * 80)
                                    logger.info(f"[{problem_alias}] FINAL SUMMARY:")
                                    logger.info(f"   Problem: {problem_data.get('title', problem_alias)}")
                                    logger.info(f"   Final verdict: {retry_verdict} (after retry)")
                                    logger.info(f"   Final score: {retry_score}")
                                    logger.info(f"   Code length: {len(retry_code)} characters")
                                    logger.info(f"   Editorial length: {len(editorial)} characters")
                                    logger.info(f"   Editorial uploaded: ✅ SUCCESS")
                                    logger.info("=" * 80)
                                    return True
                                else:
                                    logger.error(f"[{problem_alias}] Editorial upload failed")
                                    return False
                        else:
                            logger.error(f"[{problem_alias}] Both attempts failed. First: {verdict}, Retry: {retry_verdict}")
                            return False
                
                logger.error(f"[{problem_alias}] Unable to get AC solution")
                return False
                
        except Exception as e:
            logger.error(f"[{problem_alias}] Workflow failed: {str(e)}")
            return False

    def upload_editorial(self, problem_alias: str, editorial_content: str, commit_message: str = None) -> bool:
        """
        Upload editorial to omegaUp using the official /api/problem/updateSolution/ endpoint.
        """
        try:
            logger.info(f"[{problem_alias}] Uploading editorial to omegaUp")
            logger.info(f"[{problem_alias}] Editorial content length: {len(editorial_content)} chars")
            
            if commit_message is None:
                commit_message = f"Updated editorial via Production Editorial Generator on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            logger.info(f"[{problem_alias}] Commit message: {commit_message}")
            
            # Prepare data for the API call
            data = {
                'problem_alias': problem_alias,
                'solution': editorial_content,
                'message': commit_message,
                'lang': 'markdown'
            }
            
            url = f"{self.api.api_url}/problem/updateSolution"
            logger.info(f"POST {url}")
            
            # Log the data being sent (but truncate content for readability)
            log_data = data.copy()
            if len(log_data['solution']) > 200:
                log_data['solution'] = log_data['solution'][:200] + f"... (total {len(data['solution'])} chars)"
            logger.info(f"Request data: {log_data}")
            
            response = self.api.session.post(url, data=data, timeout=(10, 60))
            
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
                logger.info(f"[{problem_alias}] Editorial uploaded successfully!")
                return True
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"[{problem_alias}] Editorial upload failed: {error_msg}")
                return False
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Editorial upload request failed: {str(e)}"
            logger.error(f"[{problem_alias}] {error_msg}")
            return False

def main():
    """Main function to run production solution generation and testing."""
    
    if len(sys.argv) < 2:
        print("Usage: python prod_demo.py <problem_alias1> [problem_alias2] ... [language]")
        print("       python prod_demo.py --file <filename> [language]")
        print("       python prod_demo.py -f <filename> [language]")
        print("")
        print("Examples:")
        print("  Single problem:")
        print("    python prod_demo.py sumas")
        print("    python prod_demo.py sumas py3")
        print("    python prod_demo.py aplusb cpp17-gcc")
        print("")
        print("  Multiple problems (command line):")
        print("    python prod_demo.py sumas aplusb Product-of-Three-Numbers")
        print("    python prod_demo.py sumas aplusb py3")
        print("    python prod_demo.py problem1 problem2 problem3 cpp17-gcc")
        print("")
        print("  Multiple problems (from file):")
        print("    python prod_demo.py --file problems.txt")
        print("    python prod_demo.py -f problems.txt py3")
        print("    python prod_demo.py --file my_problems.txt cpp17-gcc")
        print("")
        print("File format (one problem alias per line):")
        print("    sumas")
        print("    aplusb")
        print("    Product-of-Three-Numbers")
        print("    fibonacci")
        print("")
        print("This will:")
        print("  1. Fetch problem details from production API")
        print("  2. Generate solution code using AI")
        print("  3. Test solution with production grader")
        print("  4. Generate editorial based on working solution")
        print("  5. Upload editorial to omegaUp")
        print("  6. Repeat for all problems")
        return 1
    
    # Parse arguments: check for file input
    known_languages = ['py3', 'py2', 'cpp17-gcc', 'cpp17-clang', 'cpp20-gcc', 'cpp20-clang', 
                      'c11-gcc', 'c11-clang', 'java', 'cs', 'go', 'rs', 'js', 'kt', 'rb', 'lua', 'hs', 'pas']
    
    args = sys.argv[1:]
    language = "py3"  # default
    problem_aliases = []
    
    # Check if reading from file
    if args[0] in ['--file', '-f']:
        if len(args) < 2:
            print("Error: --file option requires a filename")
            return 1
        
        filename = args[1]
        
        # Check if there's a language specified after the filename
        if len(args) > 2 and args[2].lower() in known_languages:
            language = args[2].lower()
        
        # Read problems from file
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Parse file content
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    problem_aliases.append(line)
            
            if not problem_aliases:
                print(f"Error: No valid problem aliases found in {filename}")
                return 1
                
            print(f"📁 Loaded {len(problem_aliases)} problems from {filename}")
            
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found")
            return 1
        except Exception as e:
            print(f"Error reading file '{filename}': {str(e)}")
            return 1
    
    else:
        # Parse command line arguments (existing logic)
        # Check if last argument is a language
        if len(args) > 1 and args[-1].lower() in known_languages:
            language = args[-1].lower()
            problem_aliases = args[:-1]
        else:
            problem_aliases = args
    
    # Validate we have at least one problem
    if not problem_aliases:
        print("Error: At least one problem alias must be provided")
        return 1
    
    try:
        logger.info("Starting Production Editorial Generator")
        
        if len(problem_aliases) == 1:
            logger.info(f"Target problem: {problem_aliases[0]}")
        else:
            logger.info(f"Target problems: {', '.join(problem_aliases)} ({len(problem_aliases)} total)")
        
        logger.info(f"Language: {language}")
        
        # Initialize demo once for all problems
        demo = ProductionDemo()
        
        # Track results
        successful_problems = []
        failed_problems = []
        
        # Process each problem
        for i, problem_alias in enumerate(problem_aliases, 1):
            if len(problem_aliases) > 1:
                logger.info("")
                logger.info("🔄" * 50)
                logger.info(f"PROCESSING PROBLEM {i}/{len(problem_aliases)}: {problem_alias}")
                logger.info("🔄" * 50)
            
            try:
                success = demo.run_solution_workflow(problem_alias, language)
                
                if success:
                    successful_problems.append(problem_alias)
                    logger.info(f"✅ {problem_alias}: SUCCESS")
                else:
                    failed_problems.append(problem_alias)
                    logger.error(f"❌ {problem_alias}: FAILED")
                    
            except Exception as e:
                failed_problems.append(problem_alias)
                logger.error(f"❌ {problem_alias}: ERROR - {str(e)}")
            
            # Add delay between problems to avoid rate limiting
            if i < len(problem_aliases):
                logger.info(f"Waiting 2 seconds before next problem...")
                time.sleep(2)
        
        # Final summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("BULK PROCESSING SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total problems processed: {len(problem_aliases)}")
        logger.info(f"Successful: {len(successful_problems)}")
        logger.info(f"Failed: {len(failed_problems)}")
        
        if successful_problems:
            logger.info(f"✅ Successful problems: {', '.join(successful_problems)}")
        
        if failed_problems:
            logger.info(f"❌ Failed problems: {', '.join(failed_problems)}")
        
        logger.info("=" * 80)
        
        # Print summary for user
        if len(problem_aliases) == 1:
            if successful_problems:
                print(f"✅ Successfully generated editorial for: {problem_aliases[0]}")
                return 0
            else:
                print(f"❌ Failed to generate editorial for: {problem_aliases[0]}")
                return 1
        else:
            print(f"📊 Bulk processing completed:")
            print(f"   ✅ Successful: {len(successful_problems)}/{len(problem_aliases)}")
            print(f"   ❌ Failed: {len(failed_problems)}/{len(problem_aliases)}")
            
            if successful_problems:
                print(f"   ✅ Success: {', '.join(successful_problems)}")
            
            if failed_problems:
                print(f"   ❌ Failed: {', '.join(failed_problems)}")
            
            # Return 0 if at least some succeeded, 1 if all failed
            return 0 if successful_problems else 1
            
    except Exception as e:
        logger.error(f"Production demo failed: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 