import os

from aws_cdk import App, Environment

from lsit_stack.lsit_stack import LSITStack
from network_stack.network_stack import NetworkStack
from queue_stack.queue_stack import QueueStack
from scheduled_task_stack.scheduled_task_stack import ScheudledTaskStack    
from monitoring_stack.monitoring_stack import MonitoringStack
from getvfd_stack.getvfd_stack import GetVFDStack
from queue_stack.queue_stack import QueueStack
from voip_stack.voip_stack import VOIPStack


CDK_DEFAULT_ACCOUNT=os.environ["CDK_DEFAULT_ACCOUNT"]
CDK_DEFAULT_REGION=os.environ["CDK_DEFAULT_REGION"]

app = App()

network_stack = NetworkStack(
    app,
    "NetworkStack",
    {
        "prefix": "LSITZoomQueue",
        "app_name": "frontdesk",
        "aws_bucket_name": "lsit-zoom-queue-env-vars",
        "need_dev": True,
        "is_legacy": True,
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

# Monitoring
monitoring_stack = MonitoringStack(
    app,
    "ECSMonitoringStack",
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

# Development
dev_frontdesk_frontend_stack = LSITStack(
    app,
    "ZoomQueueFrontendDevelopmentStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.development_cluster,
    network_stack.development_load_balancer,
    {
        "app_name": "zoom-queue-frontend",
        "app_env": "development",
        "task_port": 3000,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/zoom-queue-frontend-development:latest",
        "load_balancer_port": 3000,
        "health_check_path": "/api/health",
        "https_load_balancer_priority": 1,
        "http_load_balancer_priority": 1,
        "host_headers": ["dev.advisingfrontdesk.lsit.ucdavis.edu"],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/d18674bd-6a83-41aa-b10f-e379c2f8a1fa"]
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

LSITStack(
    app,
    "ZoomQueueBackendDevelopmentStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.development_cluster,
    network_stack.development_load_balancer,
    {
        "app_name": "zoom-queue-backend",
        "app_env": "development",
        "task_port": 3001,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/zoom-queue-backend-dev:latest",
        "load_balancer_port": 3001,
        "https_listener": dev_frontdesk_frontend_stack.https_listener,
        "http_listener": dev_frontdesk_frontend_stack.http_listener,
        "https_load_balancer_priority": 2,
        "http_load_balancer_priority": 2,
        "host_headers": ["dev.api.frontdesk.lsit.ucdavis.edu"],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/2e50e559-3efd-444e-8937-8feadec6003b"]
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

LSITStack(
    app,
    "ZoomQueueWebsocketDevelopmentStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.development_cluster,
    network_stack.development_load_balancer,
    {
        "app_name": "zoom-queue-websocket",
        "app_env": "development",
        "task_port": 80,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/zoom-queue-websocket-dev:latest",
        "load_balancer_port": 8080,
        "https_listener": dev_frontdesk_frontend_stack.https_listener,
        "http_listener": dev_frontdesk_frontend_stack.http_listener,
        "https_load_balancer_priority": 3,
        "http_load_balancer_priority": 3,
        "host_headers": ["dev.websocket.frontdesk.lsit.ucdavis.edu"],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/697571d7-e696-4c3c-9c42-d47f538fea7a"]
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "ZoomQueueDevelopmentCleanupCron",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.development_cluster,
    {
        "app_name": "zoom-queue-cleanup-cron",
        "app_env": "development",
        "image_uri": "curlimages/curl:latest",
        "command_override": ["sh","-c","curl -XDELETE https://dev.api.frontdesk.lsit.ucdavis.edu/api/guest?key=$API_KEY"]
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "ZoomQueueDevelopmentCleanupAnnouncements",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.development_cluster,
    {
        "app_name": "zoom-queue-cleanup-announcements",
        "app_env": "development",
        "image_uri": "curlimages/curl:latest",
        "command_override": ["sh","-c",'curl -XDELETE "https://dev.api.frontdesk.lsit.ucdavis.edu/api/announcement?key=$API_KEY&domain=$DOMAIN"']
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)


# Prod
frontdesk_frontend_stack = LSITStack(
    app,
    "FrontDeskAppClientProdStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    network_stack.load_balancer,
    {
        "app_name": "frontdesk-app-client",
        "app_env": "production",
        "task_port": 3000,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/frontdesk-app-client-prod:latest",
        "health_check_path": "/api/health",
        "https_load_balancer_priority": 1,
        "http_load_balancer_priority": 1,
        "host_headers": [
            "advisingfrontdesk.lsit.ucdavis.edu",
            "uea.advisingfrontdesk.lsit.ucdavis.edu",
            "lsit.advisingfrontdesk.lsit.ucdavis.edu",
            "grad.advisingfrontdesk.lsit.ucdavis.edu",
            "physics.advisingfrontdesk.lsit.ucdavis.edu",
            "eps.advisingfrontdesk.lsit.ucdavis.edu",
            "yellowcluster.advisingfrontdesk.lsit.ucdavis.edu",
            "ehe.advisingfrontdesk.lsit.ucdavis.edu",
            "langlit.advisingfrontdesk.lsit.ucdavis.edu",
            "antsocmsa.advisingfrontdesk.lsit.ucdavis.edu",
            "caes.advisingfrontdesk.lsit.ucdavis.edu",
            "cs.advisingfrontdesk.lsit.ucdavis.edu",
            "mae.advisingfrontdesk.lsit.ucdavis.edu",
            "orangecluster.advisingfrontdesk.lsit.ucdavis.edu",
            "cee.advisingfrontdesk.lsit.ucdavis.edu",
            "communication.advisingfrontdesk.lsit.ucdavis.edu",
            "intrel.advisingfrontdesk.lsit.ucdavis.edu",
            "linguistics.advisingfrontdesk.lsit.ucdavis.edu",
            "polisci.advisingfrontdesk.lsit.ucdavis.edu",
            "engineering.advisingfrontdesk.lsit.ucdavis.edu",
            "acbnc.advisingfrontdesk.lsit.ucdavis.edu",
            "oeoes.advisingfrontdesk.lsit.ucdavis.edu",
            "lgbtqia.advisingfrontdesk.lsit.ucdavis.edu",
            "menasa.advisingfrontdesk.lsit.ucdavis.edu",
            "our.advisingfrontdesk.lsit.ucdavis.edu",
            "english.advisingfrontdesk.lsit.ucdavis.edu",
            "fas.advisingfrontdesk.lsit.ucdavis.edu",
            "stat.advisingfrontdesk.lsit.ucdavis.edu",
            #"amha.advisingfrontdesk.lsit.ucdavis.edu",
            "bae.advisingfrontdesk.lsit.ucdavis.edu",
            "gsm.advisingfrontdesk.lsit.ucdavis.edu",
            "ece.advisingfrontdesk.lsit.ucdavis.edu",
            "bme.advisingfrontdesk.lsit.ucdavis.edu",
            "chms.advisingfrontdesk.lsit.ucdavis.edu",
            "chi.advisingfrontdesk.lsit.ucdavis.edu",
            "chistudies.advisingfrontdesk.lsit.ucdavis.edu",
            "lspeercoaching.advisingfrontdesk.lsit.ucdavis.edu",
            "ses.advisingfrontdesk.lsit.ucdavis.edu",
            "registrar.advisingfrontdesk.lsit.ucdavis.edu",
            "bao.advisingfrontdesk.lsit.ucdavis.edu",
            "ggcs.advisingfrontdesk.lsit.ucdavis.edu",
            "asac.advisingfrontdesk.lsit.ucdavis.edu",
            "esp.advisingfrontdesk.lsit.ucdavis.edu",
            "careercenter.advisingfrontdesk.lsit.ucdavis.edu",
        ],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/a238e17f-4f2d-4b26-b157-9733e72d5f95", "arn:aws:acm:us-west-2:042277129213:certificate/6da950e7-0463-406d-b80f-077d5f20226b"],
        "is_private": True,
        "additional_https_rule_priorities": [9,10,11,14,15,16,17,19],
        "additional_http_rule_priorities": [9,10,11,14,15,16,17,19],
        "resource_multiplier": 16,
        "monitoring_stack": monitoring_stack
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

LSITStack(
    app,
    "FrontDeskAppServerProdStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    network_stack.load_balancer,
    {
        "app_name": "frontdesk-app-server",
        "app_env": "production",
        "task_port": 3001,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/frontdesk-app-server-prod:latest",
        "https_listener": frontdesk_frontend_stack.https_listener,
        "http_listener": frontdesk_frontend_stack.http_listener,
        "https_load_balancer_priority": 2,
        "http_load_balancer_priority": 2,
        "host_headers": ["api.frontdesk.lsit.ucdavis.edu"],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/affa98c2-77b9-4942-95c6-350d25193a60"],
        "is_private": True,
        "resource_multiplier": 8,
        "monitoring_stack": monitoring_stack
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

LSITStack(
    app,
    "FrontDeskAppWebsocketProdStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    network_stack.load_balancer,
    {
        "app_name": "frontdesk-app-websocket",
        "app_env": "production",
        "task_port": 80,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/frontdesk-app-websocket-prod:latest",
        "https_listener": frontdesk_frontend_stack.https_listener,
        "http_listener": frontdesk_frontend_stack.http_listener,
        "https_load_balancer_priority": 3,
        "http_load_balancer_priority": 3,
        "host_headers": ["websocket.frontdesk.lsit.ucdavis.edu"],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/8bdad38f-d7e5-4b46-9d46-a79bb5c9ccd4"],
        "is_private": True,
        "resource_multiplier": 2,
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "FrontDeskAppProdCleanupGuests",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "frontdesk-app-cleanup-guests",
        "app_env": "production",
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/curl:latest",
        "command_override": ["sh","-c","curl -XDELETE https://api.frontdesk.lsit.ucdavis.edu/api/guest?key=$API_KEY"],
        "is_private": True
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "FrontDeskAppProdCleanupAnnouncements",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "frontdesk-app-cleanup-announcements",
        "app_env": "production",
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/curl:latest",
        "command_override": ["sh","-c",'curl -XDELETE "https://api.frontdesk.lsit.ucdavis.edu/api/announcement?key=$API_KEY"'],
        "is_private": True
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "FrontDeskAppProdCleanupExpiredGuests",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "frontdesk-app-cleanup-expired-guests",
        "app_env": "production",
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/curl:latest",
        "command_override": ["sh","-c","curl -XDELETE https://api.frontdesk.lsit.ucdavis.edu/api/expiredGuests?key=$API_KEY"],
        "is_private": True,
        "schedule": {"minute": "*"}
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "FrontDeskAppProductionProcessGuestEvents",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "frontdesk-app-process-guest-events",
        "app_env": "production",
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/frontdesk-app-server-prod:latest",
        "command_override": ["npm","run","processGuestEvents"],
        "is_private": True,
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

LSITStack(
    app,
    "FrontDeskAppSessionWorkerProductionStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    network_stack.load_balancer,
    {
        "app_name": "frontdesk-app-session-worker",
        "app_env": "production",
        "task_port": 3002,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/frontdesk-app-server-prod:latest",
        "is_private": True,
        "command": ["npm","run","sessionWorker"],
        "is_public_facing": False
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

VOIPStack(
    app,
    "FrontDeskAppVOIPProductionStack",
    network_stack.vpc,
    network_stack.bucket,
    {
        "app_name": "frontdesk-app-voip",
        "app_env": "production",
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "FrontDeskAppProductionVoipHealthCheck",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "frontdesk-app-voip-health-check",
        "app_env": "production",
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/frontdesk-app-server-prod:latest",
        "command_override": ["npm","run","voipHealthCheck"],
        "is_private": True,
        "schedule": {"minute": "/10"}
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

# Staging
LSITStack(
    app,
    "FrontDeskAppClientStagingStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    network_stack.load_balancer,
    {
        "app_name": "frontdesk-app-client",
        "app_env": "staging",
        "task_port": 3000,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/frontdesk-app-client-staging:latest",
        "health_check_path": "/api/health",
        "https_listener": frontdesk_frontend_stack.https_listener,
        "http_listener": frontdesk_frontend_stack.http_listener,
        "https_load_balancer_priority": 4,
        "http_load_balancer_priority": 4,
        "host_headers": [
            "stage.advisingfrontdesk.lsit.ucdavis.edu",
            "uea.stage.advisingfrontdesk.lsit.ucdavis.edu",
            "lsit.stage.advisingfrontdesk.lsit.ucdavis.edu",
            "grad.stage.advisingfrontdesk.lsit.ucdavis.edu",
            "antsocmsa.stage.advisingfrontdesk.lsit.ucdavis.edu",
            "cs.stage.advisingfrontdesk.lsit.ucdavis.edu",
            "langlit.stage.advisingfrontdesk.lsit.ucdavis.edu",
            "orangecluster.stage.advisingfrontdesk.lsit.ucdavis.edu",
            "our.stage.advisingfrontdesk.lsit.ucdavis.edu"
        ],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/fb44cb3a-36b8-43c5-83d7-6b54326a461b", "arn:aws:acm:us-west-2:042277129213:certificate/08b8b642-5734-4a56-864f-c813aa565c3e"],
        "is_private": True,
        "additional_https_rule_priorities": [8],
        "additional_http_rule_priorities": [8],
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

LSITStack(
    app,
    "FrontDeskAppServerStagingStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    network_stack.load_balancer,
    {
        "app_name": "frontdesk-app-server",
        "app_env": "staging",
        "task_port": 3001,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/frontdesk-app-server-staging:latest",
        "https_listener": frontdesk_frontend_stack.https_listener,
        "http_listener": frontdesk_frontend_stack.http_listener,
        "https_load_balancer_priority": 5,
        "http_load_balancer_priority": 5,
        "host_headers": ["stage.api.frontdesk.lsit.ucdavis.edu"],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/08b8b642-5734-4a56-864f-c813aa565c3e"],
        "is_private": True,
        "monitoring_stack": monitoring_stack
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

LSITStack(
    app,
    "FrontDeskAppWebsocketStagingStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    network_stack.load_balancer,
    {
        "app_name": "frontdesk-app-websocket",
        "app_env": "staging",
        "task_port": 80,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/frontdesk-app-websocket-staging:latest",
        "https_listener": frontdesk_frontend_stack.https_listener,
        "http_listener": frontdesk_frontend_stack.http_listener,
        "https_load_balancer_priority": 6,
        "http_load_balancer_priority": 6,
        "host_headers": ["stage.websocket.frontdesk.lsit.ucdavis.edu"],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/4dc5c23e-cf7c-4513-b6a5-c1e5955ad3eb"],
        "is_private": True,
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "FrontDeskAppStagingCleanupGuests",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "frontdesk-app-cleanup-guests",
        "app_env": "staging",
        "image_uri": "curlimages/curl:latest",
        "command_override": ["sh","-c","curl -XDELETE https://stage.api.frontdesk.lsit.ucdavis.edu/api/guest?key=$API_KEY"],
        "is_private": True
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "FrontDeskAppStagingCleanupAnnouncements",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "frontdesk-app-cleanup-announcements",
        "app_env": "staging",
        "image_uri": "curlimages/curl:latest",
        "command_override": ["sh","-c",'curl -XDELETE "https://stage.api.frontdesk.lsit.ucdavis.edu/api/announcement?key=$API_KEY&domain=$DOMAIN"'],
        "is_private": True
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "FrontDeskAppStagingCleanupExpiredGuests",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "frontdesk-app-cleanup-expired-guests",
        "app_env": "staging",
        "image_uri": "curlimages/curl:latest",
        "command_override": ["sh","-c","curl -XDELETE https://stage.api.frontdesk.lsit.ucdavis.edu/api/expiredGuests?key=$API_KEY"],
        "is_private": True,
        "schedule": {"minute": "*"}
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "FrontDeskAppStagingProcessGuestEvents",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "frontdesk-app-process-guest-events",
        "app_env": "staging",
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/frontdesk-app-server-staging:latest",
        "command_override": ["npm","run","processGuestEvents"],
        "is_private": True
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

LSITStack(
    app,
    "FrontDeskAppSessionWorkerStagingStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    network_stack.load_balancer,
    {
        "app_name": "frontdesk-app-session-worker",
        "app_env": "staging",
        "task_port": 3002,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/frontdesk-app-server-staging:latest",
        "is_private": True,
        "command": ["npm","run","sessionWorker"],
        "is_public_facing": False
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

VOIPStack(
    app,
    "FrontDeskAppVOIPStagingStack",
    network_stack.vpc,
    network_stack.bucket,
    {
        "app_name": "frontdesk-app-voip",
        "app_env": "staging",
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "FrontDeskAppStagingVoipHealthCheck",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "frontdesk-app-voip-health-check",
        "app_env": "staging",
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/frontdesk-app-server-staging:latest",
        "command_override": ["npm","run","voipHealthCheck"],
        "is_private": True,
        "schedule": {"minute": "/5"}
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

# Get VFD
GetVFDStack(
    app,
    "GetVFDStack",
    {
        "app_name": "frontdesk-app-getvfd",
        "app_env": "production",
        "https_listener": frontdesk_frontend_stack.https_listener,
        "http_listener": frontdesk_frontend_stack.http_listener,
        "https_load_balancer_priority": 7,
        "http_load_balancer_priority": 7,
        "host_headers": ["getvfd.ucdavis.edu"],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/a4fdc45f-ed12-41ec-aadc-f7367c8edd02"],
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION)
)

# Queue Stack
QueueStack(
    app,
    "QueueStack",
    {
        "queue_name": "GuestEventsQueue",
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION)
)

QueueStack(
    app,
    "QueueStagingStack",
    {
        "queue_name": "GuestEventsStagingQueue",
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION)
)

QueueStack(
    app,
    "QueueDevelopmentStack",
    {
        "queue_name": "GuestEventsDevelopmentQueue",
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION)
)

# Qualtrics Tools Prod
qualtrics_tools_stack = LSITStack(
    app,
    "QualtricsToolsAppProdStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    network_stack.load_balancer,
    {
        "app_name": "qualtrics-tools",
        "app_env": "production",
        "task_port": 3000,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/qualtrics-tools-production:latest",
        "https_listener": frontdesk_frontend_stack.https_listener,
        "http_listener": frontdesk_frontend_stack.http_listener,
        "health_check_path": "/api/hello",
        "https_load_balancer_priority": 12,
        "http_load_balancer_priority": 12,
        "host_headers": [
            "qualtricstools.lsit.ucdavis.edu",
        ],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/1c9afea1-244f-4e98-a460-7dc585b67205"],
        "is_private": True,
        "monitoring_stack": monitoring_stack,
        "resource_multiplier": 2,
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "QualtricsToolsAppTransferSurverys",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "qualtrics-tools-transfer-surveys",
        "app_env": "production",
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/curl:latest",
        "command_override": ["sh","-c","curl -XGET https://qualtricstools.lsit.ucdavis.edu/api/cron/transferSurveys?key=$API_KEY"],
        "is_private": True,
        "schedule": {"minute": "/5"}
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "QualtricsToolsAppSyncGroups",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "qualtrics-tools-sync-groups",
        "app_env": "production",
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/curl:latest",
        "command_override": ["sh","-c","curl -XGET https://qualtricstools.lsit.ucdavis.edu/api/cron/syncGroups?key=$API_KEY"],
        "is_private": True,
        "schedule": {"minute": "0"}
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

# Qualtrics Tools Stage
qualtrics_tools_staging_stack = LSITStack(
    app,
    "QualtricsToolsAppStagingStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    network_stack.load_balancer,
    {
        "app_name": "qualtrics-tools",
        "app_env": "staging",
        "task_port": 3000,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/qualtrics-tools-staging:latest",
        "https_listener": frontdesk_frontend_stack.https_listener,
        "http_listener": frontdesk_frontend_stack.http_listener,
        "health_check_path": "/api/hello",
        "https_load_balancer_priority": 13,
        "http_load_balancer_priority": 13,
        "host_headers": [
            "stage.qualtricstools.lsit.ucdavis.edu",
        ],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/97ee11b0-4947-4029-a7bf-0e5b2b6c33dd"],
        "is_private": True
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "QualtricsToolsAppStagingTransferSurverys",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "qualtrics-tools-transfer-surveys",
        "app_env": "staging",
        "image_uri": "curlimages/curl:latest",
        "command_override": ["sh","-c","curl -XGET https://stage.qualtricstools.lsit.ucdavis.edu/api/cron/transferSurveys?key=$API_KEY"],
        "is_private": True,
        "schedule": {"minute": "/5"}
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "QualtricsToolsAppStagingSyncGroups",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "qualtrics-tools-sync-groups",
        "app_env": "staging",
        "image_uri": "curlimages/curl:latest",
        "command_override": ["sh","-c","curl -XGET https://stage.qualtricstools.lsit.ucdavis.edu/api/cron/syncGroups?key=$API_KEY"],
        "is_private": True,
        "schedule": {"minute": "0"}
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

# LSIT Coal Prod
lsit_coal_stack = LSITStack(
    app,
    "LSITCoalAppProdStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    network_stack.load_balancer,
    {
        "app_name": "lsit-coal",
        "app_env": "production",
        "task_port": 3000,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/lsit-coal-production:latest",
        "https_listener": frontdesk_frontend_stack.https_listener,
        "http_listener": frontdesk_frontend_stack.http_listener,
        "health_check_path": "/api/health",
        "https_load_balancer_priority": 18,
        "http_load_balancer_priority": 18,
        "host_headers": [
            "coal.lsit.ucdavis.edu",
        ],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/91bcac5e-6491-4f68-b5b1-5a8e80695c1b"],
        "is_private": True,
        "monitoring_stack": monitoring_stack
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

ScheudledTaskStack(
    app,
    "LSITCoalAppCronProdStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    {
        "app_name": "lsit-coal-cron",
        "app_env": "production",
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/lsit-coal-cron-production:latest",
        "is_private": True,
        "schedule": {"minute": "0", "hour": "16"}
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

# DX Network Stack
dx_network_stack = NetworkStack(
    app,
    "DXNetworkStack",
    {
        "prefix": "DX",
        "aws_bucket_name": "lsit-dx-apps-env-vars",
        "ip_addresses": "172.29.117.0/25",
        "is_dx": True
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

# LSIT UCPath Audit Prod DX
ucpath_audit_stack = LSITStack(
    app,
    "LSITUCPathAuditDXAppProdStack",
    dx_network_stack.vpc,
    dx_network_stack.bucket,
    dx_network_stack.cluster,
    dx_network_stack.load_balancer,
    {
        "app_name": "lsit-ucpath-audit",
        "app_env": "production",
        "task_port": 3000,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/lsit-ucpath-audit-production:latest",
        "health_check_path": "/api/health",
        "https_load_balancer_priority": 1,
        "http_load_balancer_priority": 1,
        "host_headers": [
            "ucpathaudit.lsit.ucdavis.edu",
        ],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/abcf5e1d-65ec-4363-9c53-484e6fa1e81a"],
        "is_private": True,
        "monitoring_stack": monitoring_stack
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

# LSIT UCPath Audit Take Snapshots Prod DX
ScheudledTaskStack(
    app,
    "LSITUCPathAuditDXAppProdTakeSnapshots",
    dx_network_stack.vpc,
    dx_network_stack.bucket,
    dx_network_stack.cluster,
    {
        "app_name": "lsit-ucpath-audit-take-snapshots",
        "app_env": "production",
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/lsit-ucpath-audit-cron-production:latest",
        "is_private": True,
        "schedule": {"minute": "0", "hour": "14"}
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

# LSIT UCPath Audit Staging DX
ucpath_audit_stack = LSITStack(
    app,
    "LSITUCPathAuditDXAppStagingStack",
    dx_network_stack.vpc,
    dx_network_stack.bucket,
    dx_network_stack.cluster,
    dx_network_stack.load_balancer,
    {
        "app_name": "lsit-ucpath-audit",
        "app_env": "staging",
        "task_port": 3000,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/lsit-ucpath-audit-staging:latest",
        "health_check_path": "/api/health",
        "https_listener": ucpath_audit_stack.https_listener,
        "http_listener": ucpath_audit_stack.http_listener,
        "https_load_balancer_priority": 2,
        "http_load_balancer_priority": 2,
        "host_headers": [
            "stage.ucpathaudit.lsit.ucdavis.edu",
        ],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/371f6abf-1096-4385-8534-3e6fea0da989"],
        "is_private": True,
        "monitoring_stack": monitoring_stack
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

# LSIT UCPath Audit Take Snapshots Staging DX
ScheudledTaskStack(
    app,
    "LSITUCPathAuditDXAppStagingTakeSnapshots",
    dx_network_stack.vpc,
    dx_network_stack.bucket,
    dx_network_stack.cluster,
    {
        "app_name": "lsit-ucpath-audit-take-snapshots",
        "app_env": "staging",
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/lsit-ucpath-audit-cron-staging:latest",
        "is_private": True,
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

# LSIT Comp2 Prod
lsit_comp2_stack = LSITStack(
    app,
    "LSITComp2AppProdStack",
    network_stack.vpc,
    network_stack.bucket,
    network_stack.cluster,
    network_stack.load_balancer,
    {
        "app_name": "lsit-comp2",
        "app_env": "production",
        "task_port": 3000,
        "image_uri": "042277129213.dkr.ecr.us-west-2.amazonaws.com/lsit-comp2-production:latest",
        "https_listener": frontdesk_frontend_stack.https_listener,
        "http_listener": frontdesk_frontend_stack.http_listener,
        "health_check_path": "/api/health",
        "https_load_balancer_priority": 20,
        "http_load_balancer_priority": 20,
        "host_headers": [
            "comp2.lsit.ucdavis.edu",
        ],
        "certificate_arns": ["arn:aws:acm:us-west-2:042277129213:certificate/978f7b9c-5ef4-4501-bd36-451a71e85213"],
        "is_private": True,
        "monitoring_stack": monitoring_stack
    },
    env=Environment(account=CDK_DEFAULT_ACCOUNT, region=CDK_DEFAULT_REGION),
)

app.synth()
