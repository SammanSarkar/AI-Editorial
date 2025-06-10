*This editorial was generated using an AI model to help provide educational content for competitive programming practice.*

---

# Problem Analysis
The problem is asking us to perform two separate calculations on a list of integers. First, we need to calculate the sum of all negative numbers. Second, we need to calculate the average of all positive numbers. The list of integers can contain both positive and negative numbers.

# Key Insights
The main insight to solve this problem is understanding that we need to separate the numbers into two categories: positive and negative. We then perform different calculations on each category. For the negative numbers, we simply add them up. For the positive numbers, we add them up and then divide by the total number of positive numbers to get the average.

# Algorithm/Approach
1. Initialize two variables, one for the sum of negative numbers and one for the sum of positive numbers. Also, initialize a counter for the number of positive numbers.
2. Read the number of elements, n.
3. Loop over the n elements:
   - If the element is negative, add it to the sum of negative numbers.
   - If the element is positive, add it to the sum of positive numbers and increment the counter of positive numbers.
4. After the loop, print the sum of negative numbers.
5. Calculate the average of positive numbers by dividing the sum of positive numbers by the counter of positive numbers. Print this average.

# Time & Space Complexity
The time complexity of this solution is O(n), where n is the number of elements. This is because we are looping over the elements once. The space complexity is O(1), because we are only using a fixed amount of space to store the sums and the counter.

# Implementation Details
The implementation is straightforward once the algorithm is understood. However, one detail to note is that when calculating the average, we need to ensure that we are performing floating-point division, not integer division. This is achieved by declaring the sum of positive numbers as a float.

# Solution Code
```cpp17-gcc
#include <bits/stdc++.h>
using namespace std;

int main() 
{
  int n, m, i, neg, x;
  float pos;

  // Read the number of elements
  scanf("%d",&n);
  
  // Initialize the sums and the counter
  neg = pos = x = 0;
  
  // Loop over the elements
  for(i=0; i<n; i++){
    scanf("%d",&m);
    if(m<0)
      neg += m;  // Add to the sum of negative numbers
    else{
      pos += m;  // Add to the sum of positive numbers
      x++;       // Increment the counter of positive numbers
    }
  }
  
  // Print the sum of negative numbers and the average of positive numbers
  printf("%d\n%.1f", neg, pos/x);
  
  return 0;
}
```
This code reads the elements one by one, performs the necessary calculations, and prints the results. The use of `printf` and `scanf` for input and output ensures fast execution, which is important in competitive programming.