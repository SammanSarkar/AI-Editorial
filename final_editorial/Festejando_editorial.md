*This editorial was generated using an AI model to help provide educational content for competitive programming practice.*

---

# Problem Analysis
The problem is asking to find the minimum distance you need to walk to invite at least one member from each group of friends. The street is represented by a string of digits, where each digit represents a house and the group of friends living in it. The digit 0 means no friends live there. The goal is to find the minimum distance you need to walk (in meters) and the maximum number of groups you can invite.

# Key Insights
The key insight to solve this problem is to realize that you can invite a group of friends by visiting any house where a member of that group lives. Therefore, you should aim to minimize the distance walked by choosing the houses to visit strategically. 

# Algorithm/Approach
1. Initialize an array to keep track of the distance to each group of friends. Set all distances to a large constant value.
2. Iterate over the houses in the street. For each house, if a group of friends lives there, set their distance to 0. If not, increase their distance by 50 (the distance to the next house).
3. Keep track of the maximum distance to any group of friends. This is the minimum distance you need to walk to invite all groups.
4. After visiting each house, check if you can invite all groups by walking less distance than before. If so, update the minimum distance.
5. Repeat steps 2-4 for all houses in the street.
6. The minimum distance and the number of groups you can invite are the solution to the problem.

# Time & Space Complexity
The time complexity of the solution is O(n), where n is the number of houses in the street. This is because we iterate over the houses once.

The space complexity is O(1), as we only need a constant amount of space to store the distances to each group of friends and the minimum distance.

# Implementation Details
The implementation uses a string to represent the street and an array to store the distances to each group of friends. The distances are initialized to a large constant value to ensure that we can update them correctly when we visit a house where a group of friends lives. We use the ASCII value of the digits in the string to index into the array.

# Solution Code
```cpp
#include <iostream>
#include <string>
#include <cstring>
using namespace std;

int main(){
    int n, g, tam, maximo, minimo, cte, v[10];
    string s;
    cin >> n;
    while(n--){
        cin >> s;
        tam = s.size();
        memset(v, 0, sizeof(v));
        for(int i = 0; i < tam; i++)
            v[s[i]-'0'] = 1;
        for(int i = 1, g = 0; i < 10; i++)
            g+=v[i];
        cte = (tam+10)*50;
        for(int i = 0; i < 10; i++)
            v[i] = cte;
        if(g == 0)
            minimo = 0;
        else{
            minimo = cte;
            for(int i = 0; i < tam; i++){
                maximo = 0;
                for(int j = 1; j < 10; j++){
                    if(s[i] == (j+'0'))
                        v[j] = 0;
                    else if(v[j] != cte)
                        v[j]+=50;
                }
                for(int j = 1, cont = 0; j < 10; j++)
                    if(v[j] != cte && (++cont) && maximo < v[j])
                        maximo = v[j];
                if(minimo > maximo && cont == g)
                    minimo = maximo;
            }
        }
        cout << "Tengo que caminar "<<minimo<<" metros y puedo invitar a "<<g<<" grupos.\n";
    }
    return 0;
}
```
In this code, we first read the number of test cases and the string representing the street. We then initialize the array of distances and count the number of groups of friends. We then iterate over the houses in the street, updating the distances and checking if we can invite all groups by walking less distance. Finally, we print the minimum distance and the number of groups we can invite.