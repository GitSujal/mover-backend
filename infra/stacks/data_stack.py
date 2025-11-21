from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_ec2 as ec2,
    aws_efs as efs,
    aws_s3 as s3,
)
from constructs import Construct


class DataStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. S3 Bucket for Uploads
        self.upload_bucket = s3.Bucket(
            self,
            "UploadBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.PUT, s3.HttpMethods.POST],
                    allowed_origins=["*"],  # Restrict this in production
                    allowed_headers=["*"],
                )
            ],
        )

        # 2. EFS for Postgres Data
        self.postgres_fs = efs.FileSystem(
            self,
            "PostgresFileSystem",
            vpc=vpc,
            encrypted=True,
            lifecycle_policy=efs.LifecyclePolicy.AFTER_14_DAYS,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            throughput_mode=efs.ThroughputMode.BURSTING,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # 3. EFS for Redis Data
        self.redis_fs = efs.FileSystem(
            self,
            "RedisFileSystem",
            vpc=vpc,
            encrypted=True,
            lifecycle_policy=efs.LifecyclePolicy.AFTER_14_DAYS,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            throughput_mode=efs.ThroughputMode.BURSTING,
            removal_policy=RemovalPolicy.RETAIN,
        )
