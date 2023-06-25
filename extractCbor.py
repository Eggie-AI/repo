from json.encoder import INFINITY
import argparse
import os.path
from cbor2 import load


def createParser():
    parser = argparse.ArgumentParser(description='Analyse Results')
    parser.add_argument('--input', '-i',
                        type=str,
                        action='store',
                        help='XML Input File')
    parser.add_argument('--scheduleAttributesCbor', '-sac',
                        type=str,
                        action='store',
                        help='cbor schedule attributes')
    parser.add_argument('--solvetype', '-sst',
                        type=str,
                        action='store',
                        help='enter solve type of schedule')
    return parser


def run(args):
    if (args.input.split(".")[-1] != "xml"):
        print("Received a file of wrong format ", args.input.split(".")[-1], "\n")
        quit()

    summaryResults = open("Summary.txt", "a")
    problemclass = args.input.split("/")[-4]
    problemsubclass = args.input.split("/")[-3]

    canonjobs = args.input.split("_")[-5] if problemsubclass == "Canon2ReentrancyNormalDeadlinesNormalOrder" else None
    canonmachines = 4

    results = {"name": args.input,
               "class": problemclass,
               "subclass": problemsubclass,
               "solveType": args.solvetype if args.solvetype else "unknown"
               }

    if os.path.exists(args.scheduleAttributesCbor):
        with open(args.scheduleAttributesCbor, 'rb') as fp:
            obj = load(fp)
            # print(obj)
            results.update({"jobs": obj["jobs"] if results[
                                                       "subclass"] != "Canon2ReentrancyNormalDeadlinesNormalOrder" else canonjobs,
                            "machines": obj["machines"] if results[
                                                               "subclass"] != "Canon2ReentrancyNormalDeadlinesNormalOrder" else canonmachines,
                            "solveTimePerJob": obj["timePerJob"] if "timePerJob" in obj else INFINITY,
                            "totalSolveTime": obj["totalTime"] if "totalTime" in obj else INFINITY,
                            "timeOut": obj["timeOutValue"],
                            "lowerBound": obj["lowerBound"] if "lowerBound" in obj else INFINITY,
                            "cborMakespan": obj["minMakespan"]})

    summaryResults.write(f"""{results["name"]}, \
                {results["class"]}, \
                {results["subclass"]}, \
                {results["solveType"]},\
                {results["jobs"] if "jobs" in results else INFINITY},\
                {results["machines"] if "machines" in results else INFINITY},\
                {results["solveTimePerJob"] if "solveTimePerJob" in results else INFINITY},\
                {results["totalSolveTime"] if "totalSolveTime" in results else INFINITY},\
                {results["cborMakespan"] if "cborMakespan" in results else INFINITY},\
                {results["lowerBound"] if "lowerBound" in results else INFINITY} \n""")

    return results


def main():
    parser = createParser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
