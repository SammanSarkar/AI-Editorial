*This editorial was generated using an AI model to help provide educational content for competitive programming practice.*

---

# Problem Analysis

The problem is asking us to process the results of a chocolate tasting competition. Each of the five contestants is given a chocolate to taste and they have to guess its type. The types of chocolates are represented by integers from 1 to 4. The correct type of the chocolate is also given to us. We are required to find out the number of contestants who guessed the correct type and the sum of all the guesses.

# Key Insights

The key insight to solve this problem is to realize that we can solve it by iterating through the guesses of each contestant and comparing it with the correct type. If the guess is correct, we increment a counter. Regardless of whether the guess is correct or not, we add the guess to a sum variable.

# Algorithm/Approach

1. Read the correct type of chocolate from the input.
2. Initialize a counter and a sum variable to 0.
3. For each contestant, read their guess from the input.
4. If the guess is equal to the correct type, increment the counter.
5. Add the guess to the sum variable, regardless of whether it is correct or not.
6. After processing all the guesses, print the counter and the sum variable.

# Time & Space Complexity

The time complexity of the solution is O(1) because we are only processing a fixed number of inputs (5 contestants). The space complexity is also O(1) because we are only storing a fixed number of variables (the correct type, the counter, and the sum).

# Implementation Details

The implementation is straightforward once we understand the problem and the approach. We just need to be careful to initialize the counter and the sum variable to 0 before we start processing the guesses.

# Solution Code

```cpp20-gcc
#include <iostream>

using namespace std;

int main() {
    // Read the correct type of chocolate
    int correctType;
    cin >> correctType;

    // Initialize the counter and the sum
    int correctGuesses = 0;
    int sumOfGuesses = 0;

    // Process the guesses of each contestant
    for (int i = 0; i < 5; i++) {
        int guess;
        cin >> guess;

        // If the guess is correct, increment the counter
        if (guess == correctType) {
            correctGuesses++;
        }

        // Add the guess to the sum
        sumOfGuesses += guess;
    }

    // Print the number of correct guesses and the sum of all guesses
    cout << correctGuesses << " " << sumOfGuesses;

    return 0;
}
```

This solution reads the correct type of chocolate from the input, then initializes a counter and a sum variable to 0. It then processes the guesses of each contestant. If a guess is equal to the correct type, it increments the counter. Regardless of whether a guess is correct or not, it adds the guess to the sum variable. After processing all the guesses, it prints the counter and the sum variable.