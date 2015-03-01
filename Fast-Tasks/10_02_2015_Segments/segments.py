import sys

# Globals
segments = []
lines = {}
a = 0
b = 0
c = 0
n = 0

def main():
    # Get input
    inputString = input("")
    (n1, a1, b1, c1) = inputString.split()
    global n
    n = int(n1)
    global a
    a = int(a1)
    global b
    b = int(b1)
    global c
    c = int(c1)

    # Input validation
    if a > 100000 or b > 100000 or c > 100000 or n > 100000\
       or a < 0 or b < 0 or c < 0 or n < 0:
        sys.exit(-1)

    global segments
    segments = [""] * (n + 1)
    # Place Georgi's points
    for i in range(0, n + 1):
        if i % a == 0:
            segments[i] += "a"
    # Place Gergana's points
    for i in range(n, -1, -1):
        if i % b == 0:
            segments[i] += "b"

    # Time to find the lines
    global lines
    lines = {}
    for i in range(0, n + 1):
        if len(segments[i]) > 0:
            step = i + c
            if step <= n:
                if len(segments[step]):
                    lines[i] = step

    print(n - len(lines) * c)

def visualize_output(html):
    if html:
        html_string = \
            """
<html>
<head>
    <title>Segments HTML Output</title>
    <style>
        hr {
            display:block;
            height: 1px;
            color: red;
            width: 30px;
            border: 0;
            border-top: 1px solid red;
        }
        .border td {
            border-left: 1px solid black;
            width: 30px;
        }
    </style>
    <script>
        function buildResult() {
            var resultTable = document.getElementById("results");

            var row = resultTable.insertRow(0);
            row.setAttribute("class", "border");
"""

        end = 0
        for i in range(0, n + 1):
            html_string += "            var column = row.insertCell(" + str(i) + ");\n"
            if i in lines.keys():
                end = lines[i] - i
                del lines[i]

            if end > 0:
                html_string += "            column.innerHTML=\"<hr>\";\n"
                end -= 1

        html_string += "\n"
        html_string += "            var row = resultTable.insertRow(1);\n"
        for i in range(0, n + 1):
            html_string += "            var column = row.insertCell(" + str(i) + ");\n"
            html_string += "            column.innerHTML=\"" + segments[i].replace("o", "") + "\";\n"

        html_string += "        }\n"
        html_string += "    </script>\n"
        html_string += "</head>\n"
        html_string += \
"""
<body onload="buildResult()">
<table id="results">
</table>
</body>
</html>
"""
        file = open("output.html", "w")
        file.write(html_string)
        file.close()
        #print(html_string)
    else:
        # Visualize output
        buffer = ""
        end = 0
        for i in range(0, n):
            if i in lines.keys():
                end = lines[i] - i
                del lines[i]

            if end > 0:
                buffer += "|--"
                end -= 1
            else:
                buffer += "|  "
        print(buffer)

        buffer = ""
        for i in range(0, n):
            if len(segments[i]) == 0:
                buffer += "   "
            elif len(segments[i]) == 1:
                buffer += segments[i] + "  "
            else:
                buffer += segments[i] + " "
        print(buffer)

if __name__=="__main__":
    main()
    visualize_output(True)