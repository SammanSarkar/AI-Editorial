#!/usr/bin/env python3
"""
Grader Submission Test Script

This script tests the omegaUp grader submission workflow:
1. Submit a solution to a problem
2. Monitor submission status 
3. Get final verdict and score
4. Test if grading system is working

Usage: python grader_test.py [problem_alias]
"""

import sys
import os
import time
import json
from pathlib import Path

# Add the editorial_generator package to the path
sys.path.insert(0, str(Path(__file__).parent))

from editorial_generator.api import OmegaUpAPI
from editorial_generator.logger import logger


class GraderTester:
    """Tests grader submission and result checking."""

    def __init__(self):
        self.api = OmegaUpAPI()

    def submit_solution(self, problem_alias: str, language: str = "py3", source_code: str = None) -> str:
        """Submit a solution and return the submission GUID."""
        
        if source_code is None:
            # Default simple solution for 'sumas' problem
            source_code = """# Simple solution for sumas problem
a, b = map(int, input().split())
print(a + b)
"""
        
        try:
            logger.info(f"🔬 SUBMITTING SOLUTION TO GRADER")
            logger.info(f"Problem: {problem_alias}")
            logger.info(f"Language: {language}")
            logger.info(f"Source code:")
            logger.info("=" * 40)
            logger.info(source_code)
            logger.info("=" * 40)
            
            # Submit using the exact API endpoint
            data = {
                'problem_alias': problem_alias,
                'language': language,
                'source': source_code
            }
            
            url = f"{self.api.api_url}/run/create"
            logger.info(f"Submitting to: {url}")
            logger.info(f"Data: {data}")
            
            response = self.api.session.post(url, data=data, timeout=(5, 30))
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response content: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") != "ok":
                error_msg = f"Submission failed: {result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            guid = result.get('guid')
            if not guid:
                raise RuntimeError("No GUID returned from submission")
            
            logger.info(f"✅ Solution submitted successfully!")
            logger.info(f"📋 Submission GUID: {guid}")
            logger.info(f"⏱️  Submit delay: {result.get('submit_delay', 0)} minutes")
            
            return guid
            
        except Exception as e:
            logger.error(f"Submission failed: {str(e)}")
            raise

    def check_status(self, run_guid: str) -> dict:
        """Check the status of a submission."""
        try:
            url = f"{self.api.api_url}/run/status"
            params = {'run_alias': run_guid}
            
            response = self.api.session.get(url, params=params, timeout=(3, 10))
            response.raise_for_status()
            
            result = response.json()
            
            # The run/status API returns data directly, not wrapped in status:"ok"
            # If we got a valid response with a guid, it's successful
            if 'guid' in result and result['guid'] == run_guid:
                return result
            else:
                logger.error(f"Invalid status response: missing or wrong guid")
                return {}
            
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            return {}

    def wait_for_result(self, run_guid: str, max_wait_time: int = 60) -> dict:
        """Wait for submission to finish grading and return final result."""
        logger.info(f"⏳ Waiting for grading to complete...")
        
        start_time = time.time()
        last_status = ""
        
        while time.time() - start_time < max_wait_time:
            status_data = self.check_status(run_guid)
            
            if not status_data:
                time.sleep(2)
                continue
            
            current_status = status_data.get('status', 'unknown')
            verdict = status_data.get('verdict', 'unknown')
            
            # Log status changes
            if current_status != last_status:
                logger.info(f"📊 Status: {current_status} | Verdict: {verdict}")
                last_status = current_status
            
            # Check if grading is complete
            if current_status in ['ready', 'done']:
                logger.info(f"✅ Grading completed!")
                self._log_final_result(status_data)
                return status_data
            
            # Check for error states
            if current_status in ['error', 'compile_error']:
                logger.error(f"❌ Grading failed with status: {current_status}")
                self._log_final_result(status_data)
                return status_data
            
            time.sleep(3)  # Wait 3 seconds between checks
        
        logger.warning(f"⚠️ Grading timeout after {max_wait_time} seconds")
        # Return last known status
        final_status = self.check_status(run_guid)
        if final_status:
            self._log_final_result(final_status)
        return final_status

    def _log_final_result(self, status_data: dict):
        """Log the final grading result."""
        logger.info("=" * 60)
        logger.info("🏆 FINAL GRADING RESULT")
        logger.info("=" * 60)
        
        verdict = status_data.get('verdict', 'unknown')
        score = status_data.get('score', 0.0)
        runtime = status_data.get('runtime', 0)
        memory = status_data.get('memory', 0)
        language = status_data.get('language', 'unknown')
        
        logger.info(f"Verdict: {verdict}")
        logger.info(f"Score: {score}")
        logger.info(f"Runtime: {runtime}ms")
        logger.info(f"Memory: {memory}KB")
        logger.info(f"Language: {language}")
        
        # Show execution details if available
        execution = status_data.get('execution', '')
        if execution:
            logger.info(f"Execution: {execution}")
        
        output = status_data.get('output', '')
        if output:
            logger.info(f"Output: {output}")
        
        logger.info("=" * 60)

    def test_grader_workflow(self, problem_alias: str = "sumas") -> bool:
        """Test the complete grader workflow."""
        try:
            logger.info(f"🧪 TESTING GRADER WORKFLOW")
            logger.info(f"Problem: {problem_alias}")
            
            # Step 1: Submit solution
            guid = self.submit_solution(problem_alias)
            
            # Step 2: Wait for result
            final_result = self.wait_for_result(guid)
            
            # Step 3: Analyze result
            if not final_result:
                logger.error("❌ No final result received")
                return False
            
            verdict = final_result.get('verdict', 'unknown')
            score = final_result.get('score', 0.0)
            
            # Check if grading worked
            if verdict == 'AC':  # Accepted
                logger.info(f"🎉 SUCCESS: Solution accepted with score {score}")
                return True
            elif verdict in ['WA', 'TLE', 'MLE', 'RTE', 'CE']:  # Known verdicts
                logger.info(f"✅ GRADER WORKING: Got verdict {verdict} (solution may be wrong)")
                return True
            elif verdict == 'JE':  # Judge Error
                logger.warning(f"⚠️ Judge Error: {verdict}")
                return False
            else:
                logger.warning(f"❓ Unknown verdict: {verdict}")
                return False
                
        except Exception as e:
            logger.error(f"Grader test failed: {str(e)}")
            return False


def main():
    """Main entry point."""
    print("🧪 omegaUp Grader Test Script")
    print("=" * 50)
    
    # Get problem alias from command line or use default
    problem_alias = sys.argv[1] if len(sys.argv) > 1 else "sumas"
    
    try:
        tester = GraderTester()
        success = tester.test_grader_workflow(problem_alias)
        
        if success:
            print(f"\n🎉 GRADER TEST SUCCESSFUL!")
            print(f"💡 The grading system is working correctly")
            return 0
        else:
            print(f"\n❌ GRADER TEST FAILED!")
            print(f"⚠️ There may be issues with the grading system")
            return 1
            
    except Exception as e:
        logger.error(f"Test script failed: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 