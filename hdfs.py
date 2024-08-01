#! /usr/bin/env python3

import os
import json
import pytz
import shutil
import random
import timeloop
import datetime
import argparse
import logging
from pathlib import Path
from fsplit.filesplit import Filesplit
from multiprocessing import Process, Manager

args = None
file_splitter = Filesplit()
TIMED_TASK_LOOP = timeloop.Timeloop()
IST = pytz.timezone('Asia/Kolkata')
logging.getLogger("timeloop").setLevel(logging.CRITICAL)

JOB_MANAGER = Manager()
SHARED_JOB_OUTPUT = JOB_MANAGER.list()

import os
import shutil

def move_directory(src, dest):
    try:
        shutil.move(src, dest)
        print(f"Directory '{src}' moved to '{dest}' successfully.")
    except FileNotFoundError as e:
        print(f"Error moving directory: {e} (Source directory not found)")
    except FileExistsError as e:
        print(f"Error moving directory: {e} (Destination directory already exists)")
    except Exception as e:
        print(f"Unexpected error: {e}")


def copy_directory(src, dest):
    try:
        shutil.copytree(src, dest)
        print(f"Directory '{src}' copied to '{dest}' successfully.")
    except shutil.Error as e:
        print(f"Error copying directory: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def copy_file(src, dest):
    try:
        shutil.copy2(src, dest)
        print(f"File '{src}' copied to '{dest}' successfully.")
    except shutil.Error as e:
        print(f"Error copying file: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def move_file(src, dest):
    try:
        shutil.move(src, dest)
        print(f"File '{src}' moved to '{dest}' successfully.")
    except shutil.Error as e:
        print(f"Error moving file: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")



def load_config_from_json(filepath):
    global args
    with open(filepath, 'r') as f:
        config = json.load(f)
    for key, value in config.items():
        try:
            if isinstance(value, int):
                exec(f"args.{key.upper()} = {int(value)}")
            elif isinstance(value, float):
                exec(f"args.{key.upper()} = {float(value)}")
            else:
                exec(f"args.{key.upper()} = '{value}'")
        except:
            pass


def load_args():
    global args
    parser = argparse.ArgumentParser(description='Load up the DFS')
    parser.add_argument('--CONFIG', '-f', type=str,
                        help='Path to the DFS config file')
    args = parser.parse_args()

    if args.CONFIG is None:
        with open('CONFIG.txt', 'r') as log_file:
            lines = log_file.read().split('\n')
            lines = list(filter(bool, lines))
            try:
                last_load = lines[-1]
            except:
                print("No config file found. Please provide a config file.")
                exit(1)
            last_loaded_setup = last_load.split('\t')[-1]
            args.CONFIG = last_loaded_setup
            print(f"Using the last loaded setup: {last_loaded_setup}")
    args.CONFIG = Path(args.CONFIG).absolute()

    if not(Path(args.CONFIG).exists() and Path(args.CONFIG).is_file() and Path(args.CONFIG).suffix == '.json'):
        print("Configuration file does not exist. Please provide a valid config file.")
        exit(1)

    load_config_from_json(args.CONFIG)

    if not Path(args.PATH_TO_NAMENODES).exists():
        print("Path to Name Nodes does not exist. Please create the DFS and try again")
        exit(1)

    if not Path(args.PATH_TO_DATANODES).exists():
        print("Path to Data Nodes does not exist. Please create the DFS and try again")
        exit(1)

    if args.NUM_LOAD == 0:
        print("DFS has been loaded for the first time. Please format using the `format` command")
        _input = None
        while _input != "format":
            _input = input("(yadfs) > ")
            if _input == "format":
                format_namenode_datanode(quit=False)
            else:
                print("Please enter `format` to format the DFS")

    args.NUM_LOAD += 1
    with open(args.CONFIG_LOG_PATH, 'a') as f:
        f.write(
            f"{datetime.datetime.now(IST)}\t{str(Path(args.DFS_SETUP_CONFIG).absolute())}\n")

    with open(args.DFS_SETUP_CONFIG, "w") as f:
        dfs_setup_config_dict = dict()
        dfs_setup_config_dict.update(args.__dict__)
        try:
            del dfs_setup_config_dict["FILESYSTEM"]
        except:
            pass
        try:
            del dfs_setup_config_dict["BLOCK_INFO"]
        except:
            pass
        try:
            del dfs_setup_config_dict["DATANODE_INFO"]
        except:
            pass
        dfs_setup_config_dict["TIMESTAMP"] = str(datetime.datetime.now(IST))
        dfs_setup_config_dict["NUM_LOAD"] = args.NUM_LOAD
        json.dump(dfs_setup_config_dict, f, indent=4)

    if args.NUM_LOAD == 1:
        exit(0)

    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(
            args.FILESYSTEM_INFO_FILENAME), 'r') as f:
        args.FILESYSTEM = json.load(f)

    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.DATANODE_INFO_FILENAME), 'r') as f:
        args.DATANODE_INFO = json.load(f)

    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.BLOCK_INFO_FILENAME), 'r') as f:
        args.BLOCK_INFO = json.load(f)

    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.FILE_INFO_FILENAME), 'r') as f:
        args.FILE_INFO = json.load(f)


