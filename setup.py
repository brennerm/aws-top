from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='aws-top',
    version='0.1',
    packages=['aws_top'],
    install_requires=required,
    url='https://github.com/brennerm/aws-top',
    license='MIT',
    author='brennerm',
    author_email='xamrennerb@gmail.com',
    description='CLI Dashboard for AWS services'
)
