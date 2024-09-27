# CDA3101-Autograder-Config
Config to do autograding on qemu through gradescope


Read more about files on the [gradescope wiki](https://gradescope-autograders.readthedocs.io/en/latest/specs/)


### How to use

Add appropriate inputs (stdin) for the grading script in `./autograder/testcases/Input` and outputs (stdout) in `./autograder/testcases/Output`

- Testcases are currently whitepsace-agnostic
- Current timeout set to 60 seconds for all testcases
- Max retrys to grade set to 5
