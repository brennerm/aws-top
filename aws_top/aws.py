#!/usr/bin/env python3
import datetime as dt

import boto3


def get_user():
    return boto3.client('sts').get_caller_identity()["Arn"]


def get_region():
    return boto3._get_default_session().region_name


def set_region(region):
    boto3.setup_default_session(region_name=region)


class CloudWatch:
    def __init__(self, region):
        self.__cw_client = boto3.client('cloudwatch', region_name=region)

    def __get_metric_statistics(self, namespace, instance_id, metric_name):
        return self.__cw_client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            StartTime=dt.datetime.utcnow() - dt.timedelta(minutes=20),
            EndTime=dt.datetime.utcnow(),
            Period=60,
            Statistics=['Average'],
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                }
            ]
        )['Datapoints']

    def get_cpu_utilization(self, instance_id):
        return self.__get_metric_statistics(
            'AWS/EC2',
            instance_id,
            'CPUUtilization'
        )

    def get_status_check_status(self, instance_id):
        return self.__get_metric_statistics(
            'AWS/EC2',
            instance_id,
            'StatusCheckFailed'
        )

    def get_disk_bytes_read(self, instance_id):
        return self.__get_metric_statistics(
            'AWS/EC2',
            instance_id,
            'DiskReadBytes'
        )

    def get_disk_bytes_write(self, instance_id):
        return self.__get_metric_statistics(
            'AWS/EC2',
            instance_id,
            'DiskWriteBytes'
        )

    def get_network_bytes_in(self, instance_id):
        return self.__get_metric_statistics(
            'AWS/EC2',
            instance_id,
            'NetworkIn'
        )

    def get_network_bytes_out(self, instance_id):
        return self.__get_metric_statistics(
            'AWS/EC2',
            instance_id,
            'NetworkOut'
        )


class Ec2Instance:
    def __init__(self, identifier, state, instance_type, az, name=None):
        self.id = identifier
        self.state = state
        self.instance_type = instance_type
        self.az = az
        self.name = name


class Ec2:
    def __init__(self):
        self.__ec2_client = boto3.client('ec2')

    def get_all_instances(self):
        instances = []

        for instance in self.__ec2_client.describe_instances()['Reservations']:
            name = None
            instance = instance['Instances'][0]

            if 'Tags' in instance:
                for tag in instance['Tags']:
                    if tag['Key'] == 'Name':
                        name = tag['Value']

            identifier = instance['InstanceId']
            state = instance['State']['Name']
            instance_type = instance['InstanceType']
            az = instance['Placement']['AvailabilityZone']

            instances.append(
                Ec2Instance(identifier, state, instance_type, az, name)
            )

        return instances


class S3Bucket:
    def __init__(self):
        pass


class S3:
    def __init__(self):
        self.__s3_client = boto3.resource('s3')

    def get_all_buckets(self):
        buckets = list(self.__s3_client.buckets.all())

        return buckets
