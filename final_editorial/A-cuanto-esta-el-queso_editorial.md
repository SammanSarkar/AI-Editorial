*This editorial was generated using an AI model to help provide educational content for competitive programming practice.*

---

# Problem Analysis
The problem is asking us to calculate the total money earned by a cheese seller. The cheese seller sells cheese at a base price of $K$ soles. However, if the buyer is a foreigner, an extra tax of $X$ soles is added to the base price. The seller sells cheese to $N$ people, who can be either foreigners or locals. The foreigners are represented by the letter 'A' and the locals by the letter 'B'. We are required to calculate the total money earned by the seller.

# Key Insights
The key insight to solve this problem is understanding that the total money earned by the seller is the sum of the base price of the cheese and the extra tax for each foreigner. We can calculate this by iterating over each buyer, adding the base price to a counter, and if the buyer is a foreigner, also adding the tax.

# Algorithm/Approach
1. Initialize a counter `val` to 0. This will hold the total money earned by the seller.
2. Iterate over each buyer:
   - Add the base price $K$ to `val`.
   - If the buyer is a foreigner (represented by 'A'), add the tax $X$ to `val`.
3. Print `val` as the total money earned by the seller.

# Time & Space Complexity
The time complexity of this solution is O(N) because we iterate over each buyer once. The space complexity is O(1) because we only use a constant amount of space to store the input parameters and the counter `val`.

# Implementation Details
In the solution code, we use a for loop to iterate over each buyer. We read the buyer's nationality as a character `c` and add the base price to `val`. If `c` is 'A', we also add the tax to `val`.

# Solution Code
```cpp11-gcc
#include "bits/stdc++.h"
using namespace std;

void solve() {
    // Read the input parameters
    int n, k, x;
    cin >> n >> k >> x;

    // Initialize the total money earned by the seller
    int val = 0;

    // Iterate over each buyer
    for(int i = 0; i < n; ++i) {
        // Read the buyer's nationality
        char c;
        cin >> c;

        // Add the base price to the total money earned
        val += k;

        // If the buyer is a foreigner, add the tax
        if(c == 'A') {
            val += x;
        }
    }

    // Print the total money earned by the seller
    cout << val << "\n";
}

int main() {
    ios::sync_with_stdio(0);
    cin.tie(0);
    solve();
    return 0;
}
```
This solution reads the input parameters, calculates the total money earned by the seller, and prints the result. The `ios::sync_with_stdio(0); cin.tie(0);` lines are used to speed up input and output in C++.