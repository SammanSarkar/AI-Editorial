"""Command-line interface for the editorial generator."""

import os
import sys
import argparse

from . import __version__
from .api import OmegaUpAPI
from .ai import AIGenerator
from .logger import logger


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate and submit problem editorials using AI"
    )
    parser.add_argument(
        "problem_alias",
        help="Problem alias to generate editorial for (e.g., 'sumas')"
    )
    parser.add_argument(
        "--message",
        default="AI-generated editorial",
        help="Commit message for the editorial"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Only show the generated editorial without submitting"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    return parser.parse_args()


def main():
    """Main entry point for the CLI."""
    try:
        args = parse_args()
        
        # Initialize components
        print("🔧 Initializing API client...")
        api = OmegaUpAPI()
        ai = AIGenerator()
        
        # Validate and get problem
        print(f"🔍 Fetching problem '{args.problem_alias}'...")
        problem = api.get_problem(args.problem_alias)
        
        # Generate editorial
        print(f"📝 Generating editorial...")
        editorial = ai.generate_editorial(problem)
        
        # Show preview
        print("\n" + "=" * 60)
        print("📄 GENERATED EDITORIAL")
        print("=" * 60)
        print(editorial)
        print("=" * 60 + "\n")
        
        # Submit if not in preview mode
        if not args.preview:
            print(" Submitting editorial to all languages...")
            
            if api.submit_editorial_all_languages(args.problem_alias, editorial, args.message):
                print(f" Editorial successfully submitted!")
                
                # Show URL to view the editorial
                base_url = os.getenv('OMEGAUP_BASE_URL', 'http://localhost:8001')
                solution_url = f"{base_url}/arena/problem/{args.problem_alias}/#solution"
                print(f"🌐 View at: {solution_url}")
                
            else:
                print("❌ Failed to submit editorial", file=sys.stderr)
                return 1
        else:
            print(" Preview mode - editorial not submitted")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 1
        
    except Exception as e:
        logger.error(f"CLI error: {str(e)}")
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