def format_namenode_datanode(quit=True, *vargs):
    namenode_path = Path(args.PATH_TO_NAMENODES)
    shutil.rmtree(str(Path(namenode_path).joinpath(
        args.NAMENODE_CHECKPOINTS_PATH)))
    Path(namenode_path).joinpath(args.NAMENODE_CHECKPOINTS_PATH).mkdir(
        parents=True, exist_ok=True)
    Path(namenode_path).joinpath(args.NAMENODE_LOG_PATH).unlink()
    Path(namenode_path).joinpath(args.NAMENODE_LOG_PATH).touch()

    primary_namenode_path = Path(namenode_path).joinpath(
        args.PRIMARY_NAMENODE_NAME)
    with open(primary_namenode_path.joinpath(args.FILE_INFO_FILENAME), 'w') as f:
        json.dump(dict(), f)

    with open(primary_namenode_path.joinpath(args.BLOCK_INFO_FILENAME), 'w') as f:
        json.dump(dict(), f)

    datanode_info = dict()
    for i in range(args.NUM_DATANODES):
        datanode_info[f"DATANODE{i}"] = list()

        shutil.rmtree(
            str(Path(args.PATH_TO_DATANODES).joinpath(f"DATANODE{i}")))
        Path(args.PATH_TO_DATANODES).joinpath(
            f"DATANODE{i}").mkdir(parents=True, exist_ok=True)

        Path(args.DATANODE_LOG_PATH).joinpath(f"DATANODE{i}_LOG.txt").unlink
        Path(args.DATANODE_LOG_PATH).joinpath(
            f"DATANODE{i}_LOG.txt").touch(exist_ok=True)

    with open(primary_namenode_path.joinpath(args.DATANODE_INFO_FILENAME), "w") as f:
        json.dump(datanode_info, f)

    with open(primary_namenode_path.joinpath(args.FILESYSTEM_INFO_FILENAME), 'w') as f:
        json.dump(dict(), f)

    args.FILESYSTEM = dict()

    secondary_namenode_path = Path(namenode_path).joinpath(
        args.SECONDARY_NAMENODE_NAME)
    shutil.rmtree(str(secondary_namenode_path))

    update_namenode_filesystem_info()
    update_namenode_block_info_local()
    update_namenode_datanode_info_local()
    update_secondary_namenode()
    create_namenode_checkpoints()

    print("Name Node and Data Nodes formatted successfully. Please restart.")
    if quit:
        exit(0)


def check_namenode_and_metadata_exists():
    primary_namenode_path = Path(
        args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME)
    if primary_namenode_path.exists():
        return primary_namenode_path.joinpath(args.BLOCK_INFO_FILENAME).exists() and \
            primary_namenode_path.joinpath(args.DATANODE_INFO_FILENAME).exists() and \
            primary_namenode_path.joinpath(args.FILE_INFO_FILENAME).exists() and \
            primary_namenode_path.joinpath(
            args.FILESYSTEM_INFO_FILENAME).exists()
    else:
        return False


