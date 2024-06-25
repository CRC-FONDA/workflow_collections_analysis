import os
import subprocess


def print_dag_from_dag_string(dag_string, path, dag_name):
    tmp_dag_path = path+dag_name+"_tmp.txt"
    with open(tmp_dag_path, "w") as f:
        f.write(dag_string)
    subprocess.run(["cat " + dag_name + "_tmp.txt | dot -Tpdf > " + dag_name + ".pdf"], cwd=path, shell=True)
    subprocess.run(["rm " + tmp_dag_path], shell=True)

