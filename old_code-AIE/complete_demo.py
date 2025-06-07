#!/usr/bin/env python3
"""
Complete Editorial Generator Demo

This script implements the full workflow:
1. Get problem details
2. Generate solution code using OpenAI
3. Submit to grader and get verdict
4. If accepted: Generate editorial based on working solution
5. If rejected: Retry code generation once with error feedback
6. Update problem editorial

Usage: python complete_demo.py [problem_alias]
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


class CompleteDemoAI:
    """AI component for code and editorial generation."""

    def __init__(self):
        from openai import OpenAI
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.info("Using mock AI generation (no OpenAI API key)")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def generate_solution_code(self, problem_data: dict, language: str = "py3", error_feedback: str = None) -> str:
        """Generate solution code for the problem."""
        
        title = problem_data.get('title', 'Unknown Problem')
        statement = problem_data.get('statement', {}).get('markdown', '')
        
        logger.info("=" * 60)
        logger.info("GENERATING SOLUTION CODE")
        logger.info("=" * 60)
        logger.info(f"Problem: {title}")
        logger.info(f"Language: {language}")
        
        # Log problem details
        self._log_problem_details(problem_data)
        
        if error_feedback:
            logger.info("=" * 40)
            logger.info("ERROR FEEDBACK PROVIDED")
            logger.info("=" * 40)
            logger.info(error_feedback)
            logger.info("=" * 40)
        
        if self.client is None:
            return self._generate_mock_code(title, language)
        else:
            return self._generate_openai_code(title, statement, language, error_feedback)

    def _log_problem_details(self, problem_data: dict) -> None:
        """Log detailed problem information."""
        logger.info("=" * 40)
        logger.info("PROBLEM DETAILS")
        logger.info("=" * 40)
        
        title = problem_data.get('title', 'Unknown')
        alias = problem_data.get('alias', 'unknown')
        
        logger.info(f"Title: {title}")
        logger.info(f"Alias: {alias}")
        
        # Log statement
        statement = problem_data.get('statement', {})
        markdown = statement.get('markdown', '')
        if markdown:
            logger.info(f"Problem Statement ({len(markdown)} chars):")
            logger.info(markdown)
        
        # Log settings
        settings = problem_data.get('settings', {})
        limits = settings.get('limits', {})
        if limits:
            logger.info(f"Time Limit: {limits.get('TimeLimit', 'Unknown')}")
            logger.info(f"Memory Limit: {limits.get('MemoryLimit', 'Unknown')}")
        
        logger.info("=" * 40)

    def _generate_mock_code(self, title: str, language: str) -> str:
        """Generate mock code for demonstration."""
        if language == "py3":
            if "suma" in title.lower():
                code = """# Solution for sumas problem
a, b = map(int, input().split())
print(a + b)
"""
            else:
                code = """# Mock solution
data = input().strip()
print("Mock output")
"""
        else:
            code = """// Mock solution
#include <iostream>
using namespace std;
int main() {
    cout << "Mock output" << endl;
    return 0;
}
"""
        
        logger.info("Generated mock solution code")
        logger.info("=" * 40)
        logger.info("MOCK CODE GENERATED")
        logger.info("=" * 40)
        logger.info(code)
        logger.info("=" * 40)
        return code

    def _generate_openai_code(self, title: str, statement: str, language: str, error_feedback: str) -> str:
        """Generate code using OpenAI API."""
        
        lang_info = {
            "py3": "Python 3",
            "cpp17-gcc": "C++17",
            "java": "Java"
        }
        
        prompt = f"""Generate a working solution for this programming problem:

Problem: {title}
Statement: {statement}

Requirements:
- Write code in {lang_info.get(language, language)}
- The solution should be correct and efficient
- Include only the code, no explanations
- Handle input/output as specified in the problem

"""
        
        if error_feedback:
            prompt += f"""
IMPORTANT: The previous solution failed with this error:
{error_feedback}

Please fix the issue and generate a corrected solution.
"""

        try:
            logger.info("=" * 40)
            logger.info("OPENAI CODE GENERATION PROMPT")
            logger.info("=" * 40)
            logger.info(prompt)
            logger.info("=" * 40)
            
            logger.info("Requesting code generation from OpenAI")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert competitive programmer. Generate only working code solutions."},
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
            
            logger.info("=" * 40)
            logger.info("OPENAI CODE RESPONSE")
            logger.info("=" * 40)
            logger.info(code)
            logger.info("=" * 40)
            logger.info(f"Generated OpenAI solution code ({len(code)} chars)")
            return code
            
        except Exception as e:
            logger.error(f"OpenAI code generation failed: {str(e)}")
            return self._generate_mock_code(title, language)

    def generate_editorial(self, problem_data: dict, solution_code: str, verdict: str, score: float) -> str:
        """Generate editorial based on working solution."""
        
        title = problem_data.get('title', 'Unknown Problem')
        statement = problem_data.get('statement', {}).get('markdown', '')
        
        logger.info("=" * 60)
        logger.info("GENERATING EDITORIAL")
        logger.info("=" * 60)
        logger.info(f"Problem: {title}")
        logger.info(f"Solution verdict: {verdict}")
        logger.info(f"Solution score: {score}")
        logger.info(f"Code length: {len(solution_code)} chars")
        
        if self.client is None:
            return self._generate_mock_editorial(title, solution_code, verdict)
        else:
            return self._generate_openai_editorial(title, statement, solution_code, verdict)

    def _generate_mock_editorial(self, title: str, solution_code: str, verdict: str) -> str:
        """Generate mock editorial."""
        editorial = f"""# Editorial: {title}

## Problem Summary
This problem requires implementing a solution for {title}.

## Solution Approach
The approach involves reading the input, processing the data according to the problem requirements, and producing the correct output.

## Working Solution
The following solution achieved verdict {verdict}:

```python
{solution_code.strip()}
```

## Complexity Analysis
- Time Complexity: O(n) where n is the input size
- Space Complexity: O(1) additional space

## Implementation Notes
This solution correctly handles the problem constraints and produces the expected output format.
"""
        
        logger.info("=" * 40)
        logger.info("MOCK EDITORIAL GENERATED")
        logger.info("=" * 40)
        logger.info(editorial)
        logger.info("=" * 40)
        logger.info(f"Generated mock editorial ({len(editorial)} chars)")
        return editorial

    def _generate_openai_editorial(self, title: str, statement: str, solution_code: str, verdict: str) -> str:
        """Generate editorial using OpenAI API."""
        
        prompt = f"""Write a comprehensive editorial for this programming problem:

Problem: {title}
Statement: {statement}

Working Solution (Verdict: {verdict}):
{solution_code}

Please write a detailed editorial in English that includes:
1. Problem summary and understanding
2. Solution approach and algorithm explanation
3. Step-by-step implementation details
4. Complexity analysis
5. Key insights and important notes

Format the editorial in clear markdown with proper sections.
"""

        try:
            logger.info("=" * 40)
            logger.info("OPENAI EDITORIAL GENERATION PROMPT")
            logger.info("=" * 40)
            logger.info(prompt)
            logger.info("=" * 40)
            
            logger.info("Requesting editorial generation from OpenAI")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at writing clear, educational programming contest editorials."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            editorial = response.choices[0].message.content.strip()
            
            logger.info("=" * 40)
            logger.info("OPENAI EDITORIAL RESPONSE")
            logger.info("=" * 40)
            logger.info(editorial)
            logger.info("=" * 40)
            logger.info(f"Generated OpenAI editorial ({len(editorial)} chars)")
            return editorial
            
        except Exception as e:
            logger.error(f"OpenAI editorial generation failed: {str(e)}")
            return self._generate_mock_editorial(title, solution_code, verdict)


class CompleteDemoGrader:
    """Grader component for testing solutions."""

    def __init__(self, api: OmegaUpAPI):
        self.api = api

    def test_solution(self, problem_alias: str, code: str, language: str = "py3") -> dict:
        """Test solution and return result."""
        
        logger.info("=" * 60)
        logger.info("TESTING SOLUTION WITH GRADER")
        logger.info("=" * 60)
        logger.info(f"Problem: {problem_alias}")
        logger.info(f"Language: {language}")
        logger.info(f"Code length: {len(code)} chars")
        logger.info("=" * 40)
        logger.info("SOLUTION CODE")
        logger.info("=" * 40)
        logger.info(code)
        logger.info("=" * 40)
        
        try:
            # Submit solution
            data = {
                'problem_alias': problem_alias,
                'language': language,
                'source': code
            }
            
            url = f"{self.api.api_url}/run/create"
            logger.info(f"Submitting to: {url}")
            
            response = self.api.session.post(url, data=data, timeout=(5, 30))
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") != "ok":
                logger.error(f"Submission failed: {result.get('error', 'Unknown error')}")
                return {}
            
            guid = result.get('guid')
            logger.info(f"Submission successful")
            logger.info(f"GUID: {guid}")
            logger.info(f"Submit delay: {result.get('submit_delay', 0)} minutes")
            
            # Wait for result
            return self._wait_for_result(guid)
            
        except Exception as e:
            logger.error(f"Solution testing failed: {str(e)}")
            return {}

    def _wait_for_result(self, run_guid: str, max_wait_time: int = 30) -> dict:
        """Wait for grading result."""
        
        logger.info("Waiting for grading result...")
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
                        logger.info(f"Status: {status} | Verdict: {verdict}")
                        last_status = status
                    
                    if status in ['ready', 'done']:
                        logger.info("=" * 40)
                        logger.info("GRADING RESULT")
                        logger.info("=" * 40)
                        logger.info(f"Verdict: {verdict}")
                        logger.info(f"Score: {result.get('score', 0.0)}")
                        logger.info(f"Runtime: {result.get('runtime', 0)}ms")
                        logger.info(f"Memory: {result.get('memory', 0)}KB")
                        execution = result.get('execution', '')
                        if execution:
                            logger.info(f"Execution: {execution}")
                        output = result.get('output', '')
                        if output:
                            logger.info(f"Output: {output}")
                        logger.info("=" * 40)
                        return result
                    
                    if status in ['error', 'compile_error']:
                        logger.error("=" * 40)
                        logger.error("GRADING ERROR")
                        logger.error("=" * 40)
                        logger.error(f"Status: {status}")
                        logger.error(f"Verdict: {verdict}")
                        execution = result.get('execution', '')
                        if execution:
                            logger.error(f"Execution: {execution}")
                        output = result.get('output', '')
                        if output:
                            logger.error(f"Output: {output}")
                        logger.error("=" * 40)
                        return result
                
                time.sleep(2)
                
            except Exception as e:
                logger.warning(f"Status check failed: {str(e)}")
                time.sleep(2)
        
        logger.warning("Grading timeout - no result received")
        return {}


class CompleteDemo:
    """Main demo orchestrator."""

    def __init__(self):
        self.api = OmegaUpAPI()
        self.ai = CompleteDemoAI()
        self.grader = CompleteDemoGrader(self.api)

    def run_complete_workflow(self, problem_alias: str, language: str = "py3") -> bool:
        """Run the complete editorial generation workflow."""
        
        logger.info("=" * 80)
        logger.info("STARTING COMPLETE EDITORIAL GENERATION WORKFLOW")
        logger.info("=" * 80)
        logger.info(f"Problem alias: {problem_alias}")
        logger.info(f"Language: {language}")
        logger.info("=" * 80)
        
        try:
            # Step 1: Get problem details
            logger.info("STEP 1: FETCHING PROBLEM DETAILS")
            logger.info("-" * 40)
            problem_data = self.api.get_problem(problem_alias)
            title = problem_data.get('title', problem_alias)
            logger.info(f"Successfully fetched: {title}")
            
            # Step 2: Generate initial solution
            logger.info("")
            logger.info("STEP 2: GENERATING INITIAL SOLUTION")
            logger.info("-" * 40)
            solution_code = self.ai.generate_solution_code(problem_data, language)
            
            # Step 3: Test solution
            logger.info("")
            logger.info("STEP 3: TESTING SOLUTION WITH GRADER")
            logger.info("-" * 40)
            test_result = self.grader.test_solution(problem_alias, solution_code, language)
            
            if not test_result:
                logger.error("Failed to get grading result")
                return False
            
            verdict = test_result.get('verdict', 'unknown')
            score = test_result.get('score', 0.0)
            
            logger.info("")
            logger.info("STEP 3 RESULT:")
            logger.info(f"  Verdict: {verdict}")
            logger.info(f"  Score: {score}")
            
            # Step 4: Handle result
            if verdict == 'AC':
                logger.info("")
                logger.info("STEP 4: SOLUTION ACCEPTED - PROCEEDING TO EDITORIAL")
                logger.info("-" * 40)
                logger.info("Solution accepted on first try")
                final_code = solution_code
                final_verdict = verdict
                final_score = score
            else:
                logger.info("")
                logger.info("STEP 4: SOLUTION REJECTED - ATTEMPTING REGENERATION")
                logger.info("-" * 40)
                
                # Prepare error feedback
                error_info = f"Verdict: {verdict}, Score: {score}"
                execution = test_result.get('execution', '')
                output = test_result.get('output', '')
                if execution:
                    error_info += f", Execution: {execution}"
                if output:
                    error_info += f", Output: {output}"
                
                logger.info(f"Preparing error feedback for regeneration:")
                logger.info(f"  {error_info}")
                
                # Step 5: Regenerate solution with error feedback
                logger.info("")
                logger.info("STEP 5: REGENERATING SOLUTION WITH ERROR FEEDBACK")
                logger.info("-" * 40)
                retry_code = self.ai.generate_solution_code(problem_data, language, error_info)
                
                # Test retry solution
                logger.info("")
                logger.info("STEP 5b: TESTING REGENERATED SOLUTION")
                logger.info("-" * 40)
                retry_result = self.grader.test_solution(problem_alias, retry_code, language)
                
                if retry_result:
                    retry_verdict = retry_result.get('verdict', 'unknown')
                    retry_score = retry_result.get('score', 0.0)
                    
                    logger.info("")
                    logger.info("RETRY RESULT:")
                    logger.info(f"  Original: {verdict} (score: {score})")
                    logger.info(f"  Retry:    {retry_verdict} (score: {retry_score})")
                    
                    # Use the better solution
                    if retry_verdict == 'AC' or retry_score > score:
                        final_code = retry_code
                        final_verdict = retry_verdict
                        final_score = retry_score
                        logger.info("Decision: Using retry solution (better result)")
                    else:
                        final_code = solution_code
                        final_verdict = verdict
                        final_score = score
                        logger.info("Decision: Using original solution (retry didn't improve)")
                else:
                    logger.warning("Retry testing failed, using original solution")
                    final_code = solution_code
                    final_verdict = verdict
                    final_score = score
            
            # Step 6: Generate editorial
            logger.info("")
            logger.info("STEP 6: GENERATING EDITORIAL")
            logger.info("-" * 40)
            editorial = self.ai.generate_editorial(problem_data, final_code, final_verdict, final_score)
            
            # Step 7: Update problem editorial
            logger.info("")
            logger.info("STEP 7: UPDATING PROBLEM EDITORIAL")
            logger.info("-" * 40)
            commit_message = f"AI-generated editorial based on {final_verdict} solution"
            logger.info(f"Commit message: {commit_message}")
            
            success = self.api.submit_editorial_all_languages(
                problem_alias=problem_alias,
                content=editorial,
                message=commit_message
            )
            
            if success:
                logger.info("")
                logger.info("=" * 80)
                logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
                logger.info("=" * 80)
                logger.info("FINAL SUMMARY:")
                logger.info(f"  Problem: {title}")
                logger.info(f"  Problem alias: {problem_alias}")
                logger.info(f"  Final verdict: {final_verdict}")
                logger.info(f"  Final score: {final_score}")
                logger.info(f"  Editorial length: {len(editorial)} characters")
                logger.info(f"  Languages updated: ES, EN, PT")
                logger.info("=" * 80)
                return True
            else:
                logger.error("Editorial update failed")
                return False
                
        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            return False


def main():
    """Main entry point."""
    print("Complete Editorial Generator Demo")
    print("=" * 50)
    
    # Get problem alias from command line or use default
    problem_alias = sys.argv[1] if len(sys.argv) > 1 else "sumas"
    language = sys.argv[2] if len(sys.argv) > 2 else "py3"
    
    try:
        demo = CompleteDemo()
        success = demo.run_complete_workflow(problem_alias, language)
        
        if success:
            print("\nWorkflow completed successfully!")
            print(f"Check the editorial at: http://localhost:8001/arena/problem/{problem_alias}#solution")
            return 0
        else:
            print("\nWorkflow failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 