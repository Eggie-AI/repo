#!/usr/bin/env bash

# when killed, also kill all child processes
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

FLOWSHOPS_CANON="FlowShops/Canon2ReentrancyNormalDeadlinesNormalOrder"
SHOP_TYPES=("FlowShops" "JobShops")
FLOW_JOB_TYPES=("DaColTeppanLargeBenchmarks" "DemirkolBenchmarks" "DemirkolBenchmarksDeadlinesAbsolute")

instances_dir=""
fms_dir=""
python_server_file=""
model_file=""
output_dir=""
venv_dir=""
exploration_type="xd"
timeout=600000
output_state_data=0
max_makespan_paths=10
log=0
rank=-1
N=-1
run_idx=0
socket_pids=()

assert_dir() {
  if [ ! -d "$1" ]; then
    echo "Error: $2 directory '$1' does not exist"
    exit 1
  fi
}

assert_file() {
  if [ ! -f "$1" ]; then
    echo "Error: $2 file '$1' does not exist"
    exit 1
  fi
}

re_number="^\-?[0-9]+$"
assert_number() {
  if ! [[ $1 =~ $re_number ]] ; then
    echo "Error: '$1' is NaN"
    exit 1
  fi
}

assert_in_array() {
  needle=""${1,,}
  haystack=("${@:2}")

  for item in "${haystack[@]}"; do
    if [[ ${item,,} == "$needle" ]]; then
      return 1
    fi
  done

  echo "Error: '$1' is not in " "${haystack[@]}"
}

print_help() {
  echo "Usage: $0 \
<-i instances_dir> \
<-f fms_dir> \
<-v venv_dir> \
<-p python_server_file> \
<-x model_file> \
<-o output_dir> \
[-e exploration_type] \
[-t timeout] \
[-s output_state_data] \
[-m max_makespan_paths] \
[-l log] \
[-r rank] \
[-n workers] \
"
  echo "  -i instances_dir (required): directory containing the instances"
  echo "  -f fms_dir (required): directory containing the fms-scheduler"
  echo "  -v venv_dir (required for bestml): directory containing the virtual environment"
  echo "  -p python_server_file (required for bestml): Python server file"
  echo "  -x model_file (required for bestml): model joblib file"
  echo "  -o output_dir (required): directory to output the results to"
  echo "  -e exploration_type: exploration type (depth, breadth, best, bestml, static, adaptive, xd)"
  echo "  -t timeout: timeout in milliseconds"
  echo "  -s output_state_data: output state data (True or False)"
  echo "  -m max_makespan_paths: maximum number of paths per unique makespan to collect"
  echo "  -l log: log statistics over time"
  echo "  -r rank: rank of this instance (-1 for single-instance mode)"
  echo "     Instead, you can also use the SLURM_PROCID environment variable"
  echo "  -n workers: number of workers to use (default: number of cores)"
  echo "     Instead, you can also use the SLURM_NTASKS environment variable"
  exit 0
}

while getopts "i:f:v:p:x:o:e:t:sm:lr:n:h" opt; do
  case ${opt} in
    i )
      instances_dir=${OPTARG}
      assert_dir "$instances_dir" "Instances"
      ;;
    f )
      fms_dir=${OPTARG}
      assert_dir "$fms_dir" "fms-scheduler"
      ;;
    v )
      venv_dir=${OPTARG}
      assert_dir "$venv_dir" "Virtual environment"
      ;;
    p )
      python_server_file=${OPTARG}
      assert_file "$python_server_file" "Python server"
      ;;
    x )
      model_file=${OPTARG}
      assert_file "$model_file" "Model"
      ;;
    o )
      output_dir=${OPTARG}
      assert_dir "$fms_dir" "Output"
      ;;
    e )
      exploration_type=${OPTARG}
      exploration_types=("depth" "breadth" "best" "bestml" "static" "adaptive" "xd")
      assert_in_array "$exploration_type" "${exploration_types[@]}"
      ;;
    t )
      timeout=${OPTARG}
      assert_number "$timeout"
      ;;
    s )
      output_state_data=1
      ;;
    m )
      max_makespan_paths=${OPTARG}
      assert_number "$max_makespan_paths"
      ;;
    l )
      log=1
      ;;
    r )
      rank=${OPTARG}
      assert_number "$rank"
      ;;
    n )
      N=${OPTARG}
      assert_number "$N"
      ;;
    * )
      print_help
      ;;
  esac
done

i="$rank"

if [ -z "$instances_dir" ] || [ -z "$fms_dir" ] || [ -z "$output_dir" ]; then
  echo "Error: missing required arguments"
  print_help
fi

if [ "$rank" -eq -1 ]; then
  rank=$SLURM_PROCID
  if ! [[ $rank =~ $re_number ]] ; then
    rank=-1
  fi
fi

if [ "$N" -eq -1 ]; then
  N=$SLURM_NTASKS
  if ! [[ $N =~ $re_number ]] ; then
    N=$(nproc --all)
  fi
fi

if [ "$exploration_type" = "bestml" ]; then
  if [ -z "$venv_dir" ] || [ -z "$python_server_file" ] || [ -z "$model_file" ]; then
    echo "Error: missing required arguments for bestml exploration type (-v, -p, or -x)"
    print_help
  fi
fi

trap 'echo "Killing everything xd"; kill 0' SIGINT

