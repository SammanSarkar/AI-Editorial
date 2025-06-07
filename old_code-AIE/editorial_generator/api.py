import os
import time
import json
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from .logger import logger


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
            logger.info(f" Logging in as: {username}")
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
            
            logger.info(" Successfully logged in to omegaUp")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Login request failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_problem(self, problem_alias: str) -> Dict[str, Any]:
        """Fetch problem details."""
        try:
            logger.info(f" Fetching problem: {problem_alias}")
            
            url = f"{self.api_url}/problem/details"
            params = {"problem_alias": problem_alias}
            response = self.session.get(url, params=params, timeout=(3, 9))
            response.raise_for_status()
            
            problem_data = response.json()
            if problem_data.get("status") != "ok":
                error_msg = f"Failed to fetch problem: {problem_data.get('error', 'Unknown error')}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            logger.info(f" Fetched: {problem_data.get('title', problem_alias)}")
            return problem_data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch problem details: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_problem_solution(self, problem_alias: str, lang: str = "es") -> Optional[str]:
        """Get the solution/editorial for a problem."""
        try:
            url = f"{self.api_url}/problem/solution"
            params = {
                "problem_alias": problem_alias,
                "lang": lang
            }
            response = self.session.get(url, params=params, timeout=(3, 9))
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "ok":
                    solution_data = result.get("solution", {})
                    
                    if isinstance(solution_data, dict):
                        markdown = solution_data.get("markdown", "")
                        if markdown:
                            return markdown
                    elif isinstance(solution_data, str):
                        return solution_data
            
            return None
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch solution: {str(e)}")
            return None

    def get_problem_versions(self, problem_alias: str) -> Dict[str, Any]:
        """Get problem version information."""
        try:
            logger.info(f"Fetching version info for problem: {problem_alias}")
            
            url = f"{self.api_url}/problem/versions"
            params = {"problem_alias": problem_alias}
            response = self.session.get(url, params=params, timeout=(3, 9))
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "ok":
                    logger.info("=== VERSION INFO ===")
                    logger.info(f"Published Version: {result.get('published')}")
                    logger.info(f"Log Entries: {len(result.get('log', []))}")
                    for entry in result.get('log', [])[:3]:  # Show first 3 entries
                        logger.info(f"  - {entry.get('commit')}: {entry.get('message')}")
                    logger.info("=== END VERSION INFO ===")
                    return result
            
            return {}
            
        except Exception as e:
            logger.warning(f"Failed to fetch version info: {str(e)}")
            return {}

    def submit_editorial_via_update_solution(self, problem_alias: str, content: str, message: str, lang: str = None) -> bool:
        """Submit editorial using the updateSolution endpoint (our current approach)."""
        if lang is None:
            lang = os.getenv("OMEGAUP_LANG", "es")
            
        try:
            logger.info(f"=== SUBMITTING EDITORIAL VIA updateSolution ===")
            logger.info(f"Problem: {problem_alias}")
            logger.info(f"Editorial length: {len(content)} characters")
            logger.info(f"Language: {lang}")
            logger.info(f"Commit message: {message}")
            logger.info(f"Editorial content:\n{content}")
            
            data = {
                'problem_alias': problem_alias,
                'solution': content,
                'message': message,
                'lang': lang
            }
            
            url = f"{self.api_url}/problem/updateSolution"
            response = self.session.post(url, data=data, timeout=(3, 30))
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") != "ok":
                error_msg = f"Failed to submit editorial: {result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return False
            
            logger.info(" Editorial submitted via updateSolution")
            return True
            
        except Exception as e:
            logger.error(f"Editorial submission via updateSolution failed: {str(e)}")
            return False

    def submit_editorial_via_update(self, problem_alias: str, content: str, message: str, lang: str = None) -> bool:
        """Submit editorial using the general update endpoint."""
        if lang is None:
            lang = os.getenv("OMEGAUP_LANG", "es")
            
        try:
            logger.info(f"=== SUBMITTING EDITORIAL VIA update ===")
            
            # First get current problem details to maintain other settings
            problem = self.get_problem(problem_alias)
            
            data = {
                'problem_alias': problem_alias,
                'solution': content,
                'message': message,
                'lang': lang,
                'redirect': 'false',
                'update_published': 'all'
            }
            
            url = f"{self.api_url}/problem/update"
            response = self.session.post(url, data=data, timeout=(3, 30))
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") != "ok":
                error_msg = f"Failed to submit editorial via update: {result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return False
            
            logger.info(" Editorial submitted via update")
            return True
            
        except Exception as e:
            logger.error(f"Editorial submission via update failed: {str(e)}")
            return False

    def select_version(self, problem_alias: str, commit: str = None) -> bool:
        """Select/publish a specific version of the problem."""
        try:
            logger.info(f"=== SELECTING VERSION ===")
            
            if not commit:
                # Get latest commit
                problem = self.get_problem(problem_alias)
                commit = problem.get('commit')
                
            if not commit:
                logger.error("No commit hash available")
                return False
            
            logger.info(f"Selecting version {commit} for problem {problem_alias}")
            
            data = {
                'problem_alias': problem_alias,
                'commit': commit,
                'update_published': 'all'
            }
            
            url = f"{self.api_url}/problem/selectVersion"
            response = self.session.post(url, data=data, timeout=(3, 30))
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") != "ok":
                error_msg = f"Failed to select version: {result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return False
            
            logger.info(" Version selected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Version selection failed: {str(e)}")
            return False

    def submit_editorial_via_edit_form(self, problem_alias: str, content: str, message: str, lang: str = None) -> bool:
        """Submit editorial using the web interface method (form POST to edit page)."""
        if lang is None:
            lang = os.getenv("OMEGAUP_LANG", "es")
            
        try:
            logger.info(f"=== SUBMITTING EDITORIAL VIA EDIT FORM (Web Interface Method) ===")
            logger.info(f"Problem: {problem_alias}")
            logger.info(f"Editorial length: {len(content)} characters")
            logger.info(f"Language: {lang}")
            logger.info(f"Commit message: {message}")
            
            # Prepare the statements object exactly like the web interface
            statements = {lang: content}
            
            # Form data exactly as the web interface sends it
            form_data = {
                'request': 'markdown',
                'directory': 'solutions',
                'problem_alias': problem_alias,
                'message': message,
                'contents': json.dumps(statements)
            }
            
            logger.info(f"Form data: {json.dumps(form_data, indent=2)}")
            
            # Submit to the edit page (same as web interface)
            url = f"{self.base_url}/problem/{problem_alias}/edit/"
            
            # Set proper headers for form submission
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            response = self.session.post(
                url, 
                data=form_data, 
                headers=headers,
                timeout=(3, 30),
                allow_redirects=True
            )
            
            self._log_request_response("POST", url, form_data, response)
            
            response.raise_for_status()
            
            # Check if the response indicates success
            # The web interface typically redirects or shows success
            if response.status_code in [200, 302] and 'statusError' not in response.text:
                logger.info(" Editorial submitted via edit form (web interface method)")
                
                # Force cache invalidation
                self._invalidate_caches(problem_alias, lang)
                
                return True
            else:
                logger.error(f"Edit form submission failed: Status {response.status_code}")
                return False
            
        except Exception as e:
            logger.error(f"Editorial submission via edit form failed: {str(e)}")
            return False

    def _invalidate_caches(self, problem_alias: str, lang: str):
        """Force cache invalidation by making requests with cache-busting parameters."""
        try:
            logger.info(f"=== INVALIDATING CACHES ===")
            
            # Cache-busting headers
            cache_bust_headers = {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
            
            # Clear solution cache by requesting it with cache-busting
            cache_bust_params = {
                'problem_alias': problem_alias,
                'lang': lang,
                '_': str(int(time.time() * 1000))  # timestamp cache buster
            }
            
            logger.info("Invalidating solution cache...")
            url = f"{self.api_url}/problem/solution"
            response = self.session.get(
                url, 
                params=cache_bust_params, 
                headers=cache_bust_headers,
                timeout=(3, 9)
            )
            logger.info(f"Cache invalidation response: {response.status_code}")
            
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {str(e)}")

    def submit_editorial_web_form(self, problem_alias: str, content: str, message: str, lang: str = None) -> bool:
        """Submit editorial using the EXACT web interface form submission process."""
        if lang is None:
            lang = os.getenv("OMEGAUP_LANG", "es")
            
        try:
            logger.info(f" Submitting {lang.upper()} editorial ({len(content)} chars)")
            
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
                logger.info(f" {lang.upper()} editorial submitted successfully")
                self._cache_clear(problem_alias, lang)
                return True
            else:
                logger.error(f"❌ {lang.upper()} editorial submission failed")
                return False
            
        except Exception as e:
            logger.error(f"Editorial submission failed: {str(e)}")
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
            logger.info(f" Submitting editorial to all languages...")
            
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
            logger.info(f" Updated {success_count}/{total_languages} languages")
            
            if overall_success:
                logger.info(" Comprehensive editorial update successful")
            else:
                logger.error("❌ All language updates failed")
            
            return overall_success
            
        except Exception as e:
            logger.error(f"Comprehensive editorial submission failed: {str(e)}")
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