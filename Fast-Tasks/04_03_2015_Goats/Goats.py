__author__ = 'Ivan Dortulov'

import copy
import sys

# ====> INPUT <====
(n, k) = input("").split(" ")
n = int(n)
k = int(k)

if n < 0 or n > 1000:
    print("Invalid input for N")
    sys.exit(-1)
if k < 0 or k > 1000:
    print("Invalid input for K")
    sys.exit(-1)

goat_weights = input("").split(" ")
if len(goat_weights) < k or len(goat_weights) > k:
    print("Not enough sheep weights!", k)
    sys.exit(-1)

for i in range(0, len(goat_weights)):
    goat_weights[i] = int(goat_weights[i])
    if goat_weights[i] < 1 or goat_weights[i] >= 100000:
        print("Invalid goat weight! A", i)
        sys.exit(-1)

# ====> SOLUTION <====
goat_weights.sort()


def simulate(goats, min_score):
    groups = []
    goats_copy = copy.copy(goats)
    print("Boat size: ", min_score)
    remaining = []

    for i in range(0, k):
        groups.append([])
        group_score = 0
        msg = "Group " + str(i) + " ( "
        group = groups[i]
        remaining = []

        print("Remaining: ", goats_copy)
        while len(goats_copy) > 0:
            biggest_goat = goats_copy.pop()
            print("Pop: ", biggest_goat)

            if group_score + biggest_goat <= min_score:
                group.append(biggest_goat)
                group_score += biggest_goat
                print("\tAdd to group ", i, group)
            else:
                print("\tAdd to remain")
                remaining.append(biggest_goat)
                print("\tRemaining", len(remaining), remaining)

        print("Still left for transport: ", len(remaining), remaining)
        remaining.reverse()
        goats_copy = copy.copy(remaining)

        for j in range(0, len(group)):
            msg += str(group[j]) + " "
        msg += ") WEIGHT: " + str(group_score)
        print(msg)

    print("Unable to transport ", goats_copy)
    if len(goats_copy) <= 0:
        return min_score
    else:
        print("Increasing boat size ...")
        return simulate(goats, min_score + 1)

print(simulate(goat_weights, goat_weights[len(goat_weights) - 1]))
