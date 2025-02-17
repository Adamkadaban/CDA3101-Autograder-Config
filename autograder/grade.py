#!/usr/bin/env python3

import json
import os
import math
import yaml
from datetime import datetime
from pwn import context, ssh

CONFIG_FILE = "config.yml"
SUBMISSION_DIR = "/autograder/submission/"
RESULTS_FILE = "/autograder/results/results.json"
METADATA_FILE = "/autograder/submission_metadata.json"
TESTCASES_DIR = "./testcases"

context.log_level = "error"


def load_config():
    try:
        with open(CONFIG_FILE) as fin:
            config = yaml.safe_load(fin)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        write_results(0, "Autograder configuration error. Please contact staff.")


def write_results(score, output, testcases=None, output_format="text"):
    result = {"score": score, "output_format": output_format}
    if testcases:
        result["tests"] = testcases
    if output:
        result["output"] = output
    with open(RESULTS_FILE, "w") as fout:
        fout.write(json.dumps(result))

    # This tells run_autograder that grading was successful
    exit(0)


def remove_whitespace(s):
    return [i for i in s if i not in b" \n\t\r"]


def validate_config(config):
    try:
        required_keys = ["source_name", "exists_max", "compiles_max", "test_case_max"]
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required key: {key}")

        config["recursive_max"] = float(config.get("recursive_max", 0))
        config["exists_max"] = float(config["exists_max"])
        config["compiles_max"] = float(config["compiles_max"])
        config["test_case_max"] = float(config["test_case_max"])

        total_points = sum(
            [
                config[k]
                for k in [
                    "exists_max",
                    "compiles_max",
                    "test_case_max",
                    "recursive_max",
                ]
            ]
        )
        assert total_points == 100, "Total points must sum to 100."
        return config
    except (KeyError, ValueError, AssertionError) as e:
        print(f"Config validation error: {e}")
        write_results(0, "Autograder configuration error. Please contact staff.")


def get_submission_file():
    files = os.listdir(SUBMISSION_DIR)
    if not files:
        write_results(0, "No submission file found.")
    return os.path.join(SUBMISSION_DIR, files[0])


def calculate_late_penalty(metadata):
    submission_time = datetime.fromisoformat(metadata["created_at"])
    due_time = datetime.fromisoformat(metadata["assignment"]["due_date"])
    late_due_time = datetime.fromisoformat(metadata["assignment"]["late_due_date"])

    days_late = (submission_time - due_time).total_seconds() / (60 * 60 * 24)
    print(f"DAYS LATE: {days_late}")

    penalty = min(-10 * math.ceil(days_late), 0)
    if submission_time > late_due_time:
        penalty = -100
    return penalty


def compile_code(r, source_name, bin_name):
    return r(f"gcc {source_name} -o {bin_name} 2>/dev/null; echo $?") == b"0"


def run_testcases(r, bin_name, test_case_max, num_testcases):
    points_per_testcase = test_case_max / num_testcases
    testcases = []
    total_score = 0

    for i in range(1, num_testcases + 1):
        input_path = os.path.join(TESTCASES_DIR, "Input", f"{i}.in")
        expected_output_path = os.path.join(TESTCASES_DIR, "Output", f"{i}.out")
        output_path = f"test-{i}.out"

        with open(input_path, "r") as fin:
            tc_stdin = fin.read()
        r(f"stdbuf -oL ./{bin_name} < {input_path} > {output_path}")
        student_stdout = r.download_data(output_path)

        with open(expected_output_path, "rb") as fin:
            tc_stdout = fin.read()

        passed = remove_whitespace(student_stdout) == remove_whitespace(tc_stdout)

        if passed:
            total_score += points_per_testcase

        testcases.append(
            {
                "score": points_per_testcase if passed else 0,
                "max_score": points_per_testcase,
                "status": "passed" if passed else "failed",
                "output": f"Input:\n{tc_stdin}\n\nOutput:\n{student_stdout.decode()}\n\nExpected:\n{tc_stdout.decode()}",
                "output_format": "text",
                "visibility": "visible",
            }
        )
    return total_score, testcases


def main():
    config = validate_config(load_config())
    source_name = config["source_name"]
    bin_name = source_name[:-2]
    required_extension = source_name.split(".")[-1]

    submission_path = get_submission_file()
    exists = submission_path.endswith(required_extension)
    if not exists:
        write_results(
            0,
            f"No file with the `{required_extension}` extension found.",
            output_format="md",
        )
    total_score = config["exists_max"]

    r = ssh(user="root", password="root", host="localhost", port=3101, timeout=600)
    r.upload_file(submission_path, f"/root/{source_name}")
    r.upload(TESTCASES_DIR)

    with open(METADATA_FILE) as fin:
        submission_metadata = json.load(fin)
    penalty = calculate_late_penalty(submission_metadata)

    if not compile_code(r, source_name, bin_name):
        write_results(max(10 + penalty, 0), "Failed to compile")
    total_score += config["compiles_max"]

    num_testcases = len(os.listdir(os.path.join(TESTCASES_DIR, "Input")))
    test_score, testcases = run_testcases(
        r, bin_name, config["test_case_max"], num_testcases
    )
    total_score += test_score

    # TODO: Figure out smart way to have recursive points
    # This should probably be manually graded?
    # if config["recursive_max"] > 0:
    #    recursive_score, recursive_case = run_recursive_case(r, config[""])

    student_score = max(total_score + penalty, 0)
    write_results(student_score, "", testcases)


if __name__ == "__main__":
    main()
