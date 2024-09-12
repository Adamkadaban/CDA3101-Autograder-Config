#!/bin/bash

NCPU=2
MEM=1G

qemu-system-aarch64 -smp ${NCPU} -m ${MEM} -M virt -cpu cortex-a57  \
                    -initrd ../initrd.img-4.9.0-4-arm64 \
                    -kernel ../vmlinuz-4.9.0-4-arm64 -append "root=/dev/sda2 console=ttyAMA0" \
                    -global virtio-blk-device.scsi=off \
                    -device virtio-scsi-device,id=scsi \
                    -drive file=../disk.qcow2,id=rootimg,cache=unsafe,if=none \
                    -device scsi-hd,drive=rootimg \
                    -device e1000,netdev=net0 \
                    -netdev user,id=net0,hostfwd=tcp::3101-:22 \
                    -nic user,model=virtio-net-pci \
					-daemonize \
					-display none
