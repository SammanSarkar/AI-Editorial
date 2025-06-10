*This editorial was generated using an AI model to help provide educational content for competitive programming practice.*

---

# Problem Analysis

The problem is asking us to help Salvador, a grumpy teacher, to calculate the average grades of his students in three subjects: video game programming, mobile programming, and database programming. The grades are given in decimal numbers between 0 and 100. After calculating the average, we need to sort the students in descending order of their average grades. If two students have the same average, the student with the lower roll number should come first. 

# Key Insights

The key insights needed to solve this problem are:

- We need to calculate the average grade for each student. The average is calculated by adding the three grades and dividing the sum by 3.
- We need to sort the students based on their average grades. If two students have the same average grade, the student with the lower roll number should come first.
- We can use a data structure to store the roll number and the average grade of each student. A struct in C++ can be used for this purpose.
- We can use the sort function in C++ to sort the students. We need to provide a custom comparator function to the sort function to sort the students based on the conditions given in the problem.

# Algorithm/Approach

1. Read the number of students.
2. For each student, read the roll number and the grades in the three subjects.
3. Calculate the average grade for the student and store it along with the roll number in a struct.
4. Add the struct to a vector.
5. After reading the data for all students, sort the vector using the sort function. Provide a custom comparator function to sort the students based on their average grades and roll numbers.
6. Print the roll numbers and the average grades of the students in the sorted order.

# Time & Space Complexity

The time complexity of the solution is O(n log n) due to the sort function, where n is the number of students. The space complexity is O(n) for storing the data of the students.

# Implementation Details

The implementation uses a struct to store the roll number and the average grade of each student. The struct has four fields: lista (roll number), video (grade in video game programming), movil (grade in mobile programming), bd (grade in database programming), and calif (average grade). 

The compare function is a custom comparator function used by the sort function to sort the students. It returns true if the average grade of the first student is greater than the average grade of the second student. If the average grades are equal, it returns true if the roll number of the first student is less than the roll number of the second student.

# Solution Code

```cpp
#include <iostream>
#include <vector>
#include <algorithm>
#include <stdio.h>
using namespace std;

struct Student{
    int rollNumber;
    float videoGameGrade;
    float mobileProgrammingGrade;
    float databaseGrade;
    int averageGrade;
};

bool compare (Student x, Student y)
{
    if(x.averageGrade > y.averageGrade)
        return true;
    else if(x.averageGrade == y.averageGrade)
        return x.rollNumber < y.rollNumber;
    else
        return false;
}

int main()
{
    int n;
    cin >> n;
    vector <Student> students;
    Student student;

    for(int i = 0; i < n; i++)
    {
        cin >> student.rollNumber;
        cin >> student.videoGameGrade;
        cin >> student.mobileProgrammingGrade;
        cin >> student.databaseGrade;
        student.averageGrade = (student.videoGameGrade + student.mobileProgrammingGrade + student.databaseGrade) / 3;
        students.push_back(student);
    }

    sort(students.begin(), students.end(), compare);

    for(int i = 0; i < n; i++)
    {
        printf("%d %d\n", students[i].rollNumber, students[i].averageGrade);
    }

    return 0;
}
```
This code first reads the number of students and then for each student, it reads the roll number and the grades in the three subjects. It calculates the average grade and stores it along with the roll number in a struct. The struct is then added to a vector. After reading the data for all students, it sorts the vector and then prints the roll numbers and the average grades of the students in the sorted order.