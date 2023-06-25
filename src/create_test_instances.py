import argparse
import csv
import os
import pathlib
import shutil
import sys

from utils import assert_empty


def get_folders(input: pathlib.Path) -> list[pathlib.Path]:
    path = str(input)
    paths = []
    if path.startswith('canon'):
        path = 'FlowShops/Canon2ReentrancyNormalDeadlinesNormalOrder' + path[5:]
        paths.append(pathlib.Path(path))
    else:
        for shop_type in ['FlowShops', 'JobShops']:
            paths.append(pathlib.Path(shop_type) / input)
    return paths


def create_test_instances(input: pathlib.Path, test: pathlib.Path, output: pathlib.Path):
    with test.open('r') as csvfile:
        for row in csv.DictReader(csvfile):
            for rel_folder in get_folders(row['RelPath']):
                input_file: pathlib.Path = input / rel_folder
                if input_file.exists():
                    output_folder = (output / rel_folder).parent
                    output_folder.mkdir(parents=True, exist_ok=True)
                    shutil.copy(input_file, output_folder)
                else:
                    print(f"Input file '{input_file}' does not exist", file=sys.stderr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Test Instances Creator',
        description='Creates a new Instances folder based on the test CSV file',
    )

    parser.add_argument(
        '-i',
        '--input',
        required=True,
        type=pathlib.Path,
        help='The original Instances folder',
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
        help='The output Instances folder',
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

    assert_empty(args.output, args.clean, 'folder')

    create_test_instances(args.input, args.test, args.output)