def check_and_revive_primary_namenode():
    if not Path(args.PATH_TO_NAMENODES).joinpath(args.NAMENODE_LOG_PATH).exists():
        Path(args.PATH_TO_NAMENODES).joinpath(args.NAMENODE_LOG_PATH).touch()

    primary_namenode_path = Path(
        args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME)
    if not check_namenode_and_metadata_exists():
        if not primary_namenode_path.exists():
            primary_namenode_path.mkdir(parents=True)
        secondary_namenode_path = Path(
            args.PATH_TO_NAMENODES).joinpath(args.SECONDARY_NAMENODE_NAME)
        if secondary_namenode_path.exists():
            files_in_secondary_namenode = secondary_namenode_path.glob('**/*')
            files_in_secondary_namenode = list(
                filter(Path.is_file, files_in_secondary_namenode))
            for file in files_in_secondary_namenode:
                destination_path = str(
                    primary_namenode_path.joinpath(file.name))
                shutil.copy(str(file), destination_path)
        else:
            print(
                'No Secondary Name Node found to revive Primary Name Node. Please create another DFS.')
            exit()


def update_secondary_namenode():
    secondary_namenode_path = Path(
        args.PATH_TO_NAMENODES).joinpath(args.SECONDARY_NAMENODE_NAME)
    if not secondary_namenode_path.exists():
        secondary_namenode_path.mkdir(parents=True)

    files_in_secondary_namenode = secondary_namenode_path.glob('**/*')
    files_in_secondary_namenode = list(
        filter(Path.is_file, files_in_secondary_namenode))
    for filename in files_in_secondary_namenode:
        filename.unlink()

    primary_namenode_path = Path(
        args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME)
    files_in_primary_namenode = primary_namenode_path.glob('**/*')
    files_in_primary_namenode = list(
        filter(Path.is_file, files_in_primary_namenode))

    for filename in files_in_primary_namenode:
        root_name = filename.name
        destination_path = str(secondary_namenode_path.joinpath(root_name))
        filename = str(filename)
        shutil.copy(filename, destination_path)


def create_namenode_checkpoints():
    current_time = datetime.datetime.now(IST)
    checkpoint_name = f"CHECKPOINT_{current_time}"
    checkpoint_path = Path(
        args.NAMENODE_CHECKPOINTS_PATH).joinpath(checkpoint_name)
    checkpoint_path.mkdir(parents=True)

    primary_namenode_path = Path(
        args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME)
    files_in_primary_namenode = primary_namenode_path.glob('**/*')
    files_in_primary_namenode = list(
        filter(Path.is_file, files_in_primary_namenode))

    for filename in files_in_primary_namenode:
        root_name = filename.name
        destination_path = str(checkpoint_path.joinpath(root_name))
        filename = str(filename)
        shutil.copy(filename, destination_path)


def update_namenode_datanode_info_local():
    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.DATANODE_INFO_FILENAME), 'r') as f:
        datanode_info = json.load(f)

    for i in range(args.NUM_DATANODES):
        datanode_name = f"DATANODE{i}"
        datanode_path = Path(
            args.PATH_TO_DATANODES).joinpath(datanode_name)
        # handle deleted data node
        blocks_in_datanode = datanode_path.glob('**/*')
        blocks_in_datanode = list(filter(Path.is_file, blocks_in_datanode))
        blocks_in_datanode = list(
            map(lambda x: str(x.name), blocks_in_datanode))
        datanode_info[datanode_name] = blocks_in_datanode

    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.DATANODE_INFO_FILENAME), 'w') as f:
        json.dump(datanode_info, f)

    args.DATANODE_INFO = datanode_info


def update_namenode_block_info_local():
    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.DATANODE_INFO_FILENAME), 'r') as f:
        datanode_info = json.load(f)

    block_info = dict()
    for datanode_id in datanode_info:
        for block_id in datanode_info[datanode_id]:
            if block_id not in block_info:
                block_info[block_id] = list()
            block_info[block_id].append(datanode_id)

    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.BLOCK_INFO_FILENAME), 'w') as f:
        json.dump(block_info, f)

    args.BLOCK_INFO = block_info


