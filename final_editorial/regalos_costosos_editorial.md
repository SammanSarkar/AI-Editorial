*This editorial was generated using an AI model to help provide educational content for competitive programming practice.*

---

# Problem Analysis
The problem asks us to help Zagreb, who wants to give gifts to his N nephews. He has a budget of B units of currency. Each nephew i wants a gift that costs P_i units and has a shipping cost of S_i units. Zagreb also has a special coupon that he can use to buy a gift at half its price. We are to determine the maximum number of nephews Zagreb can give gifts to, given his budget and the cost of gifts.

# Key Insights
The key insights to solve this problem are:
1. Zagreb should use his coupon on the most expensive gift. This is because the coupon reduces the price by half, so using it on the most expensive gift will save the most money.
2. After using the coupon, Zagreb should buy the cheapest gifts first. This is because he wants to maximize the number of gifts he can buy, and buying the cheapest gifts first allows him to do this.

# Algorithm/Approach
1. Read the number of nephews N and the budget B.
2. Read the price P_i and the shipping cost S_i for each nephew.
3. Sort the gifts by their total cost (P_i + S_i).
4. For each gift, try using the coupon on it and calculate how many gifts can be bought with the remaining budget. Keep track of the maximum number of gifts that can be bought.
5. Print the maximum number of gifts that can be bought.

# Time & Space Complexity
The time complexity of the solution is O(N^2), due to the nested loop in the `try_coupon` function. The space complexity is O(N), due to the arrays P and S that store the price and shipping cost of each gift.

# Implementation Details
The implementation uses a simple bubble sort to sort the gifts by their total cost. This is done in the `sort_by_p_plus_s` function. The `try_coupon` function calculates how many gifts can be bought if the coupon is used on a specific gift. It does this by subtracting the discounted cost of the gift from the budget and then buying as many of the cheapest gifts as possible with the remaining budget.

# Solution Code
```cpp
#include <stdio.h>
#define MAX_N 1000

int N, B, P[MAX_N], S[MAX_N];

// Sort the gifts by their total cost (price + shipping)
void sort_by_p_plus_s(void)
{
  int i, tmp, done=0;

  while (!done) {
    done = 1;
    for (i=0; i<N-1; i++)
      if (P[i]+S[i] > P[i+1]+S[i+1]) {
        tmp = P[i]; P[i] = P[i+1]; P[i+1] = tmp;
        tmp = S[i]; S[i] = S[i+1]; S[i+1] = tmp;
        done = 0;
      }
  }
}

// Calculate how many gifts can be bought if the coupon is used on gift c
int try_coupon(int c)
{
  int i, budget = B - (P[c]/2+S[c]), total=1;

  if (budget < 0) return 0;

  for (i=0; i<N; i++) 
    if (P[i]+S[i] <= budget && i!=c) {
      budget -= P[i]+S[i];
      total++;
    }

  return total;
}

int main(void)
{
  int i, best=0;

  // Read the number of nephews and the budget
  scanf ("%d %d", &N, &B);
  
  // Read the price and shipping cost for each gift
  for (i=0; i<N; i++)
    scanf ("%d %d", &P[i], &S[i]);

  // Sort the gifts by their total cost
  sort_by_p_plus_s();

  // Try using the coupon on each gift and keep track of the maximum number of gifts that can be bought
  for (i=0; i<N; i++)
    if (try_coupon(i) > best) 
      best = try_coupon(i);

  // Print the maximum number of gifts that can be bought
  printf ("%d\n", best);
  
  return 0;
}
```
This code reads the input, sorts the gifts by their total cost, and then tries using the coupon on each gift. It keeps track of the maximum number of gifts that can be bought and prints this number at the end.