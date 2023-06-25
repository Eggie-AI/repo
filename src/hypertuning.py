import argparse
import concurrent.futures
import itertools
import json
import pathlib

import joblib
import numpy as np
import tqdm
from sklearn.cross_decomposition import PLSRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.tree import DecisionTreeRegressor

from evaluate import evaluate_model
from train import get_dataset
from utils import assert_empty

all_models = {
    'KNNR': {
        'model': KNeighborsRegressor,
        'params': {
            'n_neighbors': [3],
            'weights': ['uniform', 'distance'],
            'p': list(range(1, 4)),
        },
    },
    'PLSR': {
        'model': PLSRegression,
        'params': {
            'n_components': list(range(1, 11)),
            'scale': [True, False],
        },
    },
    'DTR': {
        'model': DecisionTreeRegressor,
        'params': {
            'criterion': ['squared_error', 'friedman_mse', 'poisson'],  # absolute_error
            'splitter': ['best', 'random'],
            'max_depth': [None, *range(1, 21)],
            'min_samples_split': list(range(2, 11, 2)),
        },
    },
    'MLPR': {
        'model': MLPRegressor,
        'params': {
            'activation': ['identity', 'logistic', 'tanh', 'relu'],
            'solver': ['lbfgs', 'sgd', 'adam'],
            'learning_rate': ['invscaling', 'adaptive'],  # constant
            'learning_rate_init': [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
        },
    },
}


def hypertune_model(model_key, model_kwargs, train_dataset, test_path):
    Model = all_models[model_key]['model']
    model = Model(**model_kwargs)
    model.fit(*train_dataset)
    _, all_percentages, _ = evaluate_model(model, test_path, silent=True)
    mean = np.mean(all_percentages)
    return model, model_key, mean, model_kwargs


def hypertune(models, train_path: pathlib.Path, test_path: pathlib.Path, output: pathlib.Path):
    train_dataset = get_dataset(train_path)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for model_key in models:
            model = all_models[model_key]
            keys = list(model['params'].keys())
            for args in itertools.product(*[model['params'][key] for key in keys]):
                future = executor.submit(hypertune_model, model_key, dict(zip(keys, args)), train_dataset, test_path)
                futures.append(future)

        best_models = {}
        for future in tqdm.tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc='Hyperparameter Tuning'):
            model, model_key, avg_percentage, model_kwargs = future.result()
            if model_key not in best_models or avg_percentage < best_models[model_key]['avg_percentage']:
                data = {
                    'avg_percentage': avg_percentage,
                    'model_kwargs': model_kwargs,
                }
                best_models[model_key] = data
                with open(output / f'{model_key}.json', 'w') as f:
                    json.dump(data, f, indent=4)
                joblib.dump(model, output / f'{model_key}.joblib')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Model Hyperparameter Tuner',
        description='Hyperparameter tuner for the ML Model based on jsonl train and test data',
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
        help='The folder to write the trained model(s) to',
    )
    parser.add_argument(
        '-m',
        '--model',
        default='ALL',
        choices=['ALL', *all_models.keys()],
        nargs='*',
        help='The model to hyperparameter tune',
    )
    parser.add_argument(
        '-c',
        '--clean',
        action=argparse.BooleanOptionalAction,
        help='Clean the output model before writing to it',
    )
    args = parser.parse_args()

    input_train: pathlib.Path = args.input / 'train.jsonl'
    input_test: pathlib.Path = args.input / 'test.jsonl'
    if not input_train.exists():
        print(f"Input train file '{input_train}' does not exist")
        exit(1)
    if not input_test.exists():
        print(f"Input test file '{input_test}' does not exist")
        exit(1)

    models = list(all_models.keys()) if (args.model == ['ALL'] or args.model == 'ALL') else args.model
    for model in models:
        assert_empty(args.output / f'{model}.joblib', args.clean, 'file')
        assert_empty(args.output / f'{model}.json', args.clean, 'file')

    print(f"Hyperparameter tuning models: {models}")
    hypertune(models, input_train, input_test, args.output)