def update_namenode_file_info():
    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.FILE_INFO_FILENAME), 'w') as f:
        json.dump(args.FILE_INFO, f)

    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.FILE_INFO_FILENAME), 'r') as f:
        args.FILE_INFO = json.load(f)


def update_namenode_datanode_info():
    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.DATANODE_INFO_FILENAME), 'w') as f:
        json.dump(args.DATANODE_INFO, f)

    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.DATANODE_INFO_FILENAME), 'r') as f:
        args.DATANODE_INFO = json.load(f)


def update_namenode_block_info():
    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.BLOCK_INFO_FILENAME), 'w') as f:
        json.dump(args.BLOCK_INFO, f)

    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.BLOCK_INFO_FILENAME), 'r') as f:
        args.BLOCK_INFO = json.load(f)


def update_namenode_filesystem_info():
    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.FILESYSTEM_INFO_FILENAME), 'w') as f:
        json.dump(args.FILESYSTEM, f)

    with open(Path(args.PATH_TO_NAMENODES).joinpath(args.PRIMARY_NAMENODE_NAME).joinpath(args.FILESYSTEM_INFO_FILENAME), 'r') as f:
        args.FILESYSTEM = json.load(f)


def get_file_block_details(file_path):
    file_path = Path(file_path)
    if file_path.exists() and file_path.is_file():
        # handle 1024?
        file_size = file_path.stat().st_size
        return file_size
    else:
        return None


def check_path_exists_in_hdfs(path):
    components = path.split('/')
    components = list(filter(bool, components))  # A/B/script.py
    # print(components)
    current = args.FILESYSTEM
    # print(args.FILESYSTEM)
    for index, component in enumerate(components):
        if component in current:
            if current[component] is None:  # and component == components[-1]:
                return True
            current = current[component]
        else:
            return False
    return True


def create_path_in_hdfs(destination_file_path):
    if not check_path_exists_in_hdfs(destination_file_path):
        components = destination_file_path.split('/')
        components = list(filter(bool, components))
        current = args.FILESYSTEM
        for component in components:
            if component not in current:
                current[component] = dict()
            current = current[component]
        return True
    else:
        return False


def create_file_in_hdfs(destination_file_path):
    if not check_path_exists_in_hdfs(destination_file_path):
        components = destination_file_path.split('/')
        components = list(filter(bool, components))
        filename = components[-1]
        current = args.FILESYSTEM
        for component in components[:-1]:
            if component not in current:
                current[component] = dict()
            current = current[component]
        current[filename] = None
        return True
    else:
        return False


def choose_datanode(mode="least", block_path=None, replica_count=None):
    all_datanodes = list(args.DATANODE_INFO.keys())
    datanode_capacities = list(
        map(lambda x: len(args.DATANODE_INFO[x]), all_datanodes))
    datanodes = list(zip(all_datanodes, datanode_capacities))
    available_datanodes = list(
        filter(lambda x: x[1] <= args.DATANODE_SIZE, datanodes))
    if not available_datanodes:
        return None
    else:
        if mode == "least":
            available_datanodes.sort(key=lambda x: x[1])
            return available_datanodes[0][0]
        elif mode == "random":
            return random.choice(available_datanodes)[0]
        elif mode == 'hashing':
            with open(block_path, 'r') as f:
                block_hash = f.read()
            block_hash = hash(block_hash) + replica_count
            block_hash = block_hash % len(available_datanodes)
            return available_datanodes[block_hash][0]


def mkdir(*vargs):
    path = vargs[0]
    status = create_path_in_hdfs(path)
    if status:
        update_namenode_filesystem_info()
        return True
    else:
        print(f"Error: Directory {path} already exists.")
        return False


def ls(*vargs):
    if vargs:
        path = vargs[0]
        if path == '.':
            path = '/'
    else:
        path = '/'
    recursive = False
    if len(vargs) > 1 and vargs[1].lower() == '-r':
        recursive = True
    status = check_path_exists_in_hdfs(path)
    if status:
        components = path.split('/')
        components = list(filter(bool, components))
        if components:
            current = args.FILESYSTEM
            for index, component in enumerate(components):
                if component in current:
                    current = current[component]
            if current is None:
                print(f"Error: Path {path} is a file, not a directory")
                return False
            else:
                if not recursive:
                    if list(current.keys()):
                        ls_items = '\n'.join(list(current.keys())).strip()
                        print(ls_items)
                else:
                    if current:
                        print(json.dumps(current, indent=4))
                return True
        else:
            if not recursive:
                if list(args.FILESYSTEM.keys()):
                    ls_items = '\n'.join(list(args.FILESYSTEM.keys())).strip()
                    print(ls_items)
            else:
                if args.FILESYSTEM:
                    print(json.dumps(args.FILESYSTEM, indent=4))
            return True
    else:
        print(f"Error: Path {path} not found.")
        return False


def remove_file_from_datanodes(file_id):
    num_blocks = args.FILE_INFO[file_id]['num_blocks']
    block_ids = [f"{file_id}__{i}" for i in range(1, num_blocks + 1)]
    for b_id in block_ids:
        del args.BLOCK_INFO[b_id]
    update_namenode_block_info()

    for datanode_id in range(args.NUM_DATANODES):
        datanode_id = f"DATANODE{datanode_id}"
        args.DATANODE_INFO[datanode_id] = [
            b_id for b_id in args.DATANODE_INFO[datanode_id] if b_id not in block_ids]
        datanode_path = Path(args.PATH_TO_DATANODES).joinpath(datanode_id)
        blocks_in_datanode = list(datanode_path.glob('**/*'))
        for block in blocks_in_datanode:
            if block.parts[-1] in block_ids:
                block.unlink()
    # update_namenode_block_info()
    update_namenode_datanode_info()


def rm(*vargs):
    path = vargs[0]
    if check_path_exists_in_hdfs(path):
        components = path.split('/')
        components = list(filter(bool, components))
        current = args.FILESYSTEM
        for component in components[:-1]:
            if component in current:
                current = current[component]
        if components[-1] in current:
            if current[components[-1]] is None:
                del current[components[-1]]
                update_namenode_filesystem_info()
                file_id = get_file_id_from_hdfs_file_path(path)
                remove_file_from_datanodes(file_id)
                del args.FILE_INFO[file_id]
                update_namenode_file_info()
                return True
            else:
                print(
                    f"Error: Path {path} is a directory, not a file. Use rmdir instead.")
        else:
            print(f"Error: Path {path} not found.")
            return False
    else:
        print(f"Error: Path {path} not found.")
        return False


def rmdir(*vargs):
    path = vargs[0]
    if check_path_exists_in_hdfs(path):
        components = path.split('/')
        components = list(filter(bool, components))
        temp_filesystem = dict(args.FILESYSTEM)
        current = temp_filesystem
        for component in components[:-1]:
            if component in current:
                current = current[component]
        if components[-1] in current:
            if not current[components[-1]] is None:
                delete_subdir_files(path)
                del current[components[-1]]
                args.FILESYSTEM = temp_filesystem
                update_namenode_filesystem_info()
                return True
            else:
                print(
                    f"Error: Path {path} is a file, not a directory. Use rm instead.")
        else:
            print(f"Error: Path {path} not found.")
            return False
    else:
        print(f"Error: Path {path} not found.")
        return False


def delete_subdir_files(dir_delete_path):
    files_to_delete = list()
    for file_id in args.FILE_INFO:
        file_path = args.FILE_INFO[file_id]['file_path']
        file_path_components = file_path.split('/')
        file_path_components = list(filter(bool, file_path_components))
        dir_delete_path_components = dir_delete_path.split('/')
        dir_delete_path_components = list(
            filter(bool, dir_delete_path_components))
        if dir_delete_path_components == file_path_components[:len(dir_delete_path_components)]:
            files_to_delete.append(file_path)
    for file_path in files_to_delete:
        rm(file_path)


def get_file_id_from_hdfs_file_path(file_path):
    for file_id in args.FILE_INFO:
        if args.FILE_INFO[file_id]['file_path'] == file_path:
            return file_id
    return None


def get_datanode_id_from_block_id(block_id):
    if block_id in args.BLOCK_INFO:
        possible_datanodes = args.BLOCK_INFO[block_id]
        for datanode_id in possible_datanodes:
            if Path(args.PATH_TO_DATANODES).joinpath(datanode_id).joinpath(block_id).exists():
                return datanode_id
        return None
    else:
        return None


def put(*vargs):
    source_file_path, destination_file_path = vargs
    file_size = get_file_block_details(source_file_path)
    if file_size is None:
        print(f"Error: {source_file_path} not found")
        return False
    else:
        check_file_created = create_file_in_hdfs(destination_file_path)
        if check_file_created:
            Path("./temp").mkdir(parents=True, exist_ok=True)

            file_splitter.split(
                file=source_file_path,
                split_size=int(args.BLOCK_SIZE * args.BLOCK_SIZE_UNIT),
                output_dir="./temp",
                newline=True
            )
            num_blocks = len(list(Path("./temp").glob("*"))) - 1

            existing_file_ids = list(args.FILE_INFO.keys())
            if existing_file_ids:
                existing_file_ids = list(
                    map(lambda x: int(x[-3:]), existing_file_ids))
                incremented_id = str(max(existing_file_ids) + 1).zfill(3)
                new_file_id = f"FILE_{incremented_id}"
            else:
                new_file_id = "FILE_000"

            args.FILE_INFO[new_file_id] = {
                "file_path": destination_file_path,
                "num_blocks": num_blocks,
                "file_size": file_size
            }

            update_namenode_file_info()
            update_namenode_filesystem_info()

            block_root_path = Path("./temp")
            block_filename = Path(source_file_path).stem
            block_suffix = Path(source_file_path).suffix
            for i in range(1, num_blocks+1):
                current_block_name = f"{block_filename}_{i}"
                if block_suffix:
                    current_block_name += block_suffix
                current_block_path = block_root_path.joinpath(
                    current_block_name)
                destination_block_name = f"{new_file_id}__{i}"
                for j in range(args.REPLICATION_FACTOR):
                    datanode_id = choose_datanode(
                        mode="hashing", block_path=current_block_path, replica_count=j)
                    if datanode_id is None:
                        print("Memory full")
                        del args.FILE_INFO[new_file_id]
                        update_namenode_file_info()
                        update_namenode_filesystem_info()
                        return
                    else:
                        path_to_datanode_block = Path(
                            args.PATH_TO_DATANODES).joinpath(datanode_id).joinpath(destination_block_name)
                        shutil.copy(str(current_block_path),
                                    str(path_to_datanode_block))
                        log_datanode(
                            datanode_id, destination_block_name, "put")
                        if destination_block_name not in args.BLOCK_INFO:
                            args.BLOCK_INFO[destination_block_name] = list()
                        args.BLOCK_INFO[destination_block_name].append(
                            datanode_id)
                        args.DATANODE_INFO[datanode_id].append(
                            destination_block_name)
            shutil.rmtree(block_root_path)
            update_namenode_block_info()
            update_namenode_datanode_info()
            return True
        else:
            print("File already exists")
            return False

import shutil

def get(source_file_path, destination_local_path):
    file_id = get_file_id_from_hdfs_file_path(source_file_path)

    # Check if the file exists
    if file_id is None or file_id not in args.FILE_INFO:
        print(f"Error: File {source_file_path} not found.")
        return False

    file_info = args.FILE_INFO[file_id]
    num_blocks = file_info["num_blocks"]

    # Check if the destination directory exists, create it if not
    os.makedirs(destination_local_path, exist_ok=True)

    # Construct the destination file path
    destination_file_path = os.path.join(destination_local_path, os.path.basename(source_file_path))

    # Check if the destination file already exists
    if os.path.exists(destination_file_path):
        print(f"Error: Destination file {destination_file_path} already exists.")
        return False

    # Create the destination file
    with open(destination_file_path, 'wb') as destination_file:
        for block_num in range(1, num_blocks + 1):
            block_name = f"{file_id}__{block_num}"
            block_replicas = args.BLOCK_INFO.get(block_name, [])

            # Choose one of the replicas (for simplicity, just choose the first one)
            if block_replicas:
                datanode_id = block_replicas[0]

                # Simulate data transfer (replace this with your actual implementation)
                block_content = read_block_from_datanode(datanode_id, block_name)

                # Write the block content to the destination file
                destination_file.write(block_content)
            else:
                print(f"Error: Block {block_name} not available on any datanode.")

    print(f"Download successful: {source_file_path} -> {destination_file_path}")
    return True

