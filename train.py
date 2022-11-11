from helper.utils import fetch_logged_data
import bentoml
import mlflow
import os
import numpy as np
from pprint import pprint
import pandas as pd
from typing import List
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import RepeatedStratifiedKFold
import consts

def main():
    mlflow.sklearn.autolog()
    try:
        input_dtypes = {
        'bedrooms': np.dtype('float64'),
        'bathrooms': np.dtype('float64'),
        'sqft_living': np.dtype('float64'),
        'sqft_lot': np.dtype('float64'),
        'floors': np.dtype('float64'),
        'waterfront': np.dtype('float64'),
        'view': np.dtype('float64'),
        'condition': np.dtype('float64'),
        'grade': np.dtype('float64'),
        'sqft_above': np.dtype('float64'),
        'sqft_basement': np.dtype('float64'),
        'yr_built': np.dtype('float64'),
        'yr_renovated': np.dtype('float64'),
        'zipcode': np.dtype('float64'),
        'lat': np.dtype('float64'),
        'long': np.dtype('float64'),
        'sqft_living15': np.dtype('float64'),
        'sqft_lot15': np.dtype('float64')
    }
        
        X_train = pd.read_csv('data/train/X_train.csv', dtype=input_dtypes)
        y_train = pd.read_csv('data/train/y_train.csv').values.ravel()

        mlflow.set_tracking_uri(consts.MLFLOW_TRACKING_URI)
        os.environ['MLFLOW_TRACKING_USERNAME'] = consts.MLFLOW_TRACKING_USERNAME
        os.environ['MLFLOW_TRACKING_PASSWORD'] = consts.MLFLOW_TRACKING_PASSWORD

    except IOError:
        print('''unavailable data..
                ''')
        return
    model = RandomForestRegressor(random_state=42)
    # define evaluation
    cv = RepeatedStratifiedKFold(n_splits=10, n_repeats=3, random_state=1)
    # define search space
    param_grid = {
        'n_estimators': [100, 200],
        'max_features': [1.0],
        'max_depth': [4, 6, 8],
        'criterion': ['squared_error']
    }
    # define search
    search = GridSearchCV(
        estimator=model, param_grid=param_grid, n_jobs=-1, cv=cv)
    # execute search
    result = search.fit(X_train, y_train)
    # summarize result
    print('Best Score: %s' % result.best_score_)
    print('Best Hyperparameters: %s' % result.best_params_)
    run_id = mlflow.last_active_run().info.run_id

    # show data logged in the parent run
    print("========== parent run ==========")
    for key, data in fetch_logged_data(run_id).items():
        print("\n---------- logged {} ----------".format(key))
        pprint(data)

    # show data logged in the child runs
    filter_child_runs = "tags.mlflow.parentRunId = '{}'".format(run_id)
    runs = mlflow.search_runs(filter_string=filter_child_runs)
    param_cols = ["params.{}".format(p) for p in param_grid.keys()]
    metric_cols = ["metrics.mean_test_score"]

    print("\n========== child runs ==========\n")
    pd.set_option("display.max_columns", None)  # prevent truncating columns
    print(runs[["run_id", *param_cols, *metric_cols]])

    # import only the best_estimator artifact to BentoML
    artifact_path = "best_estimator"
    model_uri = f"runs:/{run_id}/{artifact_path}"
    bento_model = bentoml.mlflow.import_model("sklearn_house_data", model_uri)
    print("\nModel imported to BentoML: %s" % bento_model)


if __name__ == "__main__":
    main()
