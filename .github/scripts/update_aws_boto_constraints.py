#!/usr/bin/env python3

from pathlib import PosixPath
import re
import logging
import os
from functools import partial


FORMAT = '[%(asctime)s] - %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('update_aws_user_agent')
logger.setLevel(logging.DEBUG)

MIN_BOTOCORE_RE = re.compile(r"MINIMUM_BOTOCORE_VERSION( *)=( *)[\"|'][0-9\.]+[\"|']")
MIN_BOTO3_RE = re.compile(r"MINIMUM_BOTO3_VERSION( *)=( *)[\"|'][0-9\.]+[\"|']")


def replace_vars(values, line):
    res = None
    for var, value in values.items():
        m = re.match(r"^%s([ =\"']*)[0-9\.]+(.*)" % var, line)
        if m:
            res = var + m.group(1) + value + m.group(2)
            break
    return line if res is None else res


def update_single_file(path, values):
    with open(path) as fd:
        content = fd.read().split("\n")
    new_content = list(map(partial(replace_vars, values), content))
    if new_content != content:
        with open(path, "w") as fw:
            fw.write("\n".join(new_content))
        logger.info("%s => updated" % path)


def update_tests_constraints(boto3_version, botocore_version):
    boto_values = dict(boto3=boto3_version, botocore=botocore_version)
    for file in ("tests/unit/constraints.txt", "tests/integration/constraints.txt"):
        update_single_file(file, boto_values)

    min_boto_values = dict(MINIMUM_BOTO3_VERSION=boto3_version, MINIMUM_BOTOCORE_VERSION=botocore_version)
    for root, _, files in os.walk("plugins"):
        for name in files:
            if not name.endswith(".py"):
                continue
            update_single_file(os.path.join(root, name), min_boto_values)


def read_boto_version():

    BOTOCORE_RE = re.compile(r"^botocore[>=<]+([0-9\.]+)", re.MULTILINE | re.IGNORECASE)
    BOTO3_RE = re.compile(r"^boto3[>=<]+([0-9\.]+)", re.MULTILINE | re.IGNORECASE)
    
    with PosixPath("requirements.txt").open() as fd:
        content = fd.read()
        m_boto3 = BOTO3_RE.search(content)
        m_botocore = BOTOCORE_RE.search(content)
        return m_boto3.group(1) if m_boto3 else None, m_botocore.group(1) if m_botocore else None


def main():
    boto3_version, botocore_version = read_boto_version()
    logger.info("boto3: %s - botocore: %s" % (boto3_version, botocore_version))
    update_tests_constraints(boto3_version, botocore_version)


if __name__ == "__main__":

    main()