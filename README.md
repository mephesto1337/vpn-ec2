# Quickly deploy an VPN on AWS EC2

As we interact with AWS, we need to be authenticated:
```bash
export AWS_ACCESS_KEY_ID=My_AWS_Access_Key
export AWS_SECRET_ACCESS_KEY=My_AWS_Secret_Key
```

## Prerequist
The following packages must be installed:
* easy-rsa
* python3
* python3 virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml
```

## Deploy the VM
Just run the [create-instance.py](./create-instance.py) script with the
appropriate options.
```bash
$ ./create-instance.py
[2022-02-08 15:30:10,057] create-instance - INFO - Instance i-0ef25a9959d0177cc deployed in us-east-1b
[2022-02-08 15:30:10,284] create-instance - INFO - Waiting for instance to be running
Instance i-0ef25a9959d0177cc created with DNS ec2-3-83-190-235.compute-1.amazonaws.com in us-east-1b
```

## Check our AWS inventory
```bash
$ ansible-inventory --graph
@all:
  |--@aws_ec2:
  |  |--ec2-3-83-190-235.compute-1.amazonaws.com
  |--@aws_region_us_east_1:
  |  |--ec2-3-83-190-235.compute-1.amazonaws.com
  |--@instance_type_t2_micro:
  |  |--ec2-3-83-190-235.compute-1.amazonaws.com
  |--@tag_openvpn_:
  |  |--ec2-3-83-190-235.compute-1.amazonaws.com
  |--@ungrouped:
  |--@vpn:
  |  |--ec2-3-83-190-235.compute-1.amazonaws.com
```

## Setup the VM
```bash
$ ansible-playbook -l ec2-3-83-190-235.compute-1.amazonaws.com playbooks/setup-vpn-server.yml
```

## Enjoy
The configuration file for the client is in the clients/ sub-directory
```bash
$ sudo openvpn clients/ec2-3-83-190-235.compute-1.amazonaws.com.conf
```
