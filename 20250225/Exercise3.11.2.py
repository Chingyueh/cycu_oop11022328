def print_right(text):
    # Calculate the number of leading spaces needed
    spaces_needed = 40 - len(text)
    print(" " * spaces_needed + text)

print_right("Monty")
print_right("Python's")
print_right("Flying Circus")