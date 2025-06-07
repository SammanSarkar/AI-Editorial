#!/usr/bin/env python3
"""
AC Tester for omegaUp Quality Problems
Tests AI-generated solutions against omegaUp grader to measure success rates.
"""

import sys
import os
import json
import logging
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI

# Setup logging
def setup_logging():
    """Setup logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"ac_tester_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class ACTester:
    """Tests AI-generated solutions for AC status on omegaUp problems."""

    def __init__(self):
        load_dotenv()
        
        # API Configuration
        self.api_url = os.getenv("OMEGAUP_API_URL", "https://omegaup.com/api")
        self.base_url = os.getenv("OMEGAUP_BASE_URL", "https://omegaup.com")
        
        # Initialize OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in .env file")
        self.openai_client = OpenAI(api_key=api_key)
        
        # Initialize session for persistent connections and cookies
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'omegaUp-AC-Tester/1.0',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8'
        })
        
        # Login for authenticated access
        self._login()
        
        # Statistics tracking
        self.stats = {
            'total_problems': 0,
            'successful_problems': 0,  # AC only
            'partial_problems': 0,     # PA (partial acceptance)
            'failed_problems': 0,      # Everything else
            'ac_first_try': 0,
            'ac_second_try': 0,
            'pa_first_try': 0,         # PA on first try
            'pa_second_try': 0,        # PA on second try
            'no_ac_achieved': 0,
            'api_errors': 0,
            'karel_skipped': 0,        # Karel problems skipped
            'karel_problem_names': [], # Names of Karel problems skipped
            'problem_results': []
        }
        
        logger.info("AC Tester initialized successfully")

    def _login(self) -> None:
        """Authenticate with omegaUp using the official /api/user/login/ endpoint."""
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
            response = self.session.post(url, data=login_data, timeout=(10, 30))
            
            if response.status_code != 200:
                raise RuntimeError(f"Authentication failed with status {response.status_code}")
                
            result = response.json()
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

    def get_problem_details(self, problem_alias: str) -> Optional[Dict[str, Any]]:
        """Fetch problem details from omegaUp API."""
        try:
            url = f"{self.api_url}/problem/details"
            params = {'problem_alias': problem_alias}
            
            response = self.session.get(url, params=params, timeout=(10, 30))
            
            if response.status_code != 200:
                logger.error(f"HTTP Error {response.status_code} for problem {problem_alias}")
                return None
                
            result = response.json()
            if result.get("status") == "ok":
                return result
            else:
                logger.error(f"API error for {problem_alias}: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch problem details for {problem_alias}: {str(e)}")
            return None

    def generate_solution_code(self, problem_details: Dict[str, Any], language: str = "cpp17-gcc", 
                             previous_error: Optional[str] = None, attempt: int = 1, previous_code: Optional[str] = None) -> Optional[str]:
        """Generate solution code using OpenAI GPT-4."""
        try:
            problem_statement = problem_details.get('statement', {}).get('markdown', '')
            problem_title = problem_details.get('title', 'Unknown Problem')
            
            if not problem_statement.strip():
                logger.error("Empty problem statement")
                return None
            
            # Create prompt based on language and attempt
            if language == "kj":  # Karel Java
                if attempt == 1:
                    prompt = f"""You are an expert Karel programming assistant. You are rated 2900+ in Karel programming and you are very smart with Karel programming complex problems. Generate a complete, working Karel Java solution for this omegaUp Karel problem.

Problem Title: {problem_title}

Problem Statement:
{problem_statement}

Requirements:
- Language: Karel Java (kj)
- This is a Karel programming problem for omegaUp platform
- Write efficient Karel Java code following Karel programming conventions
- Use proper Karel Java syntax and commands
- Handle all movement, beeper collection/placement as specified in the problem
- Include proper control structures (if, while, for) as needed
- Use Karel Java methods like move(), turnLeft(), pickBeeper(), putBeeper(), etc.
- Follow Karel programming best practices
- Code should compile and run correctly on omegaUp Karel judge
- Use proper Karel Java class structure with main method

