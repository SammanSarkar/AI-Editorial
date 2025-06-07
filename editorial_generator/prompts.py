"""
AI Prompt Templates for Editorial Generator

This module contains all the prompt templates used for:
- Solution code generation
- Editorial generation
- Error feedback handling
"""

def get_code_generation_prompt(title: str, statement: str, language: str, error_feedback: str = None) -> str:
    """Generate prompt for solution code generation."""
    
    lang_info = {
        "py3": "Python 3",
        "cpp17-gcc": "C++17",
        "java": "Java",
        "cpp11-gcc": "C++11",
        "cpp14-gcc": "C++14",
        "cpp20-gcc": "C++20",
        "c11-gcc": "C11",
        "cs": "C#",
        "rb": "Ruby",
        "go": "Go",
        "rs": "Rust",
        "js": "JavaScript",
        "kt": "Kotlin",
        "pas": "Pascal"
    }
    
    prompt = f"""Generate a working solution for this programming problem:

Problem: {title}
Statement: {statement}

Requirements:
- Write code in {lang_info.get(language, language)}
- The solution should be correct and efficient
- Handle all edge cases mentioned in the problem
- Follow proper competitive programming practices
- Include only the code, no explanations
- Handle input/output exactly as specified in the problem
- Consider time and memory constraints
- Use appropriate data structures and algorithms

"""
    
    if error_feedback:
        prompt += f"""
IMPORTANT: The previous solution failed with this error:
{error_feedback}

Please analyze the error and generate a corrected solution that addresses the specific issue.
Common issues to check:
- Input/output format mismatch
- Integer overflow (use long long in C++ if needed)
- Array bounds checking
- Edge cases (empty input, single element, etc.)
- Time limit exceeded (optimize algorithm)
- Wrong algorithm approach
"""

    prompt += """
Generate ONLY the source code without any markdown formatting or explanations.
"""

    return prompt   


def get_editorial_generation_prompt(title: str, statement: str, solution_code: str, verdict: str, language: str = "py3") -> str:
    """Generate prompt for editorial generation."""
    
    lang_info = {
        "py3": "Python 3",
        "cpp17-gcc": "C++17",
        "java": "Java",
        "cpp11-gcc": "C++11",
        "cpp14-gcc": "C++14", 
        "cpp20-gcc": "C++20",
        "c11-gcc": "C11",
        "cs": "C#",
        "rb": "Ruby",
        "go": "Go",
        "rs": "Rust",
        "js": "JavaScript",
        "kt": "Kotlin",
        "pas": "Pascal"
    }
    
    prompt = f"""Write a editorial for this programming problem:

Problem: {title}
Language: {lang_info.get(language, language)}
Statement: {statement}

Working Solution (Verdict: {verdict}):
```{language}
{solution_code}
```

Please write a detailed editorial that includes:

1. **Problem Understanding**
   - Clear explanation of what the problem is asking
   - Key constraints and requirements
   - Input/output format clarification

2. **Solution Approach**
   - Main algorithm or technique used
   - Why this approach works
   - Step-by-step reasoning

3. **Implementation Details**
   - Key implementation points
   - Important edge cases to handle
   - Common pitfalls to avoid

4. **Complexity Analysis**
   - Time complexity with explanation
   - Space complexity with explanation
   - Why this complexity is acceptable for the given constraints

5. **Code Walkthrough**
   - Explanation of the working solution
   - How each part contributes to solving the problem

6. **Alternative Approaches** (if applicable)
   - Other ways to solve the problem
   - Trade-offs between different approaches

Format the editorial in clear markdown with proper sections and headers.
Use educational language that helps contestants learn.
Include insights that would help someone understand not just this problem, but similar problems too.
"""

    return prompt


def get_code_system_prompt() -> str:
    """Get the system prompt for code generation."""
    return """You are an expert competitive programmer with extensive experience in algorithmic problem solving. 

Your expertise includes:
- Data structures and algorithms
- Dynamic programming
- Graph theory
- Number theory
- Geometry
- String algorithms
- Greedy algorithms
- Divide and conquer

When generating solutions:
- Always prioritize correctness over cleverness
- Write clean, readable code
- Handle edge cases properly
- Consider time and space complexity
- Use appropriate data types to avoid overflow
- Follow language-specific best practices
- Generate only working code solutions without explanations"""


def get_editorial_system_prompt() -> str:
    """Get the system prompt for editorial generation."""
    return """You are an expert at writing clear, educational programming contest editorials.

Your editorials should:
- Be accessible to competitive programmers of various skill levels
- Explain the reasoning behind the solution approach
- Include step-by-step explanations
- Highlight key insights and techniques
- Provide complexity analysis
- Help readers understand similar problems
- Use clear, structured markdown formatting
- Be comprehensive yet concise
- Focus on educational value

Write editorials that not only explain the solution but also teach problem-solving techniques and algorithmic thinking."""


def get_mock_code_template(title: str, language: str) -> str:
    """Generate mock code when OpenAI is not available."""
    
    title_lower = title.lower()
    
    if language == "py3":
        if "suma" in title_lower or "add" in title_lower:
            return """# Solution for addition problem
a, b = map(int, input().split())
print(a + b)
"""
        
        else:
            return """# Mock solution
data = input().strip()
# Process input according to problem requirements
print("Mock output")
"""
    
    elif language in ["cpp17-gcc", "cpp11-gcc", "cpp14-gcc", "cpp20-gcc"]:
        if "suma" in title_lower or "add" in title_lower:
            return """#include <iostream>
using namespace std;

int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << endl;
    return 0;
}
"""
        else:
            return """#include <iostream>
using namespace std;

int main() {
    // Mock solution
    cout << "Mock output" << endl;
    return 0;
}
"""
    
    elif language == "java":
        return """import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        // Mock solution
        System.out.println("Mock output");
    }
}
"""
    
    else:
        return f"// Mock solution for {title} in {language}"


def get_mock_editorial_template(title: str, solution_code: str, verdict: str, language: str = "py3") -> str:
    """Generate mock editorial when OpenAI is not available."""
    
    lang_info = {
        "py3": "Python 3",
        "cpp17-gcc": "C++17",
        "java": "Java",
        "cpp11-gcc": "C++11",
        "cpp14-gcc": "C++14",
        "cpp20-gcc": "C++20",
        "c11-gcc": "C11",
        "cs": "C#",
        "rb": "Ruby", 
        "go": "Go",
        "rs": "Rust",
        "js": "JavaScript",
        "kt": "Kotlin",
        "pas": "Pascal"
    }
    
    return f"""# Editorial: {title}

## Problem Understanding
This problem requires implementing a solution for {title}. The key is to understand the input/output format and apply the appropriate algorithm.

## Solution Approach
Our approach involves:
1. Reading the input according to the specified format
2. Processing the data using the most suitable algorithm
3. Producing the output in the required format

The solution uses {lang_info.get(language, language)} and follows competitive programming best practices.

## Implementation Details
The implementation handles all specified constraints and edge cases. Key points include:
- Proper input parsing
- Efficient processing algorithm
- Correct output formatting

## Working Solution
The following solution achieved verdict **{verdict}**:

```{language}
{solution_code.strip()}
```

## Complexity Analysis
- **Time Complexity**: O(n) where n represents the main input parameter
- **Space Complexity**: O(1) additional space beyond input storage

## Key Insights
- The problem tests fundamental algorithmic concepts
- Careful attention to input/output format is crucial
- The solution demonstrates efficient problem-solving techniques

## Notes
This editorial was generated as part of an AI-powered editorial generation system. The solution correctly handles the problem constraints and produces the expected output format.
""" 