from utility.parsers import iterate_rules
import numpy as np
import math


def accumulate_meta_results(meta_results, meta_result):
    return [(x[0] + x[1] if x[1] != [0] else x[0]) for x in zip(meta_results, meta_result)]


def write_meta_results(path, meta_results):
    with open(path, "w") as f:
        f.write("Number of rules: "+str(meta_results[0])+"\n")
        f.write("Number of shell rules: " + str(len(meta_results[1])) + "\n")
        f.write("Numbers of shell lines: " + str(meta_results[1]) + "\n")
        p25, p50, p75 = get_percentiles(meta_results[1])
        f.write("Percentiles: p25=" + str(p25)+", p50=" + str(p50) + ", p75="+str(p75)+"\n")
        f.write("Average shell lines: " + str(np.mean(meta_results[1])) + "\n")
        f.write("Number of run rules: " + str(len(meta_results[2])) + "\n")
        f.write("Numbers of run lines: " + str(meta_results[2]) + "\n")
        p25, p50, p75 = get_percentiles(meta_results[2])
        f.write("Percentiles: p25=" + str(p25) + ", p50=" + str(p50) + ", p75=" + str(p75) + "\n")
        f.write("Average run lines: " + str(np.mean(meta_results[2])) + "\n")
        f.write("Number of script rules: " + str(len(meta_results[3])) + "\n")
        f.write("Numbers of script lines: " + str(meta_results[3]) + "\n")
        p25, p50, p75 = get_percentiles(meta_results[3])
        f.write("Percentiles: p25=" + str(p25) + ", p50=" + str(p50) + ", p75=" + str(p75) + "\n")
        f.write("Average script lines: " + str(np.mean(meta_results[3])) + "\n")
        f.write("Number of wrapper rules: " + str(len(meta_results[4])) + "\n")
        f.write("Numbers of wrapper lines: " + str(meta_results[4]) + "\n")
        p25, p50, p75 = get_percentiles(meta_results[4])
        f.write("Percentiles: p25=" + str(p25) + ", p50=" + str(p50) + ", p75=" + str(p75) + "\n")
        f.write("Average wrapper lines: " + str(np.mean(meta_results[4])) + "\n")
        f.write("Number of executed rules: " + str(meta_results[5]) + "\n")
        f.write("Number of rules with multiple executions: " + str(meta_results[6]) + "\n")


def get_percentiles(results_list):
    length = len(results_list)
    try:
        results_list.sort(key=lambda x: x[0])
    except TypeError as e:
        results_list.sort()
    p25 = results_list[math.floor(length / 4)]
    p50 = results_list[math.floor(length / 2)]
    p75 = results_list[math.floor((length / 4) * 3)]
    return p25, p50, p75


report_path = "report.txt"
metaresults_path = "metaresults.txt"
meta_results = [0, [], [], [], [], 0, 0]
for result in queries.iterate_all_rules():
    queries.write_rule_iteration(report_path, result)
    meta_results = accumulate_meta_results(meta_results, queries.collect_meta_results(result))

write_meta_results(metaresults_path, meta_results)

print("done!")