Provide ONLY the complete Karel Java source code without any explanations, comments, or markdown formatting."""
                else:
                    prompt = f"""You are an expert Karel programmer. You are rated 2900+ in Karel programming and you are very smart with Karel programming complex problems. Your previous Karel Java solution for this omegaUp Karel problem failed. Generate a CORRECTED, working Karel Java solution.

Problem Title: {problem_title}

Problem Statement:
{problem_statement}

*IMPORTANT* ANALYZE THE ERROR AND FIX THE KAREL ISSUES:
- Look at the error/verdict carefully
- Check if it's a Karel runtime error, wrong movement, beeper handling error, etc.
- If runtime error: check for wall collisions, beeper availability, infinite loops
- If wrong answer: check Karel's movement pattern, beeper collection/placement logic
- Understand WHY THE PREVIOUS KAREL CODE FAILED AND FIX IT

*IMPORTANT* PREVIOUS ATTEMPT FAILED WITH THE FOLLOWING ERROR:
{previous_error}

*IMPORTANT* YOUR PREVIOUS KAREL CODE THAT FAILED (FIX THIS CODE):
```kj
{previous_code}
```

Requirements:
- Language: Karel Java (kj)
- This is a Karel programming problem for omegaUp platform
- Fix the issues from the previous attempt
- Write efficient Karel Java code following Karel programming conventions
- Use proper Karel Java syntax and commands
- Handle all movement, beeper collection/placement as specified in the problem
- Include proper control structures (if, while, for) as needed
- Use Karel Java methods like move(), turnLeft(), pickBeeper(), putBeeper(), etc.
- Follow Karel programming best practices

Provide ONLY the complete corrected Karel Java source code without any explanations, comments, or markdown formatting."""
                
                system_message = "You are an expert Karel programming assistant specializing in omegaUp Karel problems and Karel Java (kj). You are rated 2900+ in Karel programming and you are very smart with Karel programming complex problems."
                
            else:  # C++17 or other languages
                if attempt == 1:
                    prompt = f"""You are an expert competitive programming assistant. You are rated 2900+ in codeforces and u are very smart with competitive programming complex question that require complex concepts. Generate a complete, working solution for this omegaUp competitive programming problem.

Problem Title: {problem_title}

Problem Statement:
{problem_statement}

Requirements:
- Language: {language} (C++17)
- IMPORTANT - be careful of Time Complexity and Memory Usage
- This is for omegaUp competitive programming platform
- Write efficient, competitive programming style code
- Handle all edge cases mentioned in the problem
- Use appropriate data structures and algorithms for competitive programming
- Include proper input/output handling (typically stdin/stdout)
- Code should compile and run correctly on omegaUp judge
- Use #include <bits/stdc++.h> for convenience
- Use fast I/O: ios_base::sync_with_stdio(false); cin.tie(NULL);
- Follow competitive programming best practices

Provide ONLY the complete source code without any explanations, comments, or markdown formatting."""
                else:
                    prompt = f"""You are an expert competitive programmer. You are rated 2900+ in codeforces and u are very smart with competitive programming complex question that require complex concepts. Your previous solution for this omegaUp problem failed. Generate a CORRECTED, working solution.

Problem Title: {problem_title}

Problem Statement:
{problem_statement}

*IMPORTANT* ANALYZE THE ERROR AND FIX THE ISSUES:
- Look at the error/verdict carefully
- Check if it's a Time Limit Exceeded (TLE), Wrong Answer (WA), Runtime Error (RTE), etc.
- If TLE: optimize time complexity, use more efficient algorithms
- If WA: check logic, edge cases, input/output format
- If RTE: check for array bounds, division by zero, etc.
-UNDERSTAND WHY THE PREVIOUS CODE FAILED AND FIX IT BY LOOKING AT THE PROBLEM STATEMENT AND THE ERROR

*IMPORTANT* PREVIOUS ATTEMPT FAILED WITH THE FOLLOWING ERROR:
{previous_error}

*IMPORTANT* YOUR PREVIOUS CODE THAT FAILED (FIX THIS CODE):
```{language}
{previous_code}
```

