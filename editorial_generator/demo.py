#!/usr/bin/env python3
"""
Editorial Generator Demo

This script implements the full workflow:
1. Get problem details
2. Generate solution code using OpenAI
3. Submit to grader and get verdict
4. If accepted: Generate editorial based on working solution
5. If rejected: Retry code generation once with error feedback
6. Update problem editorial

Usage: 
  Single problem: python demo.py [problem_alias] [language]
  Bulk processing: python demo.py --bulk problems.txt [language]
"""

import sys
import os
import time
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

import requests
from dotenv import load_dotenv

# Import prompts module
from prompts import (
    get_code_generation_prompt,
    get_editorial_generation_prompt,
    get_code_system_prompt,
    get_editorial_system_prompt,
    get_mock_code_template,
    get_mock_editorial_template
)

# Set up logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"editorial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class OmegaUpAPI:
    """Client for interacting with the omegaUp API."""

    def __init__(self):
        load_dotenv()
        self.base_url = os.getenv("OMEGAUP_BASE_URL", "http://localhost:8001")
        self.api_url = f"{self.base_url}/api"
        self.session = requests.Session()
        
        # Login on initialization
        self._login()

    def _login(self) -> None:
        """Authenticate with omegaUp using credentials from environment."""
        username = os.getenv("OMEGAUP_USERNAME")
        password = os.getenv("OMEGAUP_PASSWORD")
        
        if not username or not password:
            error_msg = "OMEGAUP_USERNAME and OMEGAUP_PASSWORD must be set in .env"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            logger.info(f"Logging in as: {username}")
            login_data = {
                'usernameOrEmail': username,
                'password': password
            }
            
            url = f"{self.api_url}/user/login"
            response = self.session.post(url, data=login_data, timeout=(3, 9))
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") != "ok":
                error_msg = f"Login failed: {result.get('error', 'Invalid credentials')}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info("Successfully logged in to omegaUp")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Login request failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_problem(self, problem_alias: str) -> Dict[str, Any]:
        """Fetch problem details."""
        try:
            logger.info(f"[{problem_alias}] Fetching problem details")
            
            url = f"{self.api_url}/problem/details"
            params = {"problem_alias": problem_alias}
            response = self.session.get(url, params=params, timeout=(3, 9))
            response.raise_for_status()
            
            problem_data = response.json()
            if problem_data.get("status") != "ok":
                error_msg = f"Failed to fetch problem: {problem_data.get('error', 'Unknown error')}"
                logger.error(f"[{problem_alias}] {error_msg}")
                raise RuntimeError(error_msg)
                
            title = problem_data.get('title', problem_alias)
            logger.info(f"[{problem_alias}] Fetched: {title}")
            return problem_data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch problem details: {str(e)}"
            logger.error(f"[{problem_alias}] {error_msg}")
            raise RuntimeError(error_msg)

    def submit_editorial_web_form(self, problem_alias: str, content: str, message: str, lang: str = None) -> bool:
        """Submit editorial using the EXACT web interface form submission process."""
        if lang is None:
            lang = os.getenv("OMEGAUP_LANG", "es")
            
        try:
            logger.info(f"[{problem_alias}] Submitting {lang.upper()} editorial ({len(content)} chars)")
            
            # The EXACT form data that the web interface sends
            statements = {lang: content}
            
            form_data = {
                'request': 'markdown',
                'directory': 'solutions', 
                'problem_alias': problem_alias,
                'message': message,
                'contents': json.dumps(statements),
                'update_published': 'all'
            }
            
            # Submit to the EXACT same URL as web interface  
            url = f"{self.base_url}/problem/{problem_alias}/edit/"
            
            # Use EXACT same headers as browser
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.session.post(
                url, 
                data=form_data, 
                headers=headers,
                timeout=(5, 30),
                allow_redirects=True
            )
            
            # Check for success indicators in response
            success_indicators = [
                'statusSuccess',
                'successfully', 
                'exitoso',
                '"status":"ok"'
            ]
            
            error_indicators = [
                'statusError',
                'error',
                'failed',
                'Exception'
            ]
            
            response_text = response.text.lower()
            has_success = any(indicator.lower() in response_text for indicator in success_indicators)
            has_error = any(indicator.lower() in response_text for indicator in error_indicators)
            
            if response.status_code in [200, 302] and (has_success or not has_error):
                logger.info(f"[{problem_alias}] {lang.upper()} editorial submitted successfully")
                self._cache_clear(problem_alias, lang)
                return True
            else:
                logger.error(f"[{problem_alias}] {lang.upper()} editorial submission failed")
                return False
            
        except Exception as e:
            logger.error(f"[{problem_alias}] Editorial submission failed: {str(e)}")
            return False

    def _cache_clear(self, problem_alias: str, lang: str):
        """Clear cache with minimal logging."""
        try:
            cache_headers = {
                'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
                'Pragma': 'no-cache',
                'Expires': '0',
                'If-Modified-Since': 'Thu, 01 Jan 1970 00:00:00 GMT'
            }
            
            timestamp = str(int(time.time() * 1000))
            
            cache_bust_urls = [
                f"{self.api_url}/problem/solution?problem_alias={problem_alias}&lang={lang}&_={timestamp}",
                f"{self.api_url}/problem/details?problem_alias={problem_alias}&_={timestamp}"
            ]
            
            for url in cache_bust_urls:
                try:
                    self.session.get(url, headers=cache_headers, timeout=(2, 5))
                except:
                    pass
            
            time.sleep(1)
            
        except Exception:
            pass

    def submit_editorial_all_languages(self, problem_alias: str, content: str, message: str) -> bool:
        """Submit editorial to ALL available languages to ensure coverage."""
        try:
            logger.info(f"[{problem_alias}] Submitting editorial to all languages...")
            
            # Get problem details to see available languages
            problem_data = self.get_problem(problem_alias)
            
            success_count = 0
            total_languages = 0
            
            # Target languages to update (common ones)
            target_languages = ['es', 'en', 'pt']  # Spanish, English, Portuguese
            
            for lang in target_languages:
                # Adapt content for language (basic adaptation)
                adapted_content = self._adapt_content_for_language(content, lang)
                
                # Submit using the EXACT web interface method  
                success = self.submit_editorial_web_form(problem_alias, adapted_content, message, lang)
                
                if success:
                    success_count += 1
                
                total_languages += 1
                time.sleep(0.5)  # Small delay between language updates
            
            overall_success = success_count > 0
            logger.info(f"[{problem_alias}] Updated {success_count}/{total_languages} languages")
            
            if overall_success:
                logger.info(f"[{problem_alias}] Comprehensive editorial update successful")
            else:
                logger.error(f"[{problem_alias}] All language updates failed")
            
            return overall_success
            
        except Exception as e:
            logger.error(f"[{problem_alias}] Comprehensive editorial submission failed: {str(e)}")
            return False

    def _adapt_content_for_language(self, content: str, lang: str) -> str:
        """Adapt content for specific language (basic translation adjustments)."""
        if lang == 'en':
            # Basic Spanish to English adaptations
            adapted = content.replace('Editorial:', 'Editorial:')
            adapted = adapted.replace('Resumen del Problema', 'Problem Summary')
            adapted = adapted.replace('Enfoque de Solución', 'Solution Approach')
            adapted = adapted.replace('Código de Solución', 'Solution Code')
            adapted = adapted.replace('Complejidad', 'Complexity')
            adapted = adapted.replace('Tiempo', 'Time')
            adapted = adapted.replace('Espacio', 'Space')
            adapted = adapted.replace('Notas Importantes', 'Important Notes')
            adapted = adapted.replace('Editorial generado por IA', 'AI-generated editorial')
            adapted = adapted.replace('Versión Demo', 'Demo Version')
            return adapted
        elif lang == 'pt':
            # Basic Spanish to Portuguese adaptations  
            adapted = content.replace('Editorial:', 'Editorial:')
            adapted = adapted.replace('Resumen del Problema', 'Resumo do Problema')
            adapted = adapted.replace('Enfoque de Solución', 'Abordagem da Solução')
            adapted = adapted.replace('Código de Solución', 'Código da Solução')
            adapted = adapted.replace('Complejidad', 'Complexidade')
            adapted = adapted.replace('Tiempo', 'Tempo')
            adapted = adapted.replace('Espacio', 'Espaço')
            adapted = adapted.replace('Notas Importantes', 'Notas Importantes')
            adapted = adapted.replace('Editorial generado por IA', 'Editorial gerado por IA')
            adapted = adapted.replace('Versión Demo', 'Versão Demo')
            return adapted
        else:
            # Default to original content (Spanish)
            return content


