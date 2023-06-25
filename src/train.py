import argparse
import json
import pathlib
import joblib

from models import models, x_keys, y_key
from utils import assert_empty


def get_dataset(path: pathlib.Path):
    X = []
    y = []
    with open(path, 'r') as f:
        for line in f:
            data = json.loads(line)
            for x_key in x_keys:
                if x_key not in data:
                    raise Exception(f"Input key '{x_key}' not in json data")
            if y_key not in data:
                raise Exception(f"Output key '{y_key}' not in json data")

            X.append([data[key] for key in x_keys])
            y.append(data[y_key])
    return X, y


def train(train_path: pathlib.Path, test_path: pathlib.Path, output_path: pathlib.Path, model):
    model.fit(*get_dataset(train_path))
    joblib.dump(model, output_path)
    score = model.score(*get_dataset(test_path))
    print(f"Score: {score}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Model Trainer',
        description='Trains the ML Model based on jsonl train data',
    )

    parser.add_argument(
        '-i',
        '--input',
        required=True,
        type=pathlib.Path,
        help='The folder containing the train and test jsonl files',
    )
    parser.add_argument(
        '-o',
        '--output',
        required=True,
        type=pathlib.Path,
        help='The folder to write the trained model to',
    )
    parser.add_argument(
        '-m',
        '--model',
        required=True,
        choices=models.keys(),
        help='The model to train',
    )
    parser.add_argument(
        '-c',
        '--clean',
        action=argparse.BooleanOptionalAction,
        help='Clean the output model before writing to it',
    )

    args = parser.parse_args()
    output_model = args.output / f'{args.model}.joblib'
    input_train = args.input / 'train.jsonl'
    input_test = args.input / 'test.jsonl'
    if not input_train.exists():
        print(f"Input train file '{input_train}' does not exist")
        exit(1)
    if not input_test.exists():
        print(f"Input test file '{input_test}' does not exist")
        exit(1)
    assert_empty(output_model, args.clean, 'file')

    train(input_train, input_test, output_model, models[args.model])
