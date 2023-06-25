import argparse
import json
import os
import pathlib
import pickle

import matplotlib.pyplot as plt
import numpy as np
from joblib import load
from models import x_keys, y_key


def make_graph(path: pathlib.Path, test_path: pathlib.Path):
    plt.rcParams.update({
        'font.size': 18
    })
    data_pickle = {}
    for file in path.glob('*.joblib'):
        name = str(file).split('.')[0].split('/')[1]
        model = load(file)
        results = dict()
        with test_path.open() as f:
            i = 0
            for line in f:
                if name == "SVR" and i % 100 == 0:
                    print(i)
                i += 1
                data = json.loads(line)
                X = [data[key] for key in x_keys]
                y = data[y_key]

                prediction = model.predict([X])[0]
                if not np.isscalar(prediction):
                    prediction = prediction[0]
                error = abs(prediction - y) / y * 100
                if data['vertexDepth'] not in results:
                    results[data['vertexDepth']] = [error]
                else:
                    results[data['vertexDepth']].append(error)
        x = []
        y = []
        for key, value in results.items():
            x.append(key)
            y.append(sum(value) / len(value))
        print('model done!', name)
        plt.plot(x, y, label= name)
        data_pickle[name] = (x, y)
        # ax2.plot(x, y, label= name)

    # ax.set_ylim(2000, 200000)  # outliers only
    pickle.dump(data_pickle, open("depthErrorData.pickle", "wb"))
    d = pickle.load(open("depthErrorData.pickle", "rb"))
    for n, r in d.items():
        plt.plot(r[0], r[1], label=n)

    plt.ylim(0, 110)  # most of the data
    plt.xlabel('Depth')
    plt.ylabel('Error (%)')
    plt.style.use('classic')
    plt.legend()
    plt.tight_layout(rect=[0, 0, 1, 0.85])
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.3), ncol=3)
    plt.savefig('DepthErrorGraph.svg')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Postprocesses',
        description='Makes the graph for depth vs error for all models',
    )
    parser.add_argument(
        '-i',
        '--input',
        required=True,
        type=pathlib.Path,
        help='The file containing all the the testing data',
    )

    parser.add_argument(
        '-m',
        '--model',
        required=True,
        type=pathlib.Path,
        help='The folder containing all the models',
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Input file '{args.input}' does not exist")
        exit(1)
    make_graph(args.model, args.input)
