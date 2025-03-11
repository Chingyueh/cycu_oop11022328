def is_palindrome(word):
    return word == word[::-1]

def reverse_word(word):
    return ''.join(reversed(word))

# 定義 word_list
word_list = ['parrot', 'racecar', 'level', 'python', 'madam']

for word in word_list:
    if len(word) >= 7 and is_palindrome(word):
        print(word)
reversed('parrot')
list(reversed('parrot'))
''.join(reversed('parrot'))
def reverse_word(word):
    return ''.join(reversed(word))
for word in word_list:
    if len(word) >= 7 and is_palindrome(word):
        print(word)