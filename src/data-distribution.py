from argparse import ArgumentParser
import os
from collections import defaultdict
from pathlib import Path
from matplotlib import pyplot as plt
import pickle as pkl
import json

CACHE_DIR = "cache"

def main():
    os.makedirs(CACHE_DIR, exist_ok=True)

    parser = ArgumentParser()
    parser.add_argument("-ts", "--test_file", type=Path, required=True, help="Path to test file")
    parser.add_argument("-tr", "--train_file", type=Path, required=True, help="Path to train file")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite cache")
    parser.add_argument("-p", "--plot-dir", type=Path, default=Path("plots"), help="Path to plot directory")
    args = parser.parse_args()

    if not args.test_file.exists():
        raise FileNotFoundError(f"Test file not found: {args.test_file}")

    if not args.train_file.exists():
        raise FileNotFoundError(f"Train file not found: {args.train_file}")

    cache_file_path = Path(CACHE_DIR) / f"data-distribution.pkl"

    if cache_file_path.exists() and not args.force:
        print("Loading from cache")
        with open(cache_file_path, "rb") as f:
            data = pkl.load(f)
    else:
        max_depth = -1

        xd = [
            (args.train_file, defaultdict(int), "Train"),
            (args.test_file, defaultdict(int), "Test"),
        ]

        for file_path, depth_dict, name in xd:
            with file_path.open("r") as f:
                for line in f:
                    obj = json.loads(line)
                    depth = obj["vertexDepth"]
                    max_depth = max(max_depth, depth)
                    depth_dict[depth] += 1

        data = {}
        for file_path, depth_dict, name in xd:
            histogram = [0] * (max_depth + 1)
            for depth, count in depth_dict.items():
                histogram[depth] = count
            data[name] = histogram

        with cache_file_path.open("wb") as f:
            pkl.dump(data, f)

    print("Plotting")

    plt.rcParams.update({
        'font.size': 18,
    })

    plt.xlabel("Depth")
    plt.ylabel("Count")
    plt.yscale("log")

    for key in data:
        plt.plot(data[key], label=key)

    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(args.plot_dir / "data-distribution.svg")
    plt.clf()


if __name__ == "__main__":
    main()
