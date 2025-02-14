#!/usr/bin/env python3

import json
from pwn import *
from os import listdir as os_listdir
import os.path
from datetime import datetime, timezone

context.log_level='error'

source_name = 'pa2.s'
compiles_max = 10
test_case_max = 50
exists_max = 10
recursive_max = 30

ssh_timeout = 600 # 10 minutes. (emulator needs to start first)

submission_filename = os_listdir('/autograder/submission/')[0] # we assume a file exists, as a student must submit a file for the program to run
source_path = f'/autograder/submission/{submission_filename}'
#source_path = f'/autograder/submission/pa2.txt'

with open(source_path, 'rb') as fin:
	source_code = fin.read()

num_testcases = len(os.listdir('./testcases/Input'))
points_per_testcase = test_case_max / num_testcases
bin_name = source_name[:-2]
exists = ( os.path.exists(source_path) and source_path.split('.')[-1] == 's')

r = ssh(user='root', password='root', host='localhost', port=3101, timeout=ssh_timeout)
r.upload_file(source_path, f'/root/{source_name}')
r.upload('testcases')


total_score = 0
testcases = []


## calculate late penalty
student_submission_time = datetime.now(timezone.utc)

# utc is 4 hours ahead of est
# that means deadline is 3:59
# 3 minutes of leeway for emulator to start
due_time = datetime(2025, 3, 1, 4, 2, 0, tzinfo=timezone.utc)

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
elif days_late <= 4:
    penalty = -40
elif days_late <= 5:
    penalty = -50
elif days_late <= 6:
    penalty = -60
else:
    penalty = -100

# rubric

## exists

if exists:
	total_score += exists_max
else:
	print('no submission')
	fail_dict = {
		"score": 0,
		"output": "No file with the '.s' extension found",
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
		"score": max(10 + penalty, 0),
		"output": "Failed to compile",
	}
	with open('/autograder/results/results.json', 'w') as fout:
		fout.write(json.dumps(fail_dict))
	exit(0)

## testcases

for testcaseidx in range(num_testcases):
	with open(f'./testcases/Input/{testcaseidx + 1}.in', 'r') as fin:
		tc_stdin = fin.read()
	r(f'stdbuf -oL ./{bin_name} <./testcases/Input/{testcaseidx + 1}.in >test-{testcaseidx + 1}.out')
	student_stdout = r.download_data(f'test-{testcaseidx + 1}.out')

	with open(f'./testcases/Output/{testcaseidx + 1}.out', 'rb') as fin:
		tc_stdout = fin.read().rstrip()

	#student_stdout = r(f'echo \'{tc_stdin}\' | ./{bin_name}')

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

# recursive testcase
'''
with open('./testcases/big.in', 'r') as fin:
	tc_stdin = fin.read().rstrip()

probably_recursive = ( r(f'echo \'{tc_stdin}\' | ./{bin_name} 2>dev/null; echo $?') == b'139' ) and (b'x28' in source_code or b'sp' in source_code)

if probably_recursive:
	total_score += recursive_max
else:
	print('probably not recursive')

testcase_dict = {
    "score": recursive_max if probably_recursive else 0,
    "max_score": recursive_max,
    "status": "passed" if passed else "failed",
    "name_format": "text",
    "output":"recursive" if probably_recursive else "not recursive",
    "output_format": "text",
    "visibility": "visible",
}
#testcases.append(testcase_dict)
'''
# gradescope results

student_score = {
	"score": max(total_score + penalty, 0),
	"tests": testcases,
}


with open('/autograder/results/results.json', 'w') as fout:
	fout.write(json.dumps(student_score))
