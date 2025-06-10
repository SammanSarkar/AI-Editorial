*This editorial was generated using an AI model to help provide educational content for competitive programming practice.*

---

# Problem Analysis
The problem is asking us to create a program that will encrypt messages using the Caesar cipher. The Caesar cipher is a type of substitution cipher where each letter in the plaintext is shifted a certain number of places down the alphabet. In this problem, Lorena uses a shift of 5 and Limon uses a shift of 6. We are given the number of messages to encrypt, who the message is from, and the message itself. The output should be the encrypted message.

# Key Insights
The key insight to solve this problem is understanding how the Caesar cipher works and how to implement it in code. We need to shift each letter in the message by a certain number of places. If the letter is from Lorena, we shift it by 5 places. If it's from Limon, we shift it by 6 places. We also need to handle the case where the shift would go beyond 'z', in which case we wrap around to the beginning of the alphabet.

# Algorithm/Approach
1. Read the number of messages to encrypt.
2. For each message:
   1. Read who the message is from and the message itself.
   2. Initialize an empty string to store the encrypted message.
   3. For each character in the message:
      1. If the character is a letter, calculate the ASCII value of the shifted character. If the shift would go beyond 'z', subtract 26 to wrap around to the beginning of the alphabet. Convert the ASCII value back to a character and add it to the encrypted message.
      2. If the character is not a letter, add it to the encrypted message as is.
   4. Print the encrypted message.

# Time & Space Complexity
The time complexity of the solution is O(n*m), where n is the number of messages and m is the average length of the messages. This is because we need to iterate over each character in each message.

The space complexity is O(m), where m is the length of the longest message. This is because we need to store the encrypted message.

# Implementation Details
The tricky part of the implementation is handling the case where the shift would go beyond 'z'. We can do this by checking if the ASCII value of the shifted character would be greater than the ASCII value of 'z'. If it would, we subtract 26 to wrap around to the beginning of the alphabet.

# Solution Code
```py3
n = int(input())

for i in range(n):
	persona = input()
	frase = input()

	nueva_frase = ""

	if persona == "lo":
		for c in frase:
			if  97 <= ord(c) <= 122:
				if ord(c) >= 118:
					nueva_frase += chr((ord(c) + 5) - 26)
				else:
					nueva_frase += chr(ord(c) + 5)
			else:
				nueva_frase += " "
		print(nueva_frase)
	elif persona == "li":
		for c in frase:
			if  97 <= ord(c) <= 122:
				if ord(c) >= 117:
					nueva_frase += chr((ord(c) + 6) - 26)
				else:
					nueva_frase += chr(ord(c) + 6)
			else:
				nueva_frase += " "
		print(nueva_frase)
```
In the above code, we first read the number of messages to encrypt. For each message, we read who the message is from and the message itself. We then initialize an empty string to store the encrypted message. For each character in the message, if it's a letter, we calculate the ASCII value of the shifted character. If the shift would go beyond 'z', we subtract 26 to wrap around to the beginning of the alphabet. We convert the ASCII value back to a character and add it to the encrypted message. If the character is not a letter, we add it to the encrypted message as is. Finally, we print the encrypted message.