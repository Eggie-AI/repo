import argparse
import csv
import json
import os
import pathlib

from utils import assert_empty

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Dataset Creator',
        description='Splits the raw data into training and testing data',
    )
    parser.add_argument(
        '-i',
        '--input',
        required=True,
        type=pathlib.Path,
        help='The jsonl file containing the raw data',
    )
    parser.add_argument(
        '-t',
        '--test',
        required=True,
        type=pathlib.Path,
        help='The CSV file containing the test folder names and instance names (RelPath, ProblemName)',
    )
    parser.add_argument(
        '-o',
        '--output',
        required=True,
        type=pathlib.Path,
        help='The folder to write the processed output to',
    )
    parser.add_argument(
        '-c',
        '--clean',
        action=argparse.BooleanOptionalAction,
        help='Clean the output folder before writing to it',
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Input file '{args.input}' does not exist")
        exit(1)
    if not os.path.exists(args.test):
        print(f"Input CSV file '{args.test}' does not exist")
        exit(1)

    output_train = args.output / 'train.jsonl'
    output_test = args.output / 'test.jsonl'
    assert_empty(output_train, args.clean, 'file')
    assert_empty(output_test, args.clean, 'file')

    test_set = set()
    with open(args.test) as csvfile:
        for row in csv.DictReader(csvfile):
            test_set.add((row['RelPath'], row['ProblemName']))

    with open(args.input, 'r') as f, open(output_train, 'w') as f_train, open(output_test, 'w') as f_test:
        for line in f:
            data = json.loads(line)
            if (data['relPath'], data['problemName']) in test_set:
                f_test.write(line)
            else:
                f_train.write(line)
