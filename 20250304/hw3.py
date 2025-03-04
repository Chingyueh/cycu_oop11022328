def absolute_value_wrong(x):
    if x < 0:
        return -x
    if x > 0:
        return x
def absolute_value_extra_return(x):
    if x < 0:
        return -x
    else:
        return x
    
    return 'This is dead code.'
def is_divisible(x, y):
    if x % y == 0:
        return True
    else:
        return False