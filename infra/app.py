#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.compute_stack import ComputeStack
from stacks.data_stack import DataStack
from stacks.network_stack import NetworkStack
from stacks.notification_stack import NotificationStack

app = cdk.App()

# Environment configuration
env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION"),
)

app_name = "MoveHub"

# 1. Network Stack (VPC)
network_stack = NetworkStack(
    app,
    f"{app_name}-Network",
    env=env,
)

# 2. Data Stack (EFS, S3)
data_stack = DataStack(
    app,
    f"{app_name}-Data",
    vpc=network_stack.vpc,
    env=env,
)

# 3. Notification Stack (SES, SNS)
notification_stack = NotificationStack(
    app,
    f"{app_name}-Notifications",
    env=env,
)

# 4. Compute Stack (ECS Services)
compute_stack = ComputeStack(
    app,
    f"{app_name}-Compute",
    vpc=network_stack.vpc,
    postgres_fs=data_stack.postgres_fs,
    redis_fs=data_stack.redis_fs,
    upload_bucket=data_stack.upload_bucket,
    env=env,
)

# Add dependencies
data_stack.add_dependency(network_stack)
compute_stack.add_dependency(data_stack)
compute_stack.add_dependency(notification_stack)

app.synth()
