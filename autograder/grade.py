#!/usr/bin/env python3

import json
from pwn import *
from os import listdir as os_listdir
import os.path

context.log_level='warn'

source_name = 'pa1.s'
compiles_max = 10
test_case_max = 80
exists_max = 10

ssh_timeout = 600 # 10 minutes. (emulator needs to start first)

submission_filename = os_listdir('/autograder/submission/')[0] # we assume a file exists, as a student must submit a file for the program to run
source_path = f'/autograder/submission/{submission_filename}'

num_testcases = len(os.listdir('./testcases/Input'))
points_per_testcase = test_case_max / num_testcases
bin_name = source_name[:-2]
exists = ( os.path.exists(source_path) )

r = ssh(user='root', password='root', host='localhost', port=3101, timeout=ssh_timeout)
r.upload_file(source_path, f'/root/{source_name}')


total_score = 0
testcases = []

# rubric

## exists

if exists:
	total_score += exists_max
else:
	fail_dict = {
		"score": 0,
		"output": "No file by the name 'pa1.s' can be found",
	}
	with open('/autograder/results/results.json', 'w') as fout:
		fout.write(json.dumps(fail_dict))
	exit(-1)
## compiles

compiles = ( r(f'gcc {source_name} -o {bin_name} 2>/dev/null; echo $?') == b'0')

if compiles:
	total_score += compiles_max
else:
	fail_dict = {
		"score": 10,
		"output": "Failed to compile",
	}
	with open('/autograder/results/results.json', 'w') as fout:
		fout.write(json.dumps(fail_dict))

## testcases

for testcaseidx in range(num_testcases):
	with open(f'./testcases/Input/{testcaseidx + 1}.in', 'r') as fin:
		tc_stdin = fin.read().rstrip()
	with open(f'./testcases/Output/{testcaseidx + 1}.out', 'rb') as fin:
		tc_stdout = fin.read().rstrip()

	student_stdout = r(f'echo {tc_stdin}\\n | ./{bin_name}')

	passed = ( tc_stdout == student_stdout )
	if passed:
		total_score += points_per_testcase

	testcase_dict = {
		"score": points_per_testcase if passed else 0,
		"max_score": points_per_testcase,
		"status": "passed" if passed else "failed",
		"name_format": "text",
		"output":f"User input:\n{tc_stdin}\n\nStudent output:\n{student_stdout}\n\nExpected output:\n{tc_stdout}\n",
		"output_format": "text",
		"visibility": "visible",
	}
	testcases.append(testcase_dict)

# gradescope results

student_score = {
	"score": total_score,
	"tests": testcases,
}


with open('/autograder/results/results.json', 'w') as fout:
	fout.write(json.dumps(student_score))
