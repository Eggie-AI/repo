import argparse
import json
import os
import pathlib
import random
from math import ceil

from utils import assert_empty


def weighted_sample(state_data_depths, total_samples):
    sampled_data = []
    if len(state_data_depths) == 0:
        return sampled_data
    max_depth = max(state_data_depths.keys())

    samples_left = total_samples
    for depth, state_data_list in state_data_depths.items():
        weight = (max_depth - depth) / max_depth
        depth_samples = min(ceil(samples_left * weight), len(state_data_list))
        sampled_data.extend(random.sample(state_data_list, depth_samples))
        samples_left -= depth_samples

    # TODO: idk hack to make sure we have enough samples, for small instances is bad
    # if len(sampled_data) < 1000:
    #     state_data_list = [item for sublist in data_dict.values() for item in sublist]
    #     sampled_data.extend(random.sample(state_data_list, 1000 - len(sampled_data)))

    return sampled_data


def process(full_path: pathlib.Path, input: pathlib.Path, output: pathlib.Path, samples_per_instance: int):
    rel_path = full_path.relative_to(input)
    print(f"Processing {rel_path}...")

    state_data_map = {}
    with open(full_path, 'r') as f:
        for line in f:
            state_data_path = json.loads(line)
            for state_data in state_data_path:
                id = state_data['stateId']
                state_data["relPath"] = str(rel_path.parent)
                if id not in state_data_map or state_data_map[id]['makespan'] > state_data['makespan']:
                    state_data_map[id] = state_data

    state_data_depths = {}
    for state_data in state_data_map.values():
        depth = state_data['vertexDepth']
        if depth not in state_data_depths:
            state_data_depths[depth] = []
        state_data_depths[depth].append(state_data)

    samples = weighted_sample(state_data_depths, samples_per_instance)
    with open(output, 'a') as f:
        for sample in samples:
            json.dump(sample, f)
            f.write('\n')



def postprocess(input: pathlib.Path, output: pathlib.Path, samples_per_instance: int):
    for file in input.rglob('*.jsonl'):
        process(file, input, output, samples_per_instance)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Output Postprocessor',
        description='Processes output from the fms-scheduler into training data for the ML models',
    )
    parser.add_argument(
        '-i',
        '--input',
        required=True,
        type=pathlib.Path,
        help='The folder containing the output files from the fms-scheduler',
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
    parser.add_argument(
        '-s',
        '--samples',
        type=int,
        default=1000,
        help='The amount of samples per instance to extract',
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Input folder '{args.input}' does not exist")
        exit(1)
    assert_empty(args.output, args.clean, 'file')

    postprocess(args.input, args.output, args.samples)
