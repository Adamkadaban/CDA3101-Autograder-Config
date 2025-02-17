# CDA3101-Autograder-Config
Config to do autograding on qemu through gradescope

Read more about files on the [gradescope wiki](https://gradescope-autograders.readthedocs.io/en/latest/specs/)


### How to use

**1. Install Git LFS (Optional)**

- The ARM emulator files are stores in [/autograder/emulator](./autograder/emulator) via [Git LFS](https://git-lfs.com/)
    - If you would like to use these files, install the git plugin using the link above before cloning. 
    - If you'd like to provide your own emulator files, simply place them in the linked directory.

**2. Set up config.yml**

- Create a file in `/autograder/config.yml` according to the example below

```yaml
# Required
# This file extension is used to see if the file exists
source_name: pa1.s

# Required
# Max number of points for submitting code with the file extension defined above
exists_max: 10

# Required
# Max number of points for code compiling
compiles_max: 20

# Required
# Max number of points for passing testcases
# Points will be evenly divided between the testcases provided
test_case_max: 70

# Optional
# Max number of points for having code that is recursive
# For now, this is only for points and must be graded manually after the autograder runs.
recursive_max: 10
```
- Ensure that all point values given add up to 100, as the autograder will fail otherwise

**3. Set up testcases**

- All testcases should go in [/autograder/testcases/{Input,Output}](./autograder/testcases)
    - Files in `Input` should be labeled `1.in`, `2.in`, etc.
    - Files in `Output` should be labeled `1.out`, `2.out`, etc.

**4. Zip autograder**

- The following command can be run from the `autograder` directory to obtain `autograder.zip`, which will be uploaded to gradescope:

```bash
zip -r autograder.zip config.yml emulator fail.json grade.py requirements.txt run_autograder setup.sh testcases timeout.json
```

- If you would ever like to upload one file, you can do so with the following command to save time

```bash
# Only update the config.yml file
zip -u autograder.zip config.yml
```

- To quickly delete a file from the zip, use the following command

```bash
# Delete extra testcase
zip -d autograder.zip testcases/Input/10.in testcases/Output/10.out
```

**5 Upload to gradescope**

- Go to "Configure Autograder" for the assignment
    - Select "Zip file upload"
    - Upload the `autograder.zip` file from the previous step
- Go to "Settings" for the assignment
    - Set "Due Date" to the last time students can submit for full points
    - Set "Late Due Date" to the last time students can submit for any points
    - Set "Container Specifications" to "2.0 CPU, 3.0GB RAM"
        - This is required to ensure QEMU can run inside the container

### Features

- Can be used to test assembly or C code executing in a qemu emulator
- Configured easily via a `config.yml` file
- Secure from typical Gradescope attacks that allow students to edit grades
- Outputs of testcases are whitespace-agnostic
- Automatically deduct late points based on due date and late due date configured in gradescope

### Not implemented yet

- Automatic checking of if code is recursive
