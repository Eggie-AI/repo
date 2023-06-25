import argparse
import json
import pathlib
import sys
import time
from collections import defaultdict

import numpy as np
from joblib import load

from models import x_keys, y_key


def evaluate_model(model, test_path: pathlib.Path, silent=False):
    d = defaultdict(lambda: {
        'errors': [],
        'lowest_makespan': int(sys.float_info.max),
    })
    with test_path.open() as f:
        i = 0
        for line in f:
            i += 1
            data = json.loads(line)
            X = [data[key] for key in x_keys]
            y = data[y_key]

            prediction = model.predict([X])[0]
            if not np.isscalar(prediction):
                prediction = prediction[0]
            error = abs(prediction - y)
            key = (data['relPath'], data['problemName'])
            d[key]['errors'].append(error)
            d[key]['lowest_makespan'] = min(d[key]['lowest_makespan'], y)

    prediction_count = 0
    all_percentages = []
    for k, v in d.items():
        errors = v['errors']
        error_count = len(errors)
        error_avg = sum(errors) / error_count
        lowest_makespan = v['lowest_makespan']
        error_percentage = error_avg / lowest_makespan * 100
        all_percentages.append(error_percentage)
        prediction_count += error_count
        if not silent:
            print(f"{k}:")
            print(f"\tLowest makespan: {lowest_makespan}")
            print(f"\tAverage error: {error_avg} ({error_percentage}%)")

    return d, all_percentages, prediction_count


def main():
    parser = argparse.ArgumentParser(
        prog='Model Evaluator',
        description='Evaluates the ML Model based on csv test data',
    )
    parser.add_argument(
        '-i',
        '--input',
        required=True,
        type=pathlib.Path,
        help='The test jsonl file',
    )
    parser.add_argument(
        '-m',
        '--model',
        required=True,
        type=pathlib.Path,
        help='The trained model (.joblib) to load',
    )

    args = parser.parse_args()

    if not args.model.exists():
        print(f"Model file '{args.model}' does not exist")
        exit(1)

    if not args.input.exists():
        print(f"Input file '{args.input}' does not exist")
        exit(1)

    model = load(args.model)
    t_start = time.time()
    d, all_error_percentages, prediction_count = evaluate_model(model, args.input)
    t_diff = time.time() - t_start

    all_error_percentages.sort()
    mean = np.mean(all_error_percentages)
    std = np.std(all_error_percentages)
    p = 0.95
    p_error_percentages = all_error_percentages[:int(len(all_error_percentages) * p)]
    mean_95 = np.mean(p_error_percentages)
    std_95 = np.std(p_error_percentages)

    print()
    print(f"Total problems: {len(d)}")
    print(f"Average error percentage: {mean}% (std: {std}), 95%: {mean_95}% (std: {std_95})")
    print(f"Average time per prediction: {t_diff / prediction_count}s")
    print(f"Total time: {t_diff}s")
    print(f"Total predictions: {prediction_count}")


if __name__ == '__main__':
    main()
