from sklearn import svm
from sklearn import neighbors
from sklearn import cross_decomposition
from sklearn import tree
from sklearn import neural_network

models = {
    'SVR': svm.SVR(),
    'KNNR': neighbors.KNeighborsRegressor(n_neighbors=1, weights='uniform', algorithm='auto', metric='minkowski'),
    'PLSR': cross_decomposition.PLSRegression(n_components=1),
    'DTR': tree.DecisionTreeRegressor(random_state=1),  # ? parameter tuning
    'MLPR': neural_network.MLPRegressor(random_state=1),  # ? parameter tuning
}

x_keys = [
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
y_key = 'makespan'
