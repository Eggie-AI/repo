#!/usr/bin/env bash

set -e  # crash on errors

IDMP_FOLDER=$1
OUT_FOLDER=$3

DEBUG=0

if [ -z "$IDMP_FOLDER" ]; then
    echo "Usage: ./analyze_inputs.sh <input_folder> [out_folder]"
    exit 1
fi

if [ ! -d "$IDMP_FOLDER" ]; then
    echo "Input folder does not exist"
    exit 1
fi


if [ -d "$OUT_FOLDER" ]; then
  mkdir -p "$OUT_FOLDER"
fi

rm Summary.txt

CPMIP_EXPLORATION_TYPES=("CP" "MIP")
SAG_EXPLORATION_TYPES=("depth" "breadth" "best" "static" "adaptive")

function setExplorationTypes {
  MODEL=$1
  if [ "$MODEL" == "CPMIP" ]; then
    EXPLORATION_TYPES=$CPMIP_EXPLORATION_TYPES
  elif [ "$MODEL" == "SAG" ]; then
    EXPLORATION_TYPES=$SAG_EXPLORATION_TYPES
  else
    echo "Unknown model $MODEL"
    exit 1
  fi
}

function analyzeCanonFlowShop {
  MODEL=$1

  echo "Analyzing Canon Flow Shops $MODEL"

  setExplorationTypes $MODEL

  skipped=0
  analyzed=0

  CANON_INPUT_FOLDER="$IDMP_FOLDER/Instances/FlowShops/Canon2ReentrancyNormalDeadlinesNormalOrder"
  CANON_OUT_FOLDER="$IDMP_FOLDER/Results/$MODEL/FlowShops/Canon2ReentrancyNormalDeadlinesNormalOrder"
  for folder in "$CANON_INPUT_FOLDER"/*; do
    for xml_file in "$folder"/*.xml; do
      for exploration in $EXPLORATION_TYPES; do
        result_file="$CANON_OUT_FOLDER/$(basename "$folder")$(basename "$xml_file")SAG$exploration.txt.cbor"
        if [ ! -f "$result_file" ]; then
          skipped=$((skipped+1))
          if [ "$DEBUG" -eq 1 ]; then
            echo "Skipping $xml_file"
            echo "Result file $result_file does not exist"
          fi
          continue
        fi
        analyzed=$((analyzed+1))
        if [ "$DEBUG" -eq 1 ]; then
          echo "Analyzing $xml_file"
        fi
        python3 extractCbor.py --input "$xml_file" --scheduleAttributesCbor "$result_file" --solvetype "$MODEL_NAME"
        if [ -d "$OUT_FOLDER" ]; then
          out_path="$OUT_FOLDER/$MODEL/FlowShops/Canon2ReentrancyNormalDeadlinesNormalOrder/$(basename "$folder")-$(basename "$xml_file")-$exploration.txt"
          mkdir -p "$(dirname "$out_path")"
          mv Summary.txt "$out_path"
        fi
      done
    done
  done;

  echo "Analyzed: $analyzed"
  echo "Skipped: $skipped"
}

function analyze {
  FOLDER=$1
  SHOP_TYPE=$2
  MODEL=$3

  echo "Analyzing $FOLDER $SHOP_TYPE $MODEL"

  setExplorationTypes $MODEL

  INSTANCE_FOLDER="$IDMP_FOLDER/Instances/$SHOP_TYPE/$FOLDER"
  RESULTS_FOLDER="$IDMP_FOLDER/Results/$MODEL/$SHOP_TYPE/$FOLDER"

  skipped=0
  analyzed=0

  for xml_file in "$INSTANCE_FOLDER"/*.xml; do
    for exploration in $EXPLORATION_TYPES; do
        result_file="$RESULTS_FOLDER/$(basename "$xml_file")SAG$exploration.txt.cbor"
        if [ ! -f "$result_file" ]; then
          skipped=$((skipped+1))
          if [ "$DEBUG" -eq 1 ]; then
            echo "Skipping $xml_file"
            echo "Result file $result_file does not exist"
          fi
          continue
        fi
        analyzed=$((analyzed+1))
        python3 extractCbor.py --input "$xml_file" --scheduleAttributesCbor "$result_file" --solvetype "$MODEL_NAME"
        if [ -d "$OUT_FOLDER" ]; then
          out_path="$OUT_FOLDER/$MODEL/$SHOP_TYPE/$FOLDER/$(basename "$folder")-$(basename "$xml_file")-$exploration.txt"
          mkdir -p "$(dirname "$out_path")"
          mv Summary.txt "$out_path"
          echo "moved to $out_path"
        fi
    done
  done;

  echo "Analyzed: $analyzed"
  echo "Skipped: $skipped"
}

for MODEL in "CPMIP" "SAG"; do
  analyzeCanonFlowShop $MODEL

  for SHOP_TYPE in "FlowShops" "JobShops"; do
    analyze DaColTeppanLargeBenchmarks $SHOP_TYPE $MODEL
    analyze DemirkolBenchmarks $SHOP_TYPE $MODEL
    analyze DemirkolBenchmarksDeadlinesAbsolute $SHOP_TYPE $MODEL
  done
done
