#!/usr/bin/env python3

import json
from pwn import *
from os import listdir as os_listdir
import os.path
from datetime import datetime, timezone

student_submission_time = datetime.now(timezone.utc)

context.log_level='debug'

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
exists = ( os.path.exists(source_path) and source_path.split('.')[-1] == 's' )

r = ssh(user='root', password='root', host='localhost', port=3101, timeout=ssh_timeout)
r.upload_file(source_path, f'/root/{source_name}')


total_score = 0
testcases = []

# rubric

## exists

if exists:
	total_score += exists_max
else:
	print('no submission')
	fail_dict = {
		"score": 0,
		"output": "No file with the `.s' extension found",
	}
	with open('/autograder/results/results.json', 'w') as fout:
		fout.write(json.dumps(fail_dict))
	exit(0)
## compiles

compiles = ( r(f'gcc {source_name} -o {bin_name} 2>/dev/null; echo $?') == b'0')

if compiles:
	total_score += compiles_max
else:
	print('failed to compile')
	fail_dict = {
		"score": 10,
		"output": "Failed to compile",
	}
	with open('/autograder/results/results.json', 'w') as fout:
		fout.write(json.dumps(fail_dict))
	exit(0)

## testcases

for testcaseidx in range(num_testcases):
	with open(f'./testcases/Input/{testcaseidx + 1}.in', 'r') as fin:
		tc_stdin = fin.read().rstrip()
	with open(f'./testcases/Output/{testcaseidx + 1}.out', 'rb') as fin:
		tc_stdout = fin.read().rstrip()

	student_stdout = r(f'echo \'{tc_stdin}\' | ./{bin_name}')

	passed = ( [i for i in student_stdout if i not in b' \n\t\r'] == [i for i in tc_stdout if i not in b' \n\t\r'] )
	if passed:
		total_score += points_per_testcase

	testcase_dict = {
		"score": points_per_testcase if passed else 0,
		"max_score": points_per_testcase,
		"status": "passed" if passed else "failed",
		"name_format": "text",
		"output":f"User input:\n{tc_stdin}\n\nStudent output:\n{student_stdout.decode()}\n\nExpected output:\n{tc_stdout.decode()}\n",
		"output_format": "text",
		"visibility": "visible",
	}
	testcases.append(testcase_dict)

# gradescope results

## calculate late penalty

# utc is 4 hours ahead of est
# that means deadline is 3:59
# 3 minutes of leeway for emulator to start
due_time = datetime(2024, 10, 1, 4, 2, 0, tzinfo=timezone.utc)

days_late = ( (student_submission_time - due_time).total_seconds() / (60 * 60 * 24) )
print(f'DAYS LATE: {days_late}')


if days_late <= 0:
    penalty = 0
elif days_late <= 1:
    penalty = -10
elif days_late <= 2:
    penalty = -20
elif days_late <= 3:
    penalty = -30
else:
    penalty = -100

total_score += penalty

student_score = {
	"score": max(total_score, 0),
	"tests": testcases,
}


with open('/autograder/results/results.json', 'w') as fout:
	fout.write(json.dumps(student_score))
