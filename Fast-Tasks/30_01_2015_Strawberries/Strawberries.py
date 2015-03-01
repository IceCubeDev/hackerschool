__author__ = 'Ivan Dortulov'

from optparse import OptionParser
import sys
import time


# This is our basket of fruits
basket = []
# Which fruits in the basket are rotting
rotten = []


# Parse script arguments
def parse_options():
    parser = OptionParser()
    parser.add_option("-v", "--visualize",
                      action="store_true", dest="visualize",
                      help="Visualize the output")

    return parser.parse_args(args=sys.argv[1:])


def visualize(rows, columns):
    line = "  "
    for j in range(0, columns):
        line += str(j + 1) + " "
    print(line)

    for i in range(0, rows):
        line = str(i + 1) + " "
        for j in range(0, columns):
            if basket[j * rows + i]:
                line += "* "
            else:
                line += "0 "
        print(line)
    print()

# Simulate the rotting process and visualize the output
def simulate_and_visualize(rows, columns, day, rotting):
    visualize(rows,columns)
    time.sleep(1)
    if day == 0:
        num = 0
        for i in range(0, len(basket)):
            if basket[i] == False:
                num += 1
        return num

    neighbours = []
    for (x, y) in rotting:
        neighbours += rot(x, y, rows, columns)
        for fruit in neighbours:
            rotten.append(fruit)

    return simulate_and_visualize(rows, columns, day - 1, neighbours)


# Just simulate the rotting process
def simulate(rows, columns, day, rotting):
    #print(day, rotting)
    if day == 0:
        num = 0
        for i in range(0, len(basket)):
            if basket[i] == False:
                num += 1
        return num

    neighbours = []
    for (x, y) in rotting:
        neighbours += rot(x, y, rows, columns)
        for fruit in neighbours:
            rotten.append(fruit)

    return simulate(rows, columns, day - 1, neighbours)

# Rot the fruits around (i, j)
def rot(x, y, rows, columns):
    num = 0
    children = []
    for i in [-1, 1]:
        if x + i >= 0 and x + i < rows:
            basket[y * rows + x + i] = True
            if (x + i, y) not in rotten:
                children.append((x + i, y))
    for i in [-1, 1]:
        if y + i >= 0 and y + i < columns:
            basket[(y + i) * rows + x] = True
            if (x, y + i) not in rotten:
                children.append((x, y + i))

    return children

if __name__ == "__main__":
    # Get the script options
    (options, args) = parse_options()

    # Get the input
    (K, L, R) = sys.stdin.readline().split()
    # Convert to integers, because python input returns strings
    K = int(K)
    L = int(L)
    R = int(R)

    if K < 0 or K > 1000:
        sys.exit(-1)
    if L < 0 or L > 1000:
        sys.exit(-1)
    if R < 0 or R > 100:
        sys.exit(-1)
    if K > L:
        sys.exit(-1)

    for i in range(0, K * L):
        basket.append(False)

    # Get the rotting fruits
    (x,y) = sys.stdin.readline().split()
    x = int(x) - 1
    y = int(y) - 1
    if x < 0 or x >= K:
        sys.exit(-1)
    if y < 0 or y > L:
        sys.exit(-1)
    basket[y * K + x] = True
    rotten.append((x, y))

    input = sys.stdin.readline()
    if len(input) > 1:
        (x,y) = input.split()
        x = int(x) - 1
        y = int(y) - 1
        if x < 0 or x >= K:
            sys.exit(-1)
        if y < 0 or y >+ L:
            sys.exit(-1)
        basket[y * K + x] = True
        rotten.append((x, y))

    # If we have to visualize the output
    if options.visualize:
        print(simulate_and_visualize(K, L, R, list(rotten)))
    else:
        print(simulate(K, L, R, list(rotten)))
