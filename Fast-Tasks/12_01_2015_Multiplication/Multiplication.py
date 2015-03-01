__author__ = 'Ivan Dortulov'

import sys

# Get N
N = -1
while N < 0 or N > 3200000:
    N = int(input())

if N == 0:
    print(1)
    sys.exit(0);

sequence = ""
current_natural = 1
while len(sequence) < N:
    sequence += str(current_natural * current_natural)
    current_natural += 1

print(sequence[N-1])
