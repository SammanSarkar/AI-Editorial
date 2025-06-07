#!/usr/bin/env python3
"""
Demo script for the editorial generator.

This script demonstrates the complete workflow:
1. Connect to omegaUp API
2. Fetch problem details for 'sumas' (from bootstrap)
3. Generate editorial
4. Submit the editorial to all languages
5. Verify the submission worked

Usage: python demo.py
"""

import sys
import os
import time
from pathlib import Path

# Add the editorial_generator package to the path
sys.path.insert(0, str(Path(__file__).parent))

from editorial_generator.api import OmegaUpAPI
from editorial_generator.ai import AIGenerator
from editorial_generator.logger import logger


def main():
    """Run the demo."""
    print("🚀 omegaUp Editorial Generator Demo")
    print("=" * 50)
    
    try:
        # Step 1: Initialize API and AI clients
        print("📡 Step 1: Connecting to omegaUp API...")
        api = OmegaUpAPI()
        ai = AIGenerator()
        print(" Connected successfully")
        
        # Step 2: Test problem
        problem_alias = "sumas"
        print(f"\n🎯 Step 2: Working with problem '{problem_alias}'")
        
        # Step 3: Get current solution state
        print(" Step 3: Checking current state...")
        current_solution = api.get_problem_solution(problem_alias)
        if current_solution:
            print(f"📝 Current solution: {len(current_solution)} characters")
        else:
            print("📝 No current solution found")
        
        # Step 4: Fetch problem details
        print(f"\n🔍 Step 4: Fetching problem details...")
        problem_data = api.get_problem(problem_alias)
        
        # Step 5: Generate editorial
        print(f"\n Step 5: Generating editorial...")
        editorial = ai.generate_editorial(problem_data)
        
        # Step 6: Submit editorial using comprehensive all-languages method
        commit_message = f"Editorial Update - {time.strftime('%Y-%m-%d %H:%M:%S')}"
        print(f"\n Step 6: Submitting editorial to all languages...")
        
        success = api.submit_editorial_all_languages(
            problem_alias=problem_alias,
            content=editorial,
            message=commit_message
        )
        
        if success:
            print(" Editorial submission completed!")
            
            # Step 7: Verification
            print(f"\n🔍 Step 7: Verifying updates...")
            time.sleep(3)  # Allow processing time
            
            verification_success = False
            languages_to_check = ['es', 'en', 'pt']
            
            for lang in languages_to_check:
                try:
                    new_solution = api.get_problem_solution(problem_alias, lang)
                    
                    if new_solution:
                        # Check if it's our new editorial (not the old one)
                        is_our_editorial = (
                            "Editorial:" in new_solution or 
                            "AI-generated" in new_solution or
                            "IA" in new_solution or
                            len(new_solution) > 500  # Our editorials are longer
                        )
                        
                        if is_our_editorial:
                            print(f" {lang.upper()}: Updated successfully ({len(new_solution)} chars)")
                            verification_success = True
                        else:
                            print(f"⚠️ {lang.upper()}: Still old solution ({len(new_solution)} chars)")
                    else:
                        print(f"❌ {lang.upper()}: No solution found")
                        
                except Exception as e:
                    print(f"❌ {lang.upper()}: Error - {e}")
            
            if verification_success:
                print(f"\n🎉 DEMO COMPLETED SUCCESSFULLY!")
                print(f"🌐 Check: http://localhost:8001/arena/problem/{problem_alias}#solution")
                print(f"💡 Try switching languages if needed")
            else:
                print("⚠️ Editorial submitted but verification inconclusive")
        else:
            print("❌ Editorial submission failed")
            return
            
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return

    print(f"\n Summary:")
    print(f"   • Problem: {problem_alias}")
    print(f"   • Editorial: {len(editorial) if 'editorial' in locals() else 'N/A'} characters")
    print(f"   • Status: {'SUCCESS' if success else 'FAILED'}")


if __name__ == "__main__":
    main() 