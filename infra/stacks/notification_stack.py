from aws_cdk import (
    Stack,
    aws_ses as ses,
    aws_sns as sns,
)
from constructs import Construct


class NotificationStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. SNS Topic for SMS Notifications
        self.sms_topic = sns.Topic(
            self,
            "SmsTopic",
            display_name="MoveHub SMS Notifications",
        )

        # 2. SES Email Identity
        # In a real scenario, you would verify a domain.
        # For now, we'll verify a single email address or just set up the identity.
        # Since we don't have a domain in Route53 in this stack, we'll use EmailIdentity.
        self.email_identity = ses.EmailIdentity(
            self,
            "EmailIdentity",
            identity=ses.Identity.email("notifications@movehub.com"),
        )
