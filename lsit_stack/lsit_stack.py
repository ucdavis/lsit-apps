from aws_cdk import Stack, RemovalPolicy
from constructs import Construct
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk.aws_elasticloadbalancing import LoadBalancer
from aws_cdk.aws_elasticloadbalancingv2 import ApplicationListener, ApplicationLoadBalancer, ApplicationProtocol, ApplicationTargetGroup, ListenerAction, ListenerCondition, TargetType, ApplicationListenerRule, ListenerCertificate
from aws_cdk.aws_logs import LogGroup
from aws_cdk.aws_s3 import Bucket
import aws_cdk.aws_cloudwatch as cloudwatch
import aws_cdk.aws_cloudwatch_actions as actions
import aws_cdk.aws_sns as sns

class LSITStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, bucket: Bucket, cluster: ecs.Cluster, load_balancer: LoadBalancer, app_props: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Required props
        app_name = app_props["app_name"]
        app_env = app_props["app_env"]
        image_uri = app_props["image_uri"]
        
        # Calculated props
        app_prefix = app_name.capitalize() + app_env.capitalize()
        task_name = "{app_name}-{app_env}".format(app_name=app_name, app_env=app_env)
        env_bucket_arn = bucket.bucket_arn

        # Optional
        host_headers = app_props.get("host_headers")
        task_port = app_props.get("task_port", 80)
        resource_multiplier = app_props.get("resource_multiplier", 1)
        is_private = app_props.get("is_private", False)
        command = app_props.get("command")
        public_facing = app_props.get("is_public_facing", True)
        auto_scaling = app_props.get("auto_scaling", False)
        git_repo = app_props.get("git_repo")

        if not cluster:    
            cluster_name = task_name
        else:
            cluster_name = cluster.cluster_name
        https_load_balancer_priority = app_props.get("https_load_balancer_priority", 1)
        http_load_balancer_priority = app_props.get("http_load_balancer_priority", 1)
        load_balancer_port = app_props.get("load_balancer_port")
        self.https_listener = app_props.get("https_listener")
        self.http_listener = app_props.get("http_listener")
        certificate_arns = app_props.get("certificate_arns")
        health_check_path = app_props.get("health_check_path","/health")
        additional_https_rule_priorities = app_props.get("additional_https_rule_priorities", [])
        additional_http_rule_priorities = app_props.get("additional_http_rule_priorities", [])
        monitoring_stack = app_props.get("monitoring_stack")

        role = iam.Role(
            self,
            "{app_prefix}Role".format(app_prefix=app_prefix),
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")],
            role_name="{app_prefix}ECSTaskExecutionRole".format(app_prefix=app_prefix),
            description="Allows {task_name} tasks to run in ECS and be able to read config files from the appropriate S3 bucket.".format(task_name=task_name)
        )

        policy = iam.Policy(
            self,
            "{app_prefix}Policy".format(app_prefix=app_prefix),
            force=True,
            policy_name="{app_prefix}ConfigRead".format(app_prefix=app_prefix),
            roles=[role]
        )

        policy.add_statements(
            iam.PolicyStatement(
                actions=["s3:GetBucketLocation"],
                resources=[env_bucket_arn]
            ),
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=["{bucket}/{app_name}/*".format(app_name=app_name,bucket=env_bucket_arn)]
            )
        )

        if git_repo:
            # Define the Federated Principal
            github_principal = iam.FederatedPrincipal(
                federated="arn:aws:iam::042277129213:oidc-provider/token.actions.githubusercontent.com",
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": "repo:ucdavis/{git_repo}:*".format(git_repo=git_repo)
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity"
            )

            # Create the Role
            github_role = iam.Role(
                self,
                "{app_prefix}GithubActionsRole".format(app_prefix=app_prefix),
                assumed_by=github_principal,
                role_name="{app_prefix}GithubActionsRole".format(app_prefix=app_prefix),
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name("EC2InstanceProfileForImageBuilderECRContainerBuilds"),iam.ManagedPolicy.from_aws_managed_policy_name("EC2InstanceProfileForImageBuilderECRContainerBuilds"),
                    iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy"),
                    iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeDeployRoleForECSLimited"),    
                ],
            )

            github_policy = iam.Policy(
                self,
                "{app_prefix}GithubPolicy".format(app_prefix=app_prefix),
                force=True,
                policy_name="{app_prefix}GithubPolicy".format(app_prefix=app_prefix),
                roles=[github_role]
            )

            github_policy.add_statements(
                iam.PolicyStatement(
                    actions=["s3:GetBucketLocation"],
                    resources=[env_bucket_arn]
                ),
                iam.PolicyStatement(
                    actions=["s3:GetObject"],
                    resources=["{bucket}/{app_name}/*".format(app_name=app_name,bucket=env_bucket_arn)]
                ),
                iam.PolicyStatement(
                    actions=["s3:GetBucketLocation"],
                    resources=[env_bucket_arn]
                ),    
                iam.PolicyStatement(
                    actions=["ecs:UpdateService"],
                    resources=["*"]
                ),               
            )

        task = ecs.FargateTaskDefinition(
            self,
            "{app_prefix}Task".format(app_prefix=app_prefix),
            cpu=256*resource_multiplier,
            memory_limit_mib=512*resource_multiplier,
            family=task_name,
            execution_role=role,
            task_role=role
        )

        image = ecs.ContainerImage.from_registry(image_uri)

        task.add_container(
            task_name,
            image=image,
            cpu=256*resource_multiplier,
            memory_limit_mib=512*resource_multiplier,
            port_mappings=[ecs.PortMapping(container_port=task_port,host_port=task_port)],
            logging=ecs.LogDriver.aws_logs(
                stream_prefix=task_name,
                log_group=LogGroup(
                    scope=self,
                    id="{app_prefix}LogGroup".format(app_prefix=app_prefix),
                    log_group_name="/ecs/{task_name}".format(task_name=task_name),
                    removal_policy=RemovalPolicy.DESTROY
            )),
            environment_files=[
                ecs.S3EnvironmentFile(
                    Bucket.from_bucket_arn(
                        self,
                        "{app_prefix}Bucket".format(app_prefix=app_prefix),
                        env_bucket_arn
                    ),
                    key="{app_name}/{environment}.env".format(app_name=app_name, environment=app_env)
                )
            ],
            container_name=task_name,
            command=command
        )


        # Security groups is mandatory for lookup, see https://github.com/aws/aws-cdk/issues/11146,
        # Security group for app is used as the sg for the cluster as a workaround to this "bug",
        # even though it is not associated to the cluster whatsoever
        security_group = ec2.SecurityGroup(
            self,
            "{app_prefix}SecurityGroup".format(app_prefix=app_prefix),
            allow_all_outbound=True,
            security_group_name=task_name,
            vpc=vpc
        )
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.all_traffic()
        )

        if not cluster:
            cluster = ecs.Cluster(
                self,
                "{app_prefix}Cluster".format(app_prefix=app_prefix),
                vpc=vpc
            )
        desired_count = 1
        if auto_scaling:
            desired_count = 2
        if is_private:
            service = ecs.FargateService(
                self,
                "{app_prefix}Service".format(app_prefix=app_prefix),
                security_groups=[security_group],
                vpc_subnets=ec2.SubnetSelection(
                    subnets=vpc.private_subnets
                ),
                desired_count=desired_count,
                task_definition=task,
                cluster=cluster,
                service_name=task_name
            )
        else:
            service = ecs.FargateService(
                self,
                "{app_prefix}Service".format(app_prefix=app_prefix),
                assign_public_ip=True,
                security_groups=[security_group],
                vpc_subnets=ec2.SubnetSelection(
                    subnets=vpc.public_subnets
                ),
                desired_count=desired_count,
                task_definition=task,
                cluster=cluster,
                service_name=task_name
            )
        if auto_scaling:
            scaling = service.auto_scale_task_count(
                max_capacity=8,
                min_capacity=2
            )
            scaling.scale_on_cpu_utilization(
                "{app_prefix}CPUScaling".format(app_prefix=app_prefix),
                target_utilization_percent=50
            )

        # Setup alarms on service
        cpu_alarm = cloudwatch.Alarm(
            self, 
            "{app_prefix}CPUAlarm".format(app_prefix=app_prefix),
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            threshold=75,
            evaluation_periods=1,
            metric=service.metric_cpu_utilization(),
            alarm_name="{app_prefix}CPUAlarm".format(app_prefix=app_prefix),
            actions_enabled=True
        )

        if monitoring_stack:
            cpu_alarm.add_alarm_action(actions.SnsAction(topic=monitoring_stack.ecs_alerts_topic))

        if public_facing:

            if not load_balancer:
                load_balancer = ApplicationLoadBalancer(
                    self,
                    "{app_prefix}LoadBalancer".format(app_prefix=app_prefix),
                    vpc=vpc,
                    security_group=security_group,
                    internet_facing=True
                )

            target_group = ApplicationTargetGroup(
                self,
                "{app_prefix}TargetGroup".format(app_prefix=app_prefix),
                target_type=TargetType.IP,
                target_group_name='ecs-{task_name}-{app_env}'.format(task_name=task_name, app_env=app_env)[:32],
                protocol=ApplicationProtocol.HTTP,
                port=80,
                vpc=vpc
            )
            target_group.configure_health_check(
                path=health_check_path
            )

            service.attach_to_application_target_group(target_group)
            target_group.load_balancer_attached
    
            if host_headers:
                if not self.https_listener:
                    fixed_response_json = {
                        "fixedResponseConfig" : {
                            "contentType": "text/plain",
                            "statusCode" : "503"
                        },
                        "type" : "fixed-response"
                    }
                    self.https_listener = ApplicationListener(
                        self,
                        "{app_prefix}HttpsListener".format(app_prefix=app_prefix),
                        load_balancer=load_balancer,
                        port=443,
                        default_action=ListenerAction(fixed_response_json),
                    )
                    
                if certificate_arns:
                    certificates = []
                    for certificate_arn in certificate_arns:
                        certificates.append(
                            ListenerCertificate(
                                certificate_arn
                            )
                        )

                    self.https_listener.add_certificates(
                        "{app_prefix}Certtificates".format(app_prefix=app_prefix),
                        certificates
                    )    

                ApplicationListenerRule(
                    self,
                    "{app_prefix}HttpsListenerRule".format(app_prefix=app_prefix),
                    listener=self.https_listener,
                    conditions=[ListenerCondition.host_headers(host_headers[0:5])],
                    priority=https_load_balancer_priority,
                    target_groups=[target_group]
                )

                # HTTP listener
                if not self.http_listener:
                    fixed_response_json = {
                        "fixedResponseConfig" : {
                            "contentType": "text/plain",
                            "statusCode" : "503"
                        },
                        "type" : "fixed-response"
                    }

                    self.http_listener = ApplicationListener(
                        self,
                        "{app_prefix}HttpListener".format(app_prefix=app_prefix),
                        load_balancer=load_balancer,
                        port=80,
                        default_action=ListenerAction(fixed_response_json),
                    )

                listener_action_json = {
                    "redirectConfig" : {
                        "port" : "443",
                        "statusCode" : "HTTP_301",
                        "protocol": "HTTPS"
                    },
                    "type" : "redirect"
                }

                ApplicationListenerRule(
                    self,
                    "{app_prefix}HttpListenerRule".format(app_prefix=app_prefix),
                    listener=self.http_listener,
                    conditions=[ListenerCondition.host_headers(host_headers[0:5])],
                    priority=http_load_balancer_priority,
                    action=ListenerAction(listener_action_json)
                )

                while len(host_headers) > 5 and ( len(additional_https_rule_priorities) > 0 or len(additional_http_rule_priorities) > 0):
                    host_headers = host_headers[5:]
                    if len(additional_https_rule_priorities) > 0:
                        ApplicationListenerRule(
                            self,
                            "{app_prefix}HttpsListenerRule{rule_number}".format(app_prefix=app_prefix,rule_number=additional_https_rule_priorities[0]),
                            listener=self.https_listener,
                            conditions=[ListenerCondition.host_headers(host_headers[:5])],
                            priority=additional_https_rule_priorities[0],
                            target_groups=[target_group]
                        )
                        additional_https_rule_priorities = additional_https_rule_priorities[1:]

                    if len(additional_http_rule_priorities) > 0:
                        ApplicationListenerRule(
                            self,
                            "{app_prefix}HttpListenerRule{rule_number}".format(app_prefix=app_prefix,rule_number=additional_http_rule_priorities[0]),
                            listener=self.http_listener,
                            conditions=[ListenerCondition.host_headers(host_headers[:5])],
                            priority=additional_http_rule_priorities[0],
                            action=ListenerAction(listener_action_json)
                        )
                        additional_http_rule_priorities = additional_http_rule_priorities[1:]

            if load_balancer_port:
                additional_listener = ApplicationListener(
                    self,
                    "{app_prefix}Listener".format(app_prefix=app_prefix),
                    load_balancer=load_balancer,
                    default_target_groups=[target_group],
                    port=load_balancer_port,
                    protocol=ApplicationProtocol.HTTP,
                    open=True
                )
