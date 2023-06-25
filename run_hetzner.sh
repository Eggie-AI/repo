#!/usr/bin/env bash

N=5

for model in /home/aidmp/models/*.joblib; do
  model_name=$(basename "$model" '.joblib')
  ./run_instances.sh \
    -i /home/aidmp/InstancesTest/ \
    -f /home/aidmp/fms-scheduler/ \
    -o "/home/aidmp/output-$model_name" \
    -e bestml \
    -p /home/aidmp/repo/model_server.py \
    -x "$model" \
    -v /home/aidmp/venv/ \
    -l \
    -n $N
done