class DemoAI:
    """AI component for code and editorial generation."""

    def __init__(self):
        from openai import OpenAI
        
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.info("Using mock AI generation (no OpenAI API key)")
            self.client = None
        else:
            logger.info("Using OpenAI for code and editorial generation")
            self.client = OpenAI(api_key=api_key)
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
        
        # Log statement
        statement = problem_data.get('statement', {})
        markdown = statement.get('markdown', '')
        if markdown:
            logger.info(f"[{problem_alias}] Problem Statement ({len(markdown)} chars):")
            logger.info(f"   {markdown}")
        
        # Log settings
        settings = problem_data.get('settings', {})
        limits = settings.get('limits', {})
        if limits:
            logger.info(f"[{problem_alias}] Time Limit: {limits.get('TimeLimit', 'Unknown')}")
            logger.info(f"[{problem_alias}] Memory Limit: {limits.get('MemoryLimit', 'Unknown')}")

    def _generate_mock_code(self, problem_alias: str, title: str, language: str) -> str:
        """Generate mock code for demonstration."""
        code = get_mock_code_template(title, language)
        
        logger.info(f"[{problem_alias}] Generated mock solution code ({len(code)} chars)")
        logger.info(f"[{problem_alias}] Generated code:")
        logger.info("=" * 60)
        logger.info(code)
        logger.info("=" * 60)
        
        return code

    def _generate_openai_code(self, problem_alias: str, title: str, statement: str, language: str, error_feedback: str) -> str:
        """Generate code using OpenAI API."""
        
        prompt = get_code_generation_prompt(title, statement, language, error_feedback)

        try:
            logger.info(f"[{problem_alias}] Requesting code generation from OpenAI")
            logger.info(f"[{problem_alias}] Prompt ({len(prompt)} chars):")
            logger.info("=" * 60)
            logger.info(prompt)
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
            logger.info(code)
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
        logger.info(editorial)
        logger.info("=" * 60)
        
        return editorial

    def _generate_openai_editorial(self, problem_alias: str, title: str, statement: str, solution_code: str, verdict: str, language: str) -> str:
        """Generate editorial using OpenAI API."""
        
        prompt = get_editorial_generation_prompt(title, statement, solution_code, verdict, language)

        try:
            logger.info(f"[{problem_alias}] Requesting editorial generation from OpenAI")
            logger.info(f"[{problem_alias}] Editorial prompt ({len(prompt)} chars):")
            logger.info("=" * 60)
            logger.info(prompt)
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
            logger.info(editorial)
            logger.info("=" * 60)
            
            return editorial
            
        except Exception as e:
            logger.error(f"[{problem_alias}] OpenAI editorial generation failed: {str(e)}")
            return self._generate_mock_editorial(problem_alias, title, solution_code, verdict, language)