# Helper function to read block content from a datanode (replace this with your actual implementation)
def read_block_from_datanode(datanode_id, block_name):
    # Simulate reading data from the datanode (replace this with your actual implementation)
    #return bytes(f"Content of {block_name} from {datanode_id}", 'utf-8')
    datanode_path = os.path.join("/home/pes2ug21cs451/bd_project/demo/DATANODE", datanode_id)
    block_path = os.path.join(datanode_path, block_name)

    with open(block_path, 'rb') as block_file:
        return block_file.read()
        
def cat(*vargs):
    file_path = vargs[0]
    if check_path_exists_in_hdfs(file_path):
        file_id = get_file_id_from_hdfs_file_path(file_path)
        if file_id is None:
            print("Error: File not found.")
            return False
        num_blocks = args.FILE_INFO[file_id]['num_blocks']
        block_id = [f"{file_id}__{bid}" for bid in range(1, num_blocks+1)]
        block_paths = dict()
        for block_id in block_id:
            datanode_id = get_datanode_id_from_block_id(block_id)
            log_datanode(datanode_id, block_id, "cat")
            block_paths[block_id] = Path(
                args.PATH_TO_DATANODES).joinpath(datanode_id).joinpath(block_id)

        if None in block_paths.values():
            print("Error: Missing blocks or file not found.")
            return False
        else:
            block_paths = sorted(block_paths.items(),
                                 key=lambda x: int(x[0].split('__')[1]))
            for _, block_path in block_paths:
                with open(block_path, "r") as f:
                    print(f.read().strip())
            return True
    else:
        print(f"File {file_path} not found.")
        return False

def log_datanode(datanode_id, block_id, message):
    datanode_path = f"{datanode_id}_LOG.txt"
    date = str(datetime.datetime.now(IST))
    with open(Path(args.DATANODE_LOG_PATH).joinpath(datanode_path), "a") as f:
        f.write(f"{date} {block_id} {message.upper()}\n")


def log_namenode(message):
    date = str(datetime.datetime.now(IST))
    with open(Path(args.NAMENODE_LOG_PATH), "a") as f:
        f.write(f"{date} {message.upper()}\n")


load_args()


@ TIMED_TASK_LOOP.job(interval=datetime.timedelta(seconds=args.SYNC_PERIOD))
def update_namenode():
    check_and_revive_primary_namenode()
    log_namenode("SYNC")
    # check_and_revive_datanodes()
    update_namenode_datanode_info_local()
    update_namenode_block_info_local()
    update_secondary_namenode()
    create_namenode_checkpoints()


TIMED_TASK_LOOP.start()

command_map = {
    "put": put,
    "rm": rm,
    "mkdir": mkdir,
    "rmdir": rmdir,
    "ls": ls,
    "cat": cat,
    "format": format_namenode_datanode,
    "move_dir": move_directory,
    "move_f": move_file,
    "copy_f": copy_file,
    "copy_dir": copy_directory, 
    "get": get,
}


def process_input(_input):
    components = _input.split()
    command_string = components[0]
    _function = command_map.get(command_string)
    if _function is None:
        possible_commands = ', '.join(list(command_map.keys()))
        print(
            f"Invalid command. Valid commands are: {possible_commands}")
        return
    else:
        check_and_revive_primary_namenode()
        log_namenode(components[0])
        # check_and_revive_datanodes()
        if len(components) == 1:
            _function()
        else:
            _function(*components[1:])

        if command_string == "format":
            exit(0)


while True:
    _input = input("(yadfs) > ")
    if _input.lower() == "q":
        TIMED_TASK_LOOP.stop()
        exit(0)

    try:
        process_input(_input)
    except Exception as error_message:
        print(f"ERROR: {error_message}")
