# repo
This repo contains our training pipeline

## Analyzing the cbor files
```shell
./analyze_inputs.sh <input_folder> [out_folder]
```

`<input_folder>` should simply be the path to the folder downloaded from SurfDrive.
`[out_folder]` can be any path, as it will be created by the script (e.g. you can just type `out`)
Providing an `out_folder` create one file per input.
Not providing it will create one big Summary.txt

## Running instances the cbor files

**Make sure fms-scheduler repo has been build**

```shell
./run_instances.sh <input_folder> <fms_folder>
```

- `<input_folder>` should be the full path to the folder downloaded from SurfDrive.
- `<fms_folder]` should be the full path to the fms-scheduler
  
Output will be written to a `/data/` directory in this repo.