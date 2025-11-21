from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_efs as efs,
    aws_lambda as _lambda,
    aws_servicediscovery as servicediscovery,
    aws_s3 as s3,
)
from constructs import Construct


class ComputeStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        postgres_fs: efs.FileSystem,
        redis_fs: efs.FileSystem,
        upload_bucket: s3.Bucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. ECS Cluster with Service Discovery
        self.cluster = ecs.Cluster(
            self,
            "MoveHubCluster",
            vpc=vpc,
            container_insights=True,
            default_cloud_map_namespace=ecs.CloudMapNamespaceOptions(
                name="movehub.local",
                type=servicediscovery.NamespaceType.DNS_PRIVATE,
            ),
        )

        # 2. Postgres Service (Internal)
        postgres_task_def = ecs.FargateTaskDefinition(
            self,
            "PostgresTaskDef",
            cpu=512,
            memory_limit_mib=1024,
        )

        # Add EFS Volume
        postgres_task_def.add_volume(
            name="postgres_data",
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=postgres_fs.file_system_id,
            ),
        )

        postgres_container = postgres_task_def.add_container(
            "PostgresContainer",
            image=ecs.ContainerImage.from_registry("postgis/postgis:17-3.5"),
            logging=ecs.LogDriver.aws_logs(stream_prefix="postgres"),
            environment={
                "POSTGRES_USER": "movehub",
                "POSTGRES_PASSWORD": "movehub_dev_password",  # In prod use Secrets Manager
                "POSTGRES_DB": "movehub",
            },
            port_mappings=[ecs.PortMapping(container_port=5432)],
        )

        postgres_container.add_mount_points(
            ecs.MountPoint(
                container_path="/var/lib/postgresql/data",
                source_volume="postgres_data",
                read_only=False,
            )
        )

        self.postgres_service = ecs.FargateService(
            self,
            "PostgresService",
            cluster=self.cluster,
            task_definition=postgres_task_def,
            service_name="postgres",
            cloud_map_options=ecs.CloudMapOptions(
                name="postgres",
                dns_record_type=servicediscovery.DnsRecordType.A,
            ),
        )

        # Allow Postgres access from within VPC
        self.postgres_service.connections.allow_from(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.tcp(5432),
            "Allow Postgres access from VPC",
        )

        # Allow EFS access from Postgres Service
        postgres_fs.connections.allow_default_port_from(self.postgres_service)

        # 3. Redis Service (Internal)
        redis_task_def = ecs.FargateTaskDefinition(
            self,
            "RedisTaskDef",
            cpu=256,
            memory_limit_mib=512,
        )

        redis_task_def.add_volume(
            name="redis_data",
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=redis_fs.file_system_id,
            ),
        )

        redis_container = redis_task_def.add_container(
            "RedisContainer",
            image=ecs.ContainerImage.from_registry("redis:7.4.2-alpine"),
            logging=ecs.LogDriver.aws_logs(stream_prefix="redis"),
            command=["redis-server", "--appendonly", "yes"],
            port_mappings=[ecs.PortMapping(container_port=6379)],
        )

        redis_container.add_mount_points(
            ecs.MountPoint(
                container_path="/data",
                source_volume="redis_data",
                read_only=False,
            )
        )

        # 3. Lambda Functions
        # Cleanup Function
        self.cleanup_function = _lambda.Function(
            self,
            "CleanupFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=_lambda.Code.from_asset("src/cleanup"),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        )

        # Migrator Function (for DB initialization)
        self.migrator_function = _lambda.Function(
            self,
            "MigratorFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=_lambda.Code.from_asset("src/migrator"),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            environment={
                "DATABASE_URL": "postgresql+asyncpg://movehub:movehub_dev_password@postgres.movehub.local:5432/movehub",
            },
        )

        # Allow Migrator to access Postgres
        self.migrator_function.connections.allow_to(
            self.postgres_service,
            ec2.Port.tcp(5432),
            "Allow Migrator to access Postgres",
        )

        self.redis_service = ecs.FargateService(
            self,
            "RedisService",
            cluster=self.cluster,
            task_definition=redis_task_def,
            service_name="redis",
            cloud_map_options=ecs.CloudMapOptions(
                name="redis",
                dns_record_type=servicediscovery.DnsRecordType.A,
            ),
        )

        self.redis_service.connections.allow_from(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.tcp(6379),
            "Allow Redis access from VPC",
        )

        redis_fs.connections.allow_default_port_from(self.redis_service)

        # 4. API Service (Public ALB)
        self.api_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "ApiService",
            cluster=self.cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=2,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset(".."),  # Build from root Dockerfile
                container_port=8000,
                environment={
                    "ENVIRONMENT": "production",
                    "LOG_LEVEL": "INFO",
                    "DATABASE_URL": "postgresql+asyncpg://movehub:movehub_dev_password@postgres.movehub.local:5432/movehub",
                    "REDIS_URL": "redis://redis.movehub.local:6379/0",
                    "S3_BUCKET_NAME": upload_bucket.bucket_name,
                },
            ),
            public_load_balancer=True,
        )

        # Grant S3 access
        upload_bucket.grant_read_write(self.api_service.task_definition.task_role)

        # Configure Health Check
        self.api_service.target_group.configure_health_check(
            path="/health",
            port="8000",
        )

        # 5. Frontend Service (Public ALB)
        self.frontend_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FrontendService",
            cluster=self.cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=2,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset(
                    "../frontend",
                    build_args={
                        # NOTE: In a real production setup with a domain, you would put the domain here.
                        # Since the ALB DNS is not known at build time, we use a placeholder or localhost.
                        # For the browser to reach the API, this MUST be a public URL.
                        "NEXT_PUBLIC_API_URL": "http://localhost:8000"
                    },
                ),
                container_port=3000,
                environment={
                    "NODE_ENV": "production",
                    # We also pass it at runtime, though Next.js static optimization might ignore it.
                    "NEXT_PUBLIC_API_URL": f"http://{self.api_service.load_balancer.load_balancer_dns_name}",
                },
            ),
            public_load_balancer=True,
        )

        self.frontend_service.target_group.configure_health_check(
            path="/",
            port="3000",
        )