_i=0
await() {
  if [ "$rank" -gt -1 ]; then
    v=$(("$1" % N))
    if ! [ "$v" = "$rank" ]; then
      ret="0"
    else
      ret="1"
    fi
  else
    if [ "$_i" -ge "$N" ]; then
      wait -n
    fi
    _i=$((_i + 1))
    ret="1"
  fi
}

log() {
  echo "[$((i + 1))/$total] $1"
}

runCanonFlowShop() {
  root_folder="$instances_dir/$FLOWSHOPS_CANON"
  folder_names=$()
  if [ -d "$root_folder" ]; then
    folder_names=$(ls "$root_folder" | sort -V)
  fi
  for folder_name in $folder_names; do
    folder="$root_folder/$folder_name"
    for input_file in "$folder"/*.xml; do
      await "$i"
      if [[ "$ret" -eq 0 ]]; then
        i=$((i + 1))
        continue
      fi

      input_file_name="$(basename "$input_file")"
      rel_output_dir="canon/$folder_name/$input_file_name"
      if [ "$rank" -gt -1 ]; then
        run_app "$input_file" "$rel_output_dir" "fixedorder" "$run_idx"
      else
        run_app "$input_file" "$rel_output_dir" "fixedorder" "$run_idx" &
      fi
      run_idx=$((run_idx + 1))
      i=$((i + 1))
    done
  done
}

run_app() {
  _input_file=$1
  _rel_output_dir=$2
  _shop_type=$3
  _run_idx=$4
  _full_output_dir="$output_dir/$_rel_output_dir"

  if [ -f "$_full_output_dir/output.log" ]; then
    if grep -q "FMS Scheduler has finished" "$_full_output_dir/output.log"; then
      log "Skipping $_rel_output_dir"
      return
    fi
  fi

  mkdir -p "$_full_output_dir"

  extra=""
  if [ "$exploration_type" = "bestml" ]; then
    socket="/tmp/socket-$(basename "$model_file" .joblib)-$rank-$_run_idx.s"
    "$venv_dir/bin/python3" -u "$python_server_file" "$socket" "$model_file" > "$output_dir/model-server-$(basename "$socket" .s).log" 2>&1 &
    socket_pids+=($!)
    sleep 10
    extra="$extra --socket $socket"
  fi
  if [ "$output_state_data" = 1 ]; then
    extra="$extra --output-state-data --max-makespan-paths $max_makespan_paths"
  fi
  if [ "$log" = 1 ]; then
    extra="$extra --output-makespan-times"
  fi

  log "\"$fms_dir/scheduler/build/bin/app\" \
-i \"$_input_file\" \
-o \"$_full_output_dir/\" \
-a sag \
--shop-type \"$_shop_type\" \
--exploration-type \"$exploration_type\" \
--time-out \"$timeout\" \
$extra \
> \"$_full_output_dir/output.log\" 2>&1"

  "$fms_dir/scheduler/build/bin/app" \
    -i "$_input_file" \
    -o "$_full_output_dir/" \
    -a sag \
    --shop-type "$_shop_type" \
    --exploration-type "$exploration_type" \
    --time-out "$timeout" \
    $extra \
    > "$_full_output_dir/output.log" 2>&1
  _ret_code=$?
  if [ $_ret_code = 0 ]; then
    log "Done"
  else
    log "Process crashed with exit code $_ret_code"
  fi
}

run() {
  root_folder="$instances_dir/$shop_type/$job_type_dir"
  input_file_names=$()
  if [ -d "$root_folder" ]; then
    input_file_names=$(ls "$root_folder" | sort -V)
  fi
  for input_file_name in $input_file_names; do
    await "$i"
    if [[ "$ret" -eq 0 ]]; then
      i=$((i + 1))
      continue
    fi

    input_file="$root_folder/$input_file_name"
    rel_output_dir="$job_type_dir/$input_file_name"
    if [ "$rank" -gt -1 ]; then
      run_app "$input_file" "$rel_output_dir" "$shop_type_short" "$run_idx"
    else
      run_app "$input_file" "$rel_output_dir" "$shop_type_short" "$run_idx" &
    fi
    run_idx=$((run_idx + 1))
    i=$((i + 1))
  done
}

echo "[Rank $rank]: Running with $N workers"
total=0
for folder in "$instances_dir/$FLOWSHOPS_CANON"/*; do
  if [ ! -d "$folder" ]; then
    continue
  fi
  dir_count=$(ls -l "$folder" | wc -l)
  total=$((total + dir_count))
done
for shop_type in "${SHOP_TYPES[@]}"; do
  for job_type_dir in "${FLOW_JOB_TYPES[@]}"; do
    root_folder="$instances_dir/$shop_type/$job_type_dir"
    if [ ! -d "$root_folder" ]; then
      continue
    fi
    dir_count=$(find "$root_folder" -name "*.xml" -type f | wc -l)
    total=$((total + dir_count))
  done
done

runCanonFlowShop
for shop_type in "${SHOP_TYPES[@]}"; do
  if [ "$shop_type" = "FlowShops" ]; then
    shop_type_short="flow"
  else
    shop_type_short="job"
  fi
  for job_type_dir in "${FLOW_JOB_TYPES[@]}"; do
    run
  done
done

if [ "$exploration_type" = "bestml" ]; then
  for pid in "${socket_pids[@]}"; do
    kill -9 "$pid"
  done
fi
