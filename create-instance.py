#! /usr/bin/env python3

import argparse
import json
import logging
import os
import sys
import time

from typing import Any, Dict

import boto3
import yaml

logging.basicConfig(
    stream=sys.stderr,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, os.environ.get('LOG_LEVEL', 'INFO').upper())
)
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])

AMI_IMAGE_ID = 'ami-0a8b4cd432b1c3063'


def main():
    def parse_args():
        def load_extra_arguments(filename: str) -> Dict[str, Any]:
            """
            Tries to load file
            """
            loaders = {
                'json': (json.load, json.JSONDecodeError),
                'yaml': (lambda f: yaml.load(f, yaml.SafeLoader), yaml.error.YAMLError)
            }
            for name, loader_exception in loaders.items():
                loader, exception_class = loader_exception
                with open(filename, 'rt') as f:
                    try:
                        logger.debug('Trying %s file format', name)
                        return loader(f)
                    except exception_class:
                        pass

            raise ValueError('Bad file format')

        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        creds = parser.add_argument_group('Credentials')
        creds.add_argument(
            '--aws-access-key-id', dest='aws_access_key_id', default=os.getenv('AWS_ACCESS_KEY_ID'),
            help='AWS Access key ID'
        )
        creds.add_argument(
            '--aws-secret-access-key', dest='aws_secret_access_key',
            default=os.getenv('AWS_SECRET_ACCESS_KEY'), help='AWS Secret Access key'
        )

        instance = parser.add_argument_group('Instance')
        instance.add_argument(
            '-r', '--region', dest='region', default='us-east-1', help='AWS region name'
        )
        instance.add_argument(
            '-t', '--instance-type', dest='instance_type', default='t2.micro',
            help='AWS Instance type'
        )
        instance.add_argument(
            '-e', '--extra-args', dest='extra_args', default={}, metavar='FILE',
            type=load_extra_arguments,
            help='Extra arguments to pass `create_instances`. File must be in YAML or JSON format'
        )

        args = parser.parse_args()
        return args

    args = parse_args()
    logger.debug('args = %r', args)
    try:
        session = boto3.Session(
            aws_access_key_id=args.aws_access_key_id,
            aws_secret_access_key=args.aws_secret_access_key
        )
        available_regions = session.get_available_regions('ec2')
        if args.region not in available_regions:
            logger.error('Invalid region name %r', args.region)
            print('Available regions: {}'.format(', '.join(available_regions)))
            return 1

        ec2 = session.resource('ec2', args.region)
        keypairs = list(ec2.key_pairs.all())

        instances = ec2.create_instances(
            ImageId=AMI_IMAGE_ID, InstanceType=args.instance_type,
            MaxCount=1, MinCount=1, KeyName=keypairs[0].name,
            **args.extra_args
        )
        instance = instances[0]
        logger.info('Instance {} deployed in {}'.format(
            instance.id, instance.placement['AvailabilityZone']
        ))
        instance.create_tags(Tags=[dict(Key='openvpn', Value='')])
        logger.info('Waiting for instance to be running')
        instance.wait_until_running()
        instance.reload()

        print('Instance {} created with DNS {} in {}'.format(
            instance.id, instance.public_dns_name, instance.placement['AvailabilityZone']
        ))
    except Exception as e:
        te = type(e)
        show_bt = logger.getEffectiveLevel() <= logging.DEBUG
        logger.error(
            'Caught exception %s.%s: %s',
            te.__module__, te.__name__, str(e), exc_info=show_bt
        )
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main())