class DemoGrader:
    """Grader component for testing solutions."""

    def __init__(self, api: OmegaUpAPI):
        self.api = api

    def test_solution(self, problem_alias: str, code: str, language: str = "py3") -> dict:
        """Test solution and return result."""
        
        logger.info(f"[{problem_alias}] Testing solution with grader")
        logger.info(f"[{problem_alias}] Language: {language}")
        logger.info(f"[{problem_alias}] Code length: {len(code)} chars")
        
        try:
            # Submit solution
            data = {
                'problem_alias': problem_alias,
                'language': language,
                'source': code
            }
            
            url = f"{self.api.api_url}/run/create"
            logger.info(f"[{problem_alias}] Submitting to grader: {url}")
            
            response = self.api.session.post(url, data=data, timeout=(5, 30))
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") != "ok":
                logger.error(f"[{problem_alias}] Submission failed: {result.get('error', 'Unknown error')}")
                return {}
            
            guid = result.get('guid')
            logger.info(f"[{problem_alias}] Submission successful")
            logger.info(f"[{problem_alias}] GUID: {guid}")
            logger.info(f"[{problem_alias}] Submit delay: {result.get('submit_delay', 0)} minutes")
            
            # Wait for result
            return self._wait_for_result(problem_alias, guid)
            
        except Exception as e:
            logger.error(f"[{problem_alias}] Solution testing failed: {str(e)}")
            return {}

    def _wait_for_result(self, problem_alias: str, run_guid: str, max_wait_time: int = 30) -> dict:
        """Wait for grading result."""
        
        logger.info(f"[{problem_alias}] Waiting for grading result...")
        start_time = time.time()
        last_status = ""
        
        while time.time() - start_time < max_wait_time:
            try:
                url = f"{self.api.api_url}/run/status"
                params = {'run_alias': run_guid}
                
                response = self.api.session.get(url, params=params, timeout=(3, 10))
                response.raise_for_status()
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
                        logger.info(f"[{problem_alias}] Verdict: {verdict}")
                        logger.info(f"[{problem_alias}] Score: {result.get('score', 0.0)}")
                        logger.info(f"[{problem_alias}] Runtime: {result.get('runtime', 0)}ms")
                        logger.info(f"[{problem_alias}] Memory: {result.get('memory', 0)}KB")
                        
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
                
                time.sleep(2)
                
            except Exception as e:
                logger.warning(f"[{problem_alias}] Status check failed: {str(e)}")
                time.sleep(2)
        
        logger.warning(f"[{problem_alias}] Grading timeout - no result received")
        return {}