Requirements:
- Language: {language} (C++17)
- IMPORTANT - be careful of Time Complexity and Memory Usage
- This is for omegaUp competitive programming platform
- Fix the issues from the previous attempt
- Write efficient, competitive programming style code
- Handle all edge cases mentioned in the problem
- Use appropriate data structures and algorithms for competitive programming
- Include proper input/output handling (typically stdin/stdout)
- Code should compile and run correctly on omegaUp judge
- Use #include <bits/stdc++.h> for convenience
- Use fast I/O: ios_base::sync_with_stdio(false); cin.tie(NULL);

Provide ONLY the complete corrected source code without any explanations, comments, or markdown formatting."""
                
                system_message = "You are an expert competitive programming assistant specializing in omegaUp problems and C++17. You are rated 2900+ in codeforces and u are very smart with competitive programming complex question that require complex concepts."

            logger.info(f"Generating {language} solution (attempt {attempt}) using OpenAI GPT-4...")
            
            # Log the complete prompt being sent
            logger.info("=" * 80)
            logger.info("PROMPT BEING SENT TO OPENAI:")
            logger.info("=" * 80)
            for line in prompt.split('\n'):
                logger.info(line)
            logger.info("=" * 80)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            generated_code = response.choices[0].message.content.strip()
            
            # Clean up the code (remove markdown formatting if any)
            if generated_code.startswith('```'):
                lines = generated_code.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                generated_code = '\n'.join(lines)
            
            logger.info(f"Generated solution code ({len(generated_code)} characters)")
            logger.info("=" * 80)
            logger.info("GENERATED CODE:")
            logger.info("=" * 80)
            for line in generated_code.split('\n'):
                logger.info(line)
            logger.info("=" * 80)
            
            return generated_code
            
        except Exception as e:
            logger.error(f"Failed to generate solution code: {str(e)}")
            return None

    def submit_solution(self, problem_alias: str, language: str, source_code: str, wait_before_submit: bool = False) -> Optional[Tuple[str, str]]:
        """Submit solution to omegaUp grader and return tuple of (run_guid, actual_language_used)."""
        try:
            # Wait before submission if this is a retry to same problem
            if wait_before_submit:
                logger.info("Waiting 60 seconds before retry submission due to omegaUp rate limit...")
                time.sleep(60)
            
            url = f"{self.api_url}/run/create"
            
            data = {
                'problem_alias': problem_alias,
                'language': language,
                'source': source_code
            }
            
            logger.info(f"Submitting solution to {url}")
            logger.info(f"Data: problem_alias={problem_alias}, language={language}, source_length={len(source_code)}")
            
            response = self.session.post(url, data=data, timeout=(10, 30))
            
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Submission failed with status {response.status_code}")
                logger.error(f"Response text: {response.text}")
                
                # Check if this is a language compatibility error
                try:
                    error_response = response.json()
                    if (error_response.get("errorname") == "parameterNotInExpectedSet" and 
                        error_response.get("parameter") == "language"):
                        
                        error_msg = error_response.get("error", "")
                        logger.info(f"Language compatibility error detected: {error_msg}")
                        
                        # Check if Karel Java (kj) is supported
                        if "kj" in error_msg or "kp" in error_msg:
                            logger.info(f"Problem {problem_alias} only supports Karel languages. SKIPPING this problem.")
                            return ("KAREL_SKIP", "kj")  # Special return to indicate Karel skip
                        
                except json.JSONDecodeError:
                    pass
                
                return None
                
            result = response.json()
            logger.info(f"API Response: {result}")
            
            if result.get("status") == "ok":
                run_guid = result.get("guid")
                logger.info(f"Solution submitted successfully. Run GUID: {run_guid}")
                return (run_guid, language)  # Return run_guid and original language
            else:
                error_msg = result.get('error', 'Unknown submission error')
                logger.error(f"Submission failed: {error_msg}")
                logger.error(f"Full response: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to submit solution: {str(e)}")
            return None

    def check_run_status(self, run_guid: str, max_wait_time: int = 60) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Check run status and return (verdict, score, feedback)."""
        try:
            url = f"{self.api_url}/run/status"
            start_time = time.time()
            last_status = ""
            
            while time.time() - start_time < max_wait_time:
                params = {'run_alias': run_guid}
                response = self.session.get(url, params=params, timeout=(10, 30))
                
                if response.status_code != 200:
                    logger.error(f"Status check failed with status {response.status_code}")
                    time.sleep(2)
                    continue
                    
                result = response.json()
                
                # Check if this is a valid response for our run
                if 'guid' in result and result['guid'] == run_guid:
                    status = result.get('status', 'unknown')
                    verdict = result.get('verdict', 'unknown').upper()
                    score = result.get('score', 0)
                    
                    # Log status changes
                    if status != last_status:
                        logger.info(f"Status: {status} | Verdict: {verdict}")
                        last_status = status
                    
                    # Check if grading is complete
                    if status in ['ready', 'done']:
                        logger.info(f"Grading completed with verdict: {verdict}, score: {score}")
                        
                        # Get feedback info
                        execution = result.get('execution', '')
                        output = result.get('output', '')
                        compile_error = result.get('compile_error', '')
                        
                        feedback = execution or output or compile_error or ""
                        
                        return verdict, str(score), feedback
                    
                    # Check for errors
                    if status in ['error', 'compile_error']:
                        logger.error(f"Grading error - Status: {status}, Verdict: {verdict}")
                        
                        execution = result.get('execution', '')
                        output = result.get('output', '')
                        compile_error = result.get('compile_error', '')
                        
                        feedback = execution or output or compile_error or ""
                        
                        return verdict, str(score), feedback
                        
                else:
                    logger.warning(f"Status response doesn't match GUID or has unexpected format: {result}")
                
                time.sleep(3)
            
            logger.warning("Run status check timed out")
            return "TIMEOUT", "0", "Status check timed out"
            
        except Exception as e:
            logger.error(f"Failed to check run status: {str(e)}")
            return None, None, str(e)

    def test_problem(self, problem_alias: str, language: str = "cpp17-gcc") -> Dict[str, Any]:
        """Test a single problem with AI-generated solution (with retry)."""
        result = {
            'problem_alias': problem_alias,
            'language': language,
            'actual_language': language,  # Track actual language used (may change to Karel)
            'first_try': {'verdict': None, 'score': None, 'code_length': 0},
            'second_try': {'verdict': None, 'score': None, 'code_length': 0},
            'final_verdict': None,
            'final_score': None,
            'success': False,
            'attempts': 0,
            'karel_fallback': False,  # Track if Karel problem was skipped
            'error': None
        }
        
        logger.info(f"Testing problem: {problem_alias}")
        
        # Get problem details
        problem_details = self.get_problem_details(problem_alias)
        if not problem_details:
            result['error'] = "Failed to fetch problem details"
            return result
        
        problem_title = problem_details.get('title', 'Unknown')
        logger.info(f"Problem title: {problem_title}")
        
        # First attempt
        logger.info("=== FIRST ATTEMPT ===")
        code1 = self.generate_solution_code(problem_details, language, attempt=1)
        if not code1:
            result['error'] = "Failed to generate solution code"
            return result
        
        result['first_try']['code_length'] = len(code1)
        result['attempts'] = 1
        
        submission_result1 = self.submit_solution(problem_alias, language, code1, wait_before_submit=False)
        if not submission_result1:
            result['error'] = "Failed to submit first solution"
            return result
        
        run_guid1, actual_language1 = submission_result1
        
        # Check if this is a Karel skip
        if run_guid1 == "KAREL_SKIP":
            result['karel_fallback'] = True
            result['error'] = "Karel-only problem skipped"
            result['final_verdict'] = "KAREL_SKIP"
            logger.info(f"KAREL SKIP: Problem {problem_alias} requires Karel language - skipping")
            return result
        
        result['actual_language'] = actual_language1
        
        verdict1, score1, feedback1 = self.check_run_status(run_guid1)
        if verdict1 is None:
            result['error'] = "Failed to check first run status"
            return result
        
        result['first_try']['verdict'] = verdict1
        result['first_try']['score'] = score1
        
        if verdict1 == "AC":
            result['final_verdict'] = verdict1
            result['final_score'] = score1
            result['success'] = True
            logger.info(f"SUCCESS: AC achieved on first try!")
            return result
        
        logger.info(f"FAILED: First attempt failed: {verdict1} (score: {score1})")
        
        # Second attempt with error feedback
        logger.info("=== SECOND ATTEMPT ===")
        error_info = f"Previous verdict: {verdict1}, Score: {score1}"
        if feedback1:
            error_info += f"\nFeedback: {feedback1}"
        
        # Use the actual language from the first attempt (might be Karel if fallback occurred)
        second_attempt_language = result['actual_language']
        
        code2 = self.generate_solution_code(problem_details, second_attempt_language, error_info, attempt=2, previous_code=code1)
        if not code2:
            result['error'] = "Failed to generate second solution"
            result['final_verdict'] = verdict1
            result['final_score'] = score1
            return result
        
        result['second_try']['code_length'] = len(code2)
        result['attempts'] = 2
        
        submission_result2 = self.submit_solution(problem_alias, second_attempt_language, code2, wait_before_submit=True)
        if not submission_result2:
            result['error'] = "Failed to submit second solution"
            result['final_verdict'] = verdict1
            result['final_score'] = score1
            return result
        
        run_guid2, actual_language2 = submission_result2
        
        verdict2, score2, feedback2 = self.check_run_status(run_guid2)
        if verdict2 is None:
            result['error'] = "Failed to check second run status"
            result['final_verdict'] = verdict1
            result['final_score'] = score1
            return result
        
        result['second_try']['verdict'] = verdict2
        result['second_try']['score'] = score2
        result['final_verdict'] = verdict2
        result['final_score'] = score2
        
        if verdict2 == "AC":
            result['success'] = True
            logger.info(f"SUCCESS: AC achieved on second try!")
        else:
            logger.info(f"FAILED: Second attempt also failed: {verdict2} (score: {score2})")
        
        return result

    def load_problems_from_file(self, filename: str) -> List[str]:
        """Load problem aliases from text file."""
        try:
            filepath = Path(filename)
            if not filepath.exists():
                logger.error(f"File not found: {filename}")
                return []
            
            problems = []
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        problems.append(line)
            
            logger.info(f"Loaded {len(problems)} problems from {filename}")
            return problems
            
        except Exception as e:
            logger.error(f"Failed to load problems from file: {str(e)}")
            return []

    def run_bulk_test(self, problems: List[str], language: str = "cpp17-gcc") -> None:
        """Run AC test on multiple problems and track statistics."""
        self.stats['total_problems'] = len(problems)
        
        logger.info("=" * 80)
        logger.info("STARTING BULK AC TESTING")
        logger.info("=" * 80)
        logger.info(f"Total problems to test: {len(problems)}")
        logger.info(f"Language: {language}")
        logger.info("NOTE: Each submission has 60-second rate limit - this will take time!")
        estimated_time = len(problems) * 2 * 60 / 60  # 2 submissions per problem * 60 sec / 60 min
        logger.info(f"Estimated time: ~{estimated_time:.1f} hours for {len(problems)} problems")
        logger.info("=" * 80)
        
        for i, problem_alias in enumerate(problems, 1):
            logger.info(f"\n[{i}/{len(problems)}] Testing: {problem_alias}")
            logger.info("-" * 60)
            
            try:
                result = self.test_problem(problem_alias, language)
                
                # Update statistics
                self.stats['problem_results'].append(result)
                
                if result.get('error'):
                    if result.get('karel_fallback'):
                        # Karel problem skipped
                        self.stats['karel_skipped'] += 1
                        self.stats['karel_problem_names'].append(problem_alias)
                        logger.info(f"KAREL SKIP: {problem_alias} - Karel-only problem skipped")
                    else:
                        # Other API/system errors
                        self.stats['api_errors'] += 1
                        logger.error(f"ERROR: {result['error']}")
                elif result['success']:
                    # AC achieved
                    self.stats['successful_problems'] += 1
                    if result['attempts'] == 1:
                        self.stats['ac_first_try'] += 1
                    else:
                        self.stats['ac_second_try'] += 1
                    logger.info(f"SUCCESS (AC): {result['final_verdict']} in {result['attempts']} attempt(s)")
                else:
                    # Check if we got partial acceptance (PA)
                    final_verdict = result.get('final_verdict', '')
                    if final_verdict == 'PA':
                        self.stats['partial_problems'] += 1
                        if result['attempts'] == 1:
                            self.stats['pa_first_try'] += 1
                        else:
                            self.stats['pa_second_try'] += 1
                        logger.info(f"PARTIAL: {result['final_verdict']} in {result['attempts']} attempt(s)")
                    else:
                        # Complete failure
                        self.stats['failed_problems'] += 1
                        self.stats['no_ac_achieved'] += 1
                        logger.info(f"FAILED: {result['final_verdict']} after {result['attempts']} attempts")
                
                # No additional delay needed here since submit_solution() already handles the 60s wait
                logger.info(f"Completed {i}/{len(problems)} problems")
                
                # Print intermediate progress every 10 problems
                if i % 10 == 0:
                    current_success = self.stats['successful_problems']
                    logger.info(f"PROGRESS UPDATE: {current_success}/{i} successful so far ({current_success/i*100:.1f}%)")
                    
            except Exception as e:
                logger.error(f"Unexpected error testing {problem_alias}: {str(e)}")
                self.stats['api_errors'] += 1
        
        self._print_final_statistics()

    def _print_final_statistics(self) -> None:
        """Print comprehensive final statistics."""
        logger.info("\n" + "=" * 80)
        logger.info("FINAL STATISTICS")
        logger.info("=" * 80)
        
        raw_total = self.stats['total_problems']
        karel_skipped = self.stats['karel_skipped']
        actual_total = raw_total - karel_skipped  # Exclude Karel problems from main statistics
        
        successful = self.stats['successful_problems']  # AC only
        partial = self.stats['partial_problems']        # PA only
        failed = self.stats['failed_problems']          # Everything else
        errors = self.stats['api_errors']
        
        ac_first = self.stats['ac_first_try']
        ac_second = self.stats['ac_second_try']
        pa_first = self.stats['pa_first_try']
        pa_second = self.stats['pa_second_try']
        no_ac = self.stats['no_ac_achieved']
        
        logger.info(f"OVERALL RESULTS:")
        logger.info(f"   Total problems attempted: {raw_total}")
        logger.info(f"   Karel problems skipped: {karel_skipped}")
        logger.info(f"   Actual problems tested: {actual_total}")
        logger.info("")
        
        if actual_total > 0:
            logger.info(f"   ACCEPTED (AC): {successful}/{actual_total} ({successful/actual_total*100:.1f}%)")
            logger.info(f"   PARTIAL (PA): {partial}/{actual_total} ({partial/actual_total*100:.1f}%)")
            logger.info(f"   FAILED: {failed}/{actual_total} ({failed/actual_total*100:.1f}%)")
            logger.info(f"   API/System errors: {errors}/{actual_total} ({errors/actual_total*100:.1f}%)")
        else:
            logger.info(f"   No problems were actually tested (all were Karel or had errors)")
        
        if actual_total > 0:
            logger.info(f"\nSUCCESS BREAKDOWN (AC only):")
            logger.info(f"   AC on first try: {ac_first}/{actual_total} ({ac_first/actual_total*100:.1f}%)")
            logger.info(f"   AC on second try: {ac_second}/{actual_total} ({ac_second/actual_total*100:.1f}%)")
            
            logger.info(f"\nPARTIAL ACCEPTANCE BREAKDOWN:")
            logger.info(f"   PA on first try: {pa_first}/{actual_total} ({pa_first/actual_total*100:.1f}%)")
            logger.info(f"   PA on second try: {pa_second}/{actual_total} ({pa_second/actual_total*100:.1f}%)")
            
            logger.info(f"\nFAILURE BREAKDOWN:")
            logger.info(f"   No AC or PA achieved: {no_ac}/{actual_total} ({no_ac/actual_total*100:.1f}%)")
        
        if successful > 0:
            logger.info(f"\nSUCCESS RATE ANALYSIS (AC only):")
            logger.info(f"   First try AC rate: {ac_first/successful*100:.1f}% of AC problems")
            logger.info(f"   Second try AC rate: {ac_second/successful*100:.1f}% of AC problems")
            if (failed + ac_second) > 0:
                logger.info(f"   Retry effectiveness (AC): {ac_second/(failed+ac_second)*100:.1f}% of initially failed problems")
        
        # Print sample results by category
        successes = [r for r in self.stats['problem_results'] if r['success']]
        partials = [r for r in self.stats['problem_results'] if not r['success'] and r.get('final_verdict') == 'PA']
        failures = [r for r in self.stats['problem_results'] if not r['success'] and r.get('final_verdict') != 'PA' and not r.get('error')]
        karel_problems = [r for r in self.stats['problem_results'] if r.get('karel_fallback')]
        
        if successes:
            logger.info(f"\nSUCCESSFUL PROBLEMS (AC - showing first 10):")
            for i, result in enumerate(successes[:10], 1):
                attempts_str = "1st try" if result['attempts'] == 1 else "2nd try"
                logger.info(f"   {i:2d}. {result['problem_alias']} - AC on {attempts_str}")
        
        if partials:
            logger.info(f"\nPARTIAL ACCEPTANCE PROBLEMS (PA - showing first 10):")
            for i, result in enumerate(partials[:10], 1):
                attempts_str = "1st try" if result['attempts'] == 1 else "2nd try"
                logger.info(f"   {i:2d}. {result['problem_alias']} - PA on {attempts_str}")
        
        if failures:
            logger.info(f"\nFAILED PROBLEMS (showing first 10):")
            for i, result in enumerate(failures[:10], 1):
                logger.info(f"   {i:2d}. {result['problem_alias']} - {result['final_verdict']} (tried {result['attempts']} times)")
        
        if karel_problems:
            logger.info(f"\nKAREL SKIPPED PROBLEMS ({len(karel_problems)} total):")
            for i, result in enumerate(karel_problems, 1):
                logger.info(f"   {i:2d}. {result['problem_alias']} - SKIPPED (Karel-only problem)")
        
        # Also show Karel problem names if any
        if self.stats['karel_problem_names']:
            logger.info(f"\nKAREL PROBLEM NAMES: {', '.join(self.stats['karel_problem_names'])}")
        
        logger.info("=" * 80)
        
        # Also print user-friendly summary
        print(f"\nAC Testing Complete!")
        print(f"Total attempted: {raw_total}, Karel skipped: {karel_skipped}, Tested: {actual_total}")
        if actual_total > 0:
            print(f"Results: {successful}/{actual_total} AC ({successful/actual_total*100:.1f}%), {partial}/{actual_total} PA ({partial/actual_total*100:.1f}%)")
            print(f"Success: {ac_first} AC on first try, {ac_second} AC on second try")
            print(f"Partial: {pa_first} PA on first try, {pa_second} PA on second try")
        if karel_skipped > 0:
            print(f"Karel problems skipped: {', '.join(self.stats['karel_problem_names'])}")
        print(f"Detailed logs and statistics available above")

def main():
    """Main function to run AC testing."""
    
    if len(sys.argv) < 2:
        print("Usage: python ac_tester.py <problems_file> [language]")
        print("       python ac_tester.py quality_problems_100.txt")
        print("       python ac_tester.py quality_problems_100.txt py3")
        print("       python ac_tester.py quality_problems_50.txt java")
        print("")
        print("Default language: cpp17-gcc (C++17)")
        print("Supported languages: cpp17-gcc, py3, java, etc.")
        return 1
    
    problems_file = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "cpp17-gcc"
    
    try:
        logger.info("Starting AC Tester")
        logger.info(f"Problems file: {problems_file}")
        logger.info(f"Language: {language}")
        
        tester = ACTester()
        problems = tester.load_problems_from_file(problems_file)
        
        if not problems:
            logger.error("No problems loaded!")
            print("ERROR: No problems found to test!")
            return 1
        
        tester.run_bulk_test(problems, language)
        
        return 0
        
    except Exception as e:
        logger.error(f"AC tester failed: {str(e)}")
        print(f"ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 