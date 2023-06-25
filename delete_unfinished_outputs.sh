#!/usr/bin/env bash

for output_folder in /home/aidmp/output-*; do
  echo "Analyzing $output_folder"
  problem_instance_folders=$(find "$output_folder" -type d -name "*.xml")
  for problem_instance_folder in $problem_instance_folders; do
    output_file_path="$problem_instance_folder/output.log"
    if ! grep -q "FMS Scheduler has finished" "$output_file_path"; then
      echo "Deleting $problem_instance_folder"
      rm -r "$problem_instance_folder"
    fi
  done
done
