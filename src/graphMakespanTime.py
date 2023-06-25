import argparse
import os
import pathlib

import matplotlib.pyplot as plt
import json
from models import x_keys, y_key

def make_graph(path: pathlib.Path):
    data = []
    with open(path, 'r') as file:
        for line in file:
            data.append(json.loads(line))

    # Extract makespan and time values
    makespans = [entry['makespan'] for entry in data]
    times = [entry['time'] for entry in data]
    # Generate line graph
    plt.plot(times, makespans, marker='o')
    plt.xlabel('Time (ns)')
    plt.ylabel('Makespan')
    plt.title('How the makespan developes over time')
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Postprocesses',
        description='Makes the graph for time vs makespan',
    )
    parser.add_argument(
        '-i',
        '--input',
        required=True,
        type=pathlib.Path,
        help='The folder containing the output files from the fms-scheduler',
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Input file '{args.input}' does not exist")
        exit(1)
    make_graph(args.input)
