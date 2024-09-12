#!/bin/bash

apt-get update -y

apt-get install -y qemu-system-arm python3 python3-pip

pip3 install -r /autograder/source/requirements.txt
