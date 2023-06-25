import numpy as np
from sklearn import svm
from sklearn import neighbors
from sklearn import gaussian_process
from sklearn import cross_decomposition
from sklearn import tree
from sklearn import neural_network
from joblib import dump, load
from cbor2 import load as loadCbor
from argparse import ArgumentParser
import os
from multiprocessing import Pool

models = {
    'SVR': svm.SVR(),
    'KNNR': neighbors.KNeighborsRegressor(n_neighbors=1, weights='uniform', algorithm='auto', metric='minkowski'),
    'GPR': gaussian_process.GaussianProcessRegressor(random_state=1, kernel=None),
    'PLSR': cross_decomposition.PLSRegression(n_components=1),
    'DTR': tree.DecisionTreeRegressor(random_state=1),  # ? parameter tuning
    'MLPR': neural_network.MLPRegressor(random_state=1),  # ? parameter tuning
}

predict_keys = [
    'machineCount',
    'jobCount',
    'opCount',
    'vertexDepth',
    'avgOpTime',
    'minOpTime',
    'maxOpTime',
    'idleTime',
    'opsRemaining',
    'alapST'
]


def print_stats(label, xs):
    print(label, 'std =', np.std(xs), 'mean =', np.mean(xs), 'min =', np.min(xs), 'max =', np.max(xs))


def main():
    args = parse_args()
    cbor_dir = args.cbor_dir

    print("Loading training data")
    x, y = get_training_data(cbor_dir, predict_keys, 'makespan')

    print("Stats")
    xn = np.array(x)
    for i, key in enumerate(predict_keys):
        chunk = xn[:, i]
        print_stats(key, chunk)
    print_stats('makespan', y)

    print("Training")
    train(x, y)

    print("Predicting")
    predict([x[0]])

    print('gt', y[0])


def parse_args():
    parser = ArgumentParser(description='Train models based on cbor files')
    parser.add_argument('cbor_dir', type=str, action='store', help='Directory containing cbor files')
    return parser.parse_args()


def get_training_data(cbor_dir, input_key_names, output_key_name):
    if not os.path.exists(cbor_dir):
        raise Exception(f"Invalid cbor dir {cbor_dir}")

    x = []  # inputs
    y = []  # outputs
    for subdirs, dirs, files in os.walk(cbor_dir):
        for file in files:
            if file.endswith(".cbor"):
                with open(os.path.join(subdirs, file), 'rb') as fp:
                    try:
                        cbor_data = loadCbor(fp)
                    except:
                        continue

                for key_name in input_key_names:
                    if key_name not in cbor_data:
                        raise Exception(f"input_key_name '{key_name}' not in cbor data")

                if output_key_name not in cbor_data:
                    raise Exception(f"output_key_name '' not in cbor data")

                cbor_values = [cbor_data[key] for key in input_key_names]
                x.append(cbor_values)
                y.append(cbor_data[output_key_name])

    return x, y


def train(x, y):
    with Pool(processes=os.cpu_count()) as pool:
        # TODO: it may be faster to load x, y in the train_model function (this is a lot of message passing)
        pool.starmap(train_model, [(name, model, x, y) for name, model in models.items()])


def train_model(name, model, x, y):
    model.fit(x, y)
    dump(model, f'models/{name}.joblib')
    print(f"Done training {name}")


def predict(x):
    for name in models.keys():
        model = load(f'models/{name}.joblib')
        print(f'model {name} predicted {model.predict(x)} for {x}')


if __name__ == '__main__':
    if not os.path.exists('models'):
        os.mkdir('models')
    main()

# TODO: connect with cpp (in another scriptm just load the .joblib)
# TODO: train with more data
# TODO: get actual makespan in training data
# TODO: transform data where appropriate (normalization or something)
# TODO: tune parameters
# TODO: preprocess by shuffling etc (proper data loading)
# TODO: separate models for flowshop/jobshop (perhaps even per problem class)

# ALTERNATIVE IDEA: use only root state + makespan as input, and predict makespan. states closest to makespan are then used


# TODO: stratified split test/train 20/80
# TODO: draft report presentation (and show to eggie)
