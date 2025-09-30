import os
import sys
import time
from enum import Enum

import pandas as pd
from tqdm import tqdm

from parse_dimacs import parse_dimacs
from timeout import timeout_wrapper, TimeoutError


class TestResult(Enum):
    UNSAT = 0
    SAT = 1
    TIMEOUT = 2


def run_test(filepath, verbose: bool = False, timeout: int = 5):
    _, filename = os.path.split(filepath)
    if verbose:
        print("Parsing file:", filename)
    problem = parse_dimacs(filepath)
    if verbose:
        print(problem)
        print("Solving problem...")
    start_time = time.time()
    try:
        result = timeout_wrapper(
            problem.dpll, kwargs={"verbose": verbose}, timeout_seconds=timeout
        )
        runtime = time.time() - start_time
        if verbose:
            print(
                "Solved problem in {:.2f}s: {}".format(
                    runtime, "SAT" if result else "UNSAT"
                )
            )
        if result:
            return TestResult.SAT, runtime
        else:
            return TestResult.UNSAT, runtime
    except TimeoutError:
        if verbose:
            print("Problem solve process timed out ({}s)".format(timeout))
        return TestResult.TIMEOUT, timeout


if __name__ == "__main__":
    filenames = os.listdir("aim")
    timeout = 10  # seconds
    test_results = []
    runtimes = []
    num_problems = len(filenames)
    with tqdm(total=num_problems, desc="Total Progress") as pbar:
        for i, filename in enumerate(filenames):
            desc = f"\rProcessing item {i+1} of {len(filenames)}... "
            pbar.set_description(desc)
            pbar.update(1)
            filepath = os.path.join("aim", filename)
            test_result, runtime = run_test(filepath, verbose=False, timeout=timeout)
            test_results.append(test_result)
            runtimes.append(runtime)
    df_results = pd.DataFrame(
        {
            "filename": filenames,
            "result": [result.name for result in test_results],
            "runtime": runtimes,
        }
    )
    print("Writing results to CSV...")
    df_results.to_csv(os.path.join("results", "results_2025-09-29.csv"), index=False)
    print("Done.")
