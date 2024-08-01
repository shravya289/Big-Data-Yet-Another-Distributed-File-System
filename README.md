# EC-Team-51-Yet-Another-Distributed-File-System-YADFS-
Repo for EC-Team-51-Yet Another Distributed File System (YADFS)

Yet Another Distributed File System (YADFS):

YADFS is a distributed file system designed to provide scalable and reliable storage for large-scale applications. Whether you're dealing with big data processing, distributed computing, or simply need a robust and fault-tolerant file storage solution, YADFS has got you covered.

Key Features:

Scalability: YADFS is designed to scale horizontally, allowing you to seamlessly add more nodes to your cluster as your storage needs grow.

Fault Tolerance: With built-in redundancy and fault-tolerant mechanisms, YADFS ensures data integrity and availability even in the face of hardware failures or network issues.

Distributed Architecture: YADFS distributes data across multiple nodes, optimizing performance and reducing the risk of bottlenecks.

Efficient Data Access: YADFS provides efficient data access through distributed caching and intelligent data placement, minimizing latency and optimizing throughput.

#Installation
Follow these steps to set up YADFS on your distributed environment:

clone it first using git clone

after cloning change the config_files paths according to your system

1. Setup the Distributed File System
   
To set up the distributed file system, use the setup.py script. The configuration for the setup is provided in the config_sample.json file.
usage: setup.py [-h] --CONFIG CONFIG [--CLEANUP CLEANUP]

Setup the DFS

optional arguments:
  -h, --help            show this help message and exit
  --CONFIG CONFIG, -f CONFIG
                        Path to the config file
  --CLEANUP CLEANUP, -c CLEANUP
                        Overwrite existing DFS

  Example:
python3 setup.py --CONFIG config_sample.json --CLEANUP True

Running this script will generate a configuration file (dfs_setup.json) to load the distributed file system from.

2. Access the Distributed File System

   Once the DFS is set up, use the hdfs.py script to interact with it. The CLI tool provides commands for managing the distributed file system
   
usage: hdfs.py [-h] --CONFIG CONFIG

Load up the DFS

optional arguments:
  -h, --help            show this help message and exit
  --CONFIG CONFIG, -f CONFIG
                        Path to the DFS config file

Example:
python3 hdfs.py --CONFIG dfs_setup.json

Use this CLI to perform various operations on the distributed file system, such as uploading, downloading, and managing files.

TEAM MEMBERS:

M BHAVYA,
S SAI SREE LAKSHMI,
SAHANA S PATIL,
SHRAVYA REDDY B

Enjoy using Yet Another Distributed File System!



