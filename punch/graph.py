def render_bargraph(values, labels, bounds, w, h):
    canvas = [[" " for i in range(w)] for j in range(h)]
    min_value = bounds[0]
    max_value = bounds[1]
    diff = max(1, max_value - min_value)
    normalized = [(value - min_value) / diff for value in values]
    bar_w = int(w / len(values))
    for bar, value in enumerate(normalized):
        bar_h = int(value * h)
        for j in range(min(bar_h, h)):
            for i in range(max(1, bar_w - 1)):
                canvas[j][bar * bar_w + i] = "\u2588"
    labelline = ["{0:<{1}}".format(label, bar_w) for label in labels]
    labelline += [" "] * (w - len("".join(labelline)))
    canvas.insert(0, labelline)
    canvas.insert(0, ["-" for i in range(w)])
    canvas.insert(2, ["-" for i in range(w)])
    canvas.append(["-" for i in range(w)])
    for i, line in enumerate(canvas):
        c = "|"
        if i in (0, len(canvas) - 1):
            c = "+"
        line.insert(0, c)
        line.append(c)
    return reversed(canvas)


def print_bargraph(graph):
    for row in graph:
        print("".join(row))
