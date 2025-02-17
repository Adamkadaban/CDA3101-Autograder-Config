#!/usr/bin/env python3

import json
from pwn import *
from os import listdir as os_listdir
import os.path
from datetime import datetime
import math
import yaml

with open('config.yml') as fin:
	config_data = yaml.safe_load(fin)

fail_dict = {
	"score": 0,
	"output": "Autograder configuration error. Please contact staff.",
	"output_format": "text"
}

try:
	source_name = config_data['source_name']
	exists_max = float(config_data['exists_max'])
	compiles_max = float(config_data['compiles_max'])
	test_case_max = float(config_data['test_case_max'])
except KeyError as e:
	print(str(e))
	print('Missing one of the required fields in config.yml')
	with open('/autograder/results/results.json', 'w') as fout:
		fout.write(json.dumps(fail_dict))
	exit(0)
except ValueError as e:
	print(str(e))
	print('Unable to parse one or more *_max values')
	with open('/autograder/results/results.json', 'w') as fout:
		fout.write(json.dumps(fail_dict))
	exit(0)

recursive_max = float(config_data['recursive_max']) if 'recursive_max' in config_data else None

max_points = recursive_max or 0
max_points += exists_max + compiles_max + test_case_max

try:
	assert(max_points == 100)
except AssertionError:
	print('More or less than 100 points allocated to autograder')
	with open('/autograder/results/results.json', 'w') as fout:
		fout.write(json.dumps(fail_dict))
	exit(0)


file_extension_required = source_name.split('.')[-1]

context.log_level='error'

ssh_timeout = 600 # 10 minutes. (emulator needs to start first)

submission_filename = os_listdir('/autograder/submission/')[0] # we assume a file exists, as a student must submit a file for the program to run
source_path = f'/autograder/submission/{submission_filename}'

with open(source_path, 'rb') as fin:
	source_code = fin.read()

num_testcases = len(os.listdir('./testcases/Input'))
points_per_testcase = test_case_max / num_testcases
bin_name = source_name[:-2]
exists = ( os.path.exists(source_path) and source_path.split('.')[-1] == file_extension_required)

r = ssh(user='root', password='root', host='localhost', port=3101, timeout=ssh_timeout)
r.upload_file(source_path, f'/root/{source_name}')
r.upload('testcases')


total_score = 0
testcases = []


## calculate late penalty
with open('/autograder/submission_metadata.json') as fin:
	submission_metadata = json.loads(fin.read())

student_submission_time = datetime.fromisoformat(submission_metadata['created_at'])
due_time = datetime.fromisoformat(submission_metadata['assignment']['due_date'])
late_due_time = datetime.fromisoformat(submission_metadata['assignment']['late_due_date'])

days_late = ( (student_submission_time - due_time).total_seconds() / (60 * 60 * 24) )
print(f'DAYS LATE: {days_late}')

# -10 points per full or partial day late
# -100 points if submitting past late date
penalty = min(-10 * math.ceil(days_late), 0)
if student_submission_time > late_due_time:
	penalty = -100

# rubric

## exists

if exists:
	total_score += exists_max
else:
	print('no submission')
	fail_dict = {
		"score": 0,
		"output": f"No file with the `{file_extension_required}` extension found",
		"output_format": "md"
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
if recursive_max:
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
	testcases.append(testcase_dict)



# gradescope results

student_score = {
	"score": max(total_score + penalty, 0),
	"tests": testcases,
}


with open('/autograder/results/results.json', 'w') as fout:
	fout.write(json.dumps(student_score))