class Demo:
    """Main demo orchestrator."""

    def __init__(self):
        self.api = OmegaUpAPI()
        self.ai = DemoAI()
        self.grader = DemoGrader(self.api)

    def run_single_workflow(self, problem_alias: str, language: str = "py3") -> bool:
        """Run the complete editorial generation workflow for a single problem."""
        
        logger.info("=" * 80)
        logger.info(f"[{problem_alias}] STARTING EDITORIAL GENERATION WORKFLOW")
        logger.info("=" * 80)
        logger.info(f"[{problem_alias}] Problem alias: {problem_alias}")
        logger.info(f"[{problem_alias}] Language: {language}")
        logger.info("=" * 80)
        
        try:
            # Step 1: Get problem details
            logger.info(f"[{problem_alias}] STEP 1: FETCHING PROBLEM DETAILS")
            logger.info("-" * 40)
            problem_data = self.api.get_problem(problem_alias)
            title = problem_data.get('title', problem_alias)
            logger.info(f"[{problem_alias}] Successfully fetched: {title}")
            
            # Step 2: Generate initial solution
            logger.info("")
            logger.info(f"[{problem_alias}] STEP 2: GENERATING INITIAL SOLUTION")
            logger.info("-" * 40)
            solution_code = self.ai.generate_solution_code(problem_data, language)
            
            # Step 3: Test solution
            logger.info("")
            logger.info(f"[{problem_alias}] STEP 3: TESTING SOLUTION WITH GRADER")
            logger.info("-" * 40)
            test_result = self.grader.test_solution(problem_alias, solution_code, language)
            
            if not test_result:
                logger.error(f"[{problem_alias}] Failed to get grading result")
                return False
            
            verdict = test_result.get('verdict', 'unknown')
            score = test_result.get('score', 0.0)
            
            logger.info("")
            logger.info(f"[{problem_alias}] STEP 3 RESULT:")
            logger.info(f"   Verdict: {verdict}")
            logger.info(f"   Score: {score}")
            
            # Step 4: Handle result
            if verdict == 'AC':
                logger.info("")
                logger.info(f"[{problem_alias}] STEP 4: SOLUTION ACCEPTED - PROCEEDING TO EDITORIAL")
                logger.info("-" * 40)
                logger.info(f"[{problem_alias}] Solution accepted on first try")
                final_code = solution_code
                final_verdict = verdict
                final_score = score
            else:
                logger.info("")
                logger.info(f"[{problem_alias}] STEP 4: SOLUTION REJECTED - ATTEMPTING REGENERATION")
                logger.info("-" * 40)
                
                # Prepare error feedback
                error_info = f"Verdict: {verdict}, Score: {score}"
                execution = test_result.get('execution', '')
                output = test_result.get('output', '')
                if execution:
                    error_info += f", Execution: {execution}"
                if output:
                    error_info += f", Output: {output}"
                
                logger.info(f"[{problem_alias}] Preparing error feedback for regeneration:")
                logger.info(f"   {error_info}")
                
                # Step 5: Regenerate solution with error feedback
                logger.info("")
                logger.info(f"[{problem_alias}] STEP 5: REGENERATING SOLUTION WITH ERROR FEEDBACK")
                logger.info("-" * 40)
                retry_code = self.ai.generate_solution_code(problem_data, language, error_info)
                
                # Test retry solution
                logger.info("")
                logger.info(f"[{problem_alias}] STEP 5b: TESTING REGENERATED SOLUTION")
                logger.info("-" * 40)
                retry_result = self.grader.test_solution(problem_alias, retry_code, language)
                
                if retry_result:
                    retry_verdict = retry_result.get('verdict', 'unknown')
                    retry_score = retry_result.get('score', 0.0)
                    
                    logger.info("")
                    logger.info(f"[{problem_alias}] RETRY RESULT:")
                    logger.info(f"   Original: {verdict} (score: {score})")
                    logger.info(f"   Retry:    {retry_verdict} (score: {retry_score})")
                    
                    # Use the better solution
                    if retry_verdict == 'AC' or retry_score > score:
                        final_code = retry_code
                        final_verdict = retry_verdict
                        final_score = retry_score
                        logger.info(f"[{problem_alias}] Decision: Using retry solution (better result)")
                    else:
                        final_code = solution_code
                        final_verdict = verdict
                        final_score = score
                        logger.info(f"[{problem_alias}] Decision: Using original solution (retry didn't improve)")
                else:
                    logger.warning(f"[{problem_alias}] Retry testing failed, using original solution")
                    final_code = solution_code
                    final_verdict = verdict
                    final_score = score
            
            # Step 6: Generate editorial
            logger.info("")
            logger.info(f"[{problem_alias}] STEP 6: GENERATING EDITORIAL")
            logger.info("-" * 40)
            editorial = self.ai.generate_editorial(problem_data, final_code, final_verdict, final_score, language)
            
            # Step 7: Update problem editorial
            logger.info("")
            logger.info(f"[{problem_alias}] STEP 7: UPDATING PROBLEM EDITORIAL")
            logger.info("-" * 40)
            commit_message = f"AI-generated editorial based on {final_verdict} solution"
            logger.info(f"[{problem_alias}] Commit message: {commit_message}")
            
            success = self.api.submit_editorial_all_languages(
                problem_alias=problem_alias,
                content=editorial,
                message=commit_message
            )
            
            if success:
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"[{problem_alias}] WORKFLOW COMPLETED SUCCESSFULLY")
                logger.info("=" * 80)
                logger.info(f"[{problem_alias}] FINAL SUMMARY:")
                logger.info(f"   Problem: {title}")
                logger.info(f"   Problem alias: {problem_alias}")
                logger.info(f"   Final verdict: {final_verdict}")
                logger.info(f"   Final score: {final_score}")
                logger.info(f"   Editorial length: {len(editorial)} characters")
                logger.info(f"   Languages updated: ES, EN, PT")
                logger.info("=" * 80)
                return True
            else:
                logger.error(f"[{problem_alias}] Editorial update failed")
                return False
                
        except Exception as e:
            logger.error(f"[{problem_alias}] Workflow failed: {str(e)}")
            return False

    def run_bulk_workflow(self, problems_file: str, language: str = "py3") -> Dict[str, bool]:
        """Run the editorial generation workflow for multiple problems."""
        
        logger.info("=" * 100)
        logger.info("STARTING BULK EDITORIAL GENERATION WORKFLOW")
        logger.info("=" * 100)
        logger.info(f"Problems file: {problems_file}")
        logger.info(f"Language: {language}")
        logger.info("=" * 100)
        
        # Read problems list
        try:
            with open(problems_file, 'r', encoding='utf-8') as f:
                problem_aliases = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            logger.error(f"Problems file not found: {problems_file}")
            return {}
        except Exception as e:
            logger.error(f"Error reading problems file: {str(e)}")
            return {}
        
        if not problem_aliases:
            logger.error("No problems found in file")
            return {}
        
        logger.info(f"Found {len(problem_aliases)} problems to process:")
        for i, alias in enumerate(problem_aliases, 1):
            logger.info(f"   {i:2d}. {alias}")
        
        results = {}
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        # Process each problem
        for i, problem_alias in enumerate(problem_aliases, 1):
            logger.info("")
            logger.info("=" * 100)
            logger.info(f"PROCESSING PROBLEM {i}/{len(problem_aliases)}: {problem_alias}")
            logger.info("=" * 100)
            
            try:
                success = self.run_single_workflow(problem_alias, language)
                results[problem_alias] = success
                
                if success:
                    successful += 1
                    logger.info(f"[{problem_alias}] Problem {i}/{len(problem_aliases)} completed successfully")
                else:
                    failed += 1
                    logger.error(f"[{problem_alias}] Problem {i}/{len(problem_aliases)} failed")
                
                # Add delay between problems to avoid overwhelming the server
                if i < len(problem_aliases):
                    logger.info(f"Waiting 5 seconds before next problem...")
                    time.sleep(5)
                    
            except Exception as e:
                failed += 1
                results[problem_alias] = False
                logger.error(f"[{problem_alias}] Problem {i}/{len(problem_aliases)} crashed: {str(e)}")
        
        # Final summary
        elapsed_time = time.time() - start_time
        logger.info("")
        logger.info("=" * 100)
        logger.info("BULK WORKFLOW COMPLETED")
        logger.info("=" * 100)
        logger.info(f"BULK PROCESSING SUMMARY:")
        logger.info(f"   Total problems: {len(problem_aliases)}")
        logger.info(f"   Successful: {successful}")
        logger.info(f"   Failed: {failed}")
        logger.info(f"   Success rate: {successful/len(problem_aliases)*100:.1f}%")
        logger.info(f"   Total time: {elapsed_time/60:.1f} minutes")
        logger.info(f"   Average time per problem: {elapsed_time/len(problem_aliases):.1f} seconds")
        
        logger.info("")
        logger.info("DETAILED RESULTS:")
        for alias, success in results.items():
            status = "SUCCESS" if success else "FAILED"
            logger.info(f"   {alias}: {status}")
        
        logger.info("=" * 100)
        
        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Editorial Generator Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Single problem:     python demo.py sumas
  Single with lang:   python demo.py sumas cpp17-gcc
  Bulk processing:    python demo.py --bulk problems.txt
  Bulk with lang:     python demo.py --bulk problems.txt py3
        """
    )
    
    # Add mutually exclusive group for single vs bulk mode
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('problem_alias', nargs='?', help='Problem alias for single mode')
    mode_group.add_argument('--bulk', dest='problems_file', help='Problems file for bulk processing')
    
    parser.add_argument('language', nargs='?', default='py3', help='Programming language (default: py3)')
    
    args = parser.parse_args()
    
    print("Editorial Generator Demo")
    print("=" * 50)
    
    try:
        demo = Demo()
        
        if args.problems_file:
            # Bulk processing mode
            problems_file = args.problems_file
            language = args.language
            
            results = demo.run_bulk_workflow(problems_file, language)
            
            if results:
                successful = sum(1 for success in results.values() if success)
                total = len(results)
                print(f"\nBulk processing completed!")
                print(f"Results: {successful}/{total} problems successful")
                return 0 if successful > 0 else 1
            else:
                print("\nBulk processing failed!")
                return 1
        else:
            # Single problem mode
            if not args.problem_alias:
                print("Error: Problem alias is required for single mode")
                parser.print_help()
                return 1
                
            problem_alias = args.problem_alias
            language = args.language
            
            success = demo.run_single_workflow(problem_alias, language)
            
            if success:
                print(f"\nWorkflow completed successfully!")
                print(f"Check the editorial at: http://localhost:8001/arena/problem/{problem_alias}#solution")
                return 0
            else:
                print(f"\nWorkflow failed!")
                return 1
                
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 