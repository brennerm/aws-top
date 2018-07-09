#!/usr/bin/env python3
import datetime
import datetime as dt

import boto3


def get_user():
    return boto3.client('sts').get_caller_identity()["Arn"]


def get_region():
    return boto3._get_default_session().region_name


def set_region(region):
    boto3.setup_default_session(region_name=region)


def set_credentials(aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None):
    boto3.setup_default_session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token
    )


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

    @staticmethod
    def from_dict(dict_content):
        name = None

        if 'Tags' in dict_content:
            for tag in dict_content['Tags']:
                if tag['Key'] == 'Name':
                    name = tag['Value']

        return Ec2Instance(
            dict_content['InstanceId'],
            dict_content['State']['Name'],
            dict_content['InstanceType'],
            dict_content['Placement']['AvailabilityZone'],
            name
        )


class Ec2:
    def __init__(self):
        self.__ec2_client = boto3.client('ec2')

    def get_all_instances(self):
        instances = []

        for instance in self.__ec2_client.describe_instances()['Reservations']:
            instances.append(
                Ec2Instance.from_dict(
                    instance['Instances'][0]
                )
            )

        return instances


class S3:
    def __init__(self):
        self.__s3_client = boto3.resource('s3')

    def get_all_buckets(self):
        buckets = list(self.__s3_client.buckets.all())

        return buckets


class LambdaFunction:
    def __init__(self, name, runtime, code_size, memory_size, timeout, last_modified):
        self.name = name
        self.runtime = runtime
        self.code_size = code_size
        self.memory_size = memory_size
        self.timeout = timeout
        self.last_modified = last_modified

    @staticmethod
    def from_dict(dict_content):
        last_modified = dict_content['LastModified']
        last_modified = datetime.datetime.strptime(
            last_modified,
            '%Y-%m-%dT%H:%M:%S.%f%z'
        )

        return LambdaFunction(
            dict_content['FunctionName'],
            dict_content['Runtime'],
            str(dict_content['CodeSize']),
            str(dict_content['MemorySize']),
            str(dict_content['Timeout']),
            last_modified.strftime("%Y-%m-%d %H:%M:%S")
        )


class Lambda:
    def __init__(self):
        self.__lambda_client = boto3.client('lambda')

    def get_all_functions(self):
        return [
            LambdaFunction.from_dict(func) for func in self.__lambda_client.list_functions()['Functions']
        ]
