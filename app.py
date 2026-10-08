import os
import re
import sys
import shutil
import tempfile
import json
import uuid
import glob
import streamlit as st
import streamlit.components.v1 as components
import boto3
from fpdf import FPDF
from PIL import Image

# Ensure Graphviz dot is found in common Windows installation paths
def ensure_graphviz_in_path():
    if shutil.which("dot") is not None:
        return True
    
    candidate_paths = [
        r"C:\Program Files\Graphviz\bin",
        r"C:\Program Files (x86)\Graphviz\bin",
        os.path.expanduser(r"~\AppData\Local\Programs\Graphviz\bin"),
        os.path.expanduser(r"~\AppData\Local\Graphviz\bin"),
    ]
    
    import glob
    candidate_paths.extend(glob.glob(r"C:\Program Files\Graphviz*\bin"))
    candidate_paths.extend(glob.glob(r"C:\Program Files (x86)\Graphviz*\bin"))

    for p in candidate_paths:
        dot_path = os.path.join(p, "dot.exe")
        if os.path.exists(dot_path):
            os.environ["PATH"] += os.pathsep + p
            return True
    return False

HAS_GRAPHVIZ_DOT = ensure_graphviz_in_path()

# Setup Streamlit page configuration
st.set_page_config(
    page_title="ArchitectAI | Enterprise AWS Design Studio",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Enterprise Dark Theme ─────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes pulseGlow {
    0%,100% { box-shadow: 0 0 6px rgba(255,153,0,.35); }
    50%      { box-shadow: 0 0 22px rgba(255,153,0,.75); }
  }

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .main .block-container {
    padding-top: 1.6rem;
    padding-bottom: 3rem;
    animation: fadeInUp .5s ease-out;
  }

  /* ── Hero banner ── */
  .hero-container {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 55%, #0F172A 100%);
    border: 1px solid rgba(255,255,255,.09);
    border-radius: 16px;
    padding: 2.2rem 2.5rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 20px 40px rgba(0,0,0,.4);
  }
  .hero-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    background: rgba(16,185,129,.15);
    color: #10B981;
    border: 1px solid rgba(16,185,129,.35);
    font-size: .80rem;
    font-weight: 600;
    margin-bottom: .7rem;
    letter-spacing: .03em;
  }
  .hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #FF9900 0%, #FFC066 50%, #FFFFFF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.2;
    margin-bottom: .45rem;
  }
  .hero-subtitle {
    color: #94A3B8;
    font-size: 1.02rem;
  }

  /* ── Metric cards ── */
  .metric-card {
    background: rgba(30,41,59,.75);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 12px;
    padding: 1.1rem .8rem;
    text-align: center;
    transition: transform .25s ease, border-color .25s ease;
  }
  .metric-card:hover {
    transform: translateY(-4px);
    border-color: rgba(255,153,0,.45);
    animation: pulseGlow 2s infinite;
  }
  .metric-value { font-size: 1.7rem; font-weight: 700; color: #FF9900; }
  .metric-label {
    font-size: .78rem;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: .06em;
    margin-top: .25rem;
  }

  /* ── Preset buttons ── */
  .stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all .25s ease !important;
    border: 1px solid rgba(255,153,0,.4) !important;
  }
  .stButton > button:hover {
    background: rgba(255,153,0,.15) !important;
    border-color: #FF9900 !important;
    color: #FF9900 !important;
    transform: translateY(-2px) !important;
  }

  /* ── Generate CTA ── */
  div[data-testid="stButton"]:has(button[kind="primary"]) button {
    background: linear-gradient(90deg, #FF9900, #E68A00) !important;
    color: #fff !important;
    font-size: 1.05rem !important;
    padding: .7rem 1.5rem !important;
    border: none !important;
    border-radius: 12px !important;
    animation: pulseGlow 3s infinite;
  }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(15,23,42,.8);
    border-radius: 10px;
    padding: 4px;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: .4rem 1rem;
    font-weight: 600;
    color: #94A3B8;
  }
  .stTabs [aria-selected="true"] {
    background: rgba(255,153,0,.18) !important;
    color: #FF9900 !important;
  }

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
    border-right: 1px solid rgba(255,255,255,.07);
  }
  section[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
  section[data-testid="stSidebar"] h1,
  section[data-testid="stSidebar"] h2,
  section[data-testid="stSidebar"] h3 { color: #FF9900 !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg",
        width=110
    )
    st.title("⚙️ Engine Settings")

    st.subheader("AWS Region")
    aws_region = st.selectbox(
        "Region",
        ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "ap-south-1"],
        index=0
    )

    st.divider()
    st.subheader("AI Engine")
    # On Render (no AWS credentials available), default to Smart Engine automatically.
    # Locally with AWS CLI configured, defaults to Bedrock.
    _default_engine_idx = 1 if os.environ.get("DEFAULT_ENGINE") == "smart" else 0
    ai_engine = st.selectbox(
        "Select Provider",
        ["AWS Bedrock (Claude / Nova via Boto3)", "Smart AWS Architect Engine (Local / Zero Setup)"],
        index=_default_engine_idx
    )

    bedrock_model = "amazon.nova-lite-v1:0"
    if "Bedrock" in ai_engine:
        bedrock_model = st.selectbox(
            "Bedrock Model",
            [
                "amazon.nova-lite-v1:0",
                "amazon.nova-micro-v1:0",
                "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "anthropic.claude-3-haiku-20240307-v1:0",
            ],
            index=0,
            help="Nova Lite: fast & cost-effective. Claude Sonnet: highest quality."
        )

    st.divider()
    st.caption("🟢 **Status:** Ready")
    st.caption("💡 **Cost/run:** ~$0.001")

# Helper Function: Generate Diagram using diagrams library
# Comprehensive AWS service detection map - covers 50+ services
# Maps a canonical service key -> list of keyword aliases to look for in the
# user's requirement text / code snippet. This enables ChatGPT-level service detection.
SERVICE_KEYWORD_MAP = {
    # Edge & Network Services
    "route53": ["route 53", "route53", "dns", "domain name system"],
    "cloudfront": ["cloudfront", "cdn", "content delivery", "edge cache"],
    "waf": ["waf", "web application firewall", "ddos protection"],
    "shield": ["shield", "ddos protection", "advanced protection"],
    "globalaccelerator": ["global accelerator", "anycast ip", "edge optimization"],
    
    # Load Balancers & API
    "alb": ["load balancer", "alb", "application load balancer", "elb", "elastic load balancer"],
    "nlb": ["network load balancer", "nlb", "layer 4"],
    "apigateway": ["api gateway", "rest api", "graphql api", "appsync", "http api"],
    "appmesh": ["app mesh", "service mesh", "microservices mesh"],
    
    # Authentication & Authorization
    "cognito": ["cognito", "user pool", "authentication", "auth0", " auth ", "identity pool"],
    "iam": ["iam role", "iam policy", " iam ", "access control", "permissions"],
    "directory": ["directory service", "active directory", "ldap"],
    "sso": ["single sign-on", "sso", "identity center"],
    
    # Compute Services
    "lambda": ["lambda", "serverless function", "serverless backend", "function as a service"],
    "ec2": ["ec2", "virtual machine", "compute instance", "elastic compute"],
    "ecs": ["ecs", "fargate", "elastic container service", "docker container"],
    "eks": ["eks", "kubernetes", "k8s", "container orchestration"],
    "batch": ["aws batch", "batch processing", "job queue"],
    "lightsail": ["lightsail", "vps", "virtual private server"],
    "outposts": ["outposts", "hybrid cloud", "on-premises"],
    
    # Serverless & Orchestration
    "stepfunctions": ["step functions", "state machine", "workflow orchestration"],
    "eventbridge": ["eventbridge", "event bus", "event-driven"],
    "apprunner": ["app runner", "containerized web app"],
    
    # Storage Services
    "s3": ["s3", "object storage", "static assets", "bucket", "blob storage"],
    "efs": ["efs", "elastic file system", "network file system", "nfs"],
    "fsx": ["fsx", "lustre", "windows file system"],
    "ebs": ["ebs", "elastic block store", "disk storage"],
    "storagegw": ["storage gateway", "hybrid storage"],
    
    # Database Services
    "dynamodb": ["dynamodb", "nosql", "key-value database", "document database"],
    "rds": ["rds", "aurora", "postgres", "mysql", "relational database", "sql database"],
    "redshift": ["redshift", "data warehouse", "analytics database", "olap"],
    "elasticache": ["elasticache", "redis", "memcached", "in-memory cache"],
    "documentdb": ["documentdb", "mongodb", "document store"],
    "neptune": ["neptune", "graph database", "neo4j"],
    "timestream": ["timestream", "time series database"],
    "keyspaces": ["keyspaces", "cassandra", "wide column"],
    "qldb": ["qldb", "quantum ledger", "blockchain", "immutable ledger"],
    "opensearch": ["opensearch", "elasticsearch", "search engine", "full-text search"],
    
    # Analytics & Big Data
    "kinesis": ["kinesis", "data stream", "real-time analytics", "streaming data"],
    "glue": ["glue", "etl job", "data catalog", "data preparation"],
    "athena": ["athena", "query data lake", "serverless sql"],
    "emr": ["emr", "hadoop", "spark", "big data processing"],
    "databrew": ["databrew", "data preparation", "visual etl"],
    "lake": ["lake formation", "data lake", "data governance"],
    "msk": ["msk", "kafka", "managed kafka", "message streaming"],
    "quicksight": ["quicksight", "business intelligence", "data visualization", "dashboards"],
    
    # Machine Learning & AI
    "sagemaker": ["sagemaker", "machine learning model", "ml training", "jupyter"],
    "bedrock": ["bedrock", "foundation model", "generative ai", "llm"],
    "comprehend": ["comprehend", "natural language processing", "nlp", "sentiment"],
    "rekognition": ["rekognition", "image recognition", "computer vision", "facial recognition"],
    "textract": ["textract", "ocr", "document analysis"],
    "translate": ["translate", "language translation"],
    "polly": ["polly", "text to speech", "tts"],
    "transcribe": ["transcribe", "speech to text", "stt"],
    "lex": ["lex", "chatbot", "conversational ai"],
    "personalize": ["personalize", "recommendation engine"],
    "forecast": ["forecast", "time series forecasting"],
    
    # Messaging & Communication
    "sqs": ["sqs", "queue", "message queue"],
    "sns": ["sns", "pub/sub", "push notification", "topic"],
    "ses": ["ses", "email notification", "send email", "email service"],
    "pinpoint": ["pinpoint", "marketing automation", "customer engagement"],
    "chime": ["chime", "video conferencing", "communication"],
    
    # Security Services
    "kms": ["kms", "encryption key", "key management"],
    "secretsmanager": ["secrets manager", "secret rotation", "credential management"],
    "hsm": ["cloudhsm", "hardware security module"],
    "acm": ["certificate manager", "ssl certificate", "tls certificate"],
    "inspector": ["inspector", "security assessment", "vulnerability scanning"],
    "guardduty": ["guardduty", "threat detection", "security monitoring"],
    "macie": ["macie", "data discovery", "pii detection"],
    "config": ["config", "configuration compliance", "resource monitoring"],
    "cloudtrail": ["cloudtrail", "audit logging", "api calls"],
    "securityhub": ["security hub", "security posture", "compliance dashboard"],
    
    # Monitoring & Management
    "cloudwatch": ["cloudwatch", "monitoring", "metrics", "alarms", "logs"],
    "xray": ["x-ray", "distributed tracing", "application insights"],
    "systems": ["systems manager", "parameter store", "patch manager"],
    "cloudformation": ["cloudformation", "infrastructure as code", "iac", "stack"],
    "cdk": ["cdk", "cloud development kit", "infrastructure code"],
    "opsworks": ["opsworks", "configuration management", "chef", "puppet"],
    
    # Developer Tools
    "codecommit": ["codecommit", "git repository", "source control"],
    "codebuild": ["codebuild", "build service", "continuous integration"],
    "codedeploy": ["codedeploy", "deployment automation"],
    "codepipeline": ["codepipeline", "cicd", "continuous delivery"],
    "cloud9": ["cloud9", "ide", "development environment"],
    "codecatalyst": ["codecatalyst", "devops platform"],
    
    # Integration Services
    "swf": ["simple workflow", "swf", "workflow service"],
    "mq": ["amazon mq", "message broker", "activemq"],
    "appflow": ["appflow", "data integration", "saas integration"],
    
    # Content & Media
    "mediaconvert": ["mediaconvert", "video processing", "transcoding"],
    "mediastore": ["mediastore", "media storage"],
    "medialive": ["medialive", "live streaming"],
    
    # IoT Services
    "iot": ["iot core", "internet of things", "device management"],
    "greengrass": ["greengrass", "edge computing", "iot edge"],
    
    # Game Development
    "gamelift": ["gamelift", "game server hosting", "multiplayer"],
    
    # Blockchain
    "managedblockchain": ["managed blockchain", "hyperledger fabric", "ethereum"],
    
    # Satellite
    "groundstation": ["ground station", "satellite communication"],
    
    # Quantum Computing
    "braket": ["braket", "quantum computing"],
    
    # Robotics
    "robomaker": ["robomaker", "robot development", "ros"],
}

# Enhanced diagram tiers for better architectural flow - covers all 70+ services
# Within a tier, nodes fan out from the previous tier's node(s) and all feed
# into the next tier's node(s) — giving a layout that reflects actual request
# flow instead of one arbitrary chain through every detected service.
SERVICE_TIERS = [
    # Tier 1: Edge & DNS Layer
    ["route53", "cloudfront", "waf", "shield", "globalaccelerator"],
    
    # Tier 2: Load Balancing & API Gateway Layer  
    ["alb", "nlb", "apigateway", "appmesh"],
    
    # Tier 3: Authentication & Authorization Layer
    ["cognito", "iam", "directory", "sso"],
    
    # Tier 4: Compute & Processing Layer
    ["lambda", "ec2", "ecs", "eks", "batch", "lightsail", "outposts", "apprunner"],
    
    # Tier 5: Orchestration & Workflow Layer
    ["stepfunctions", "eventbridge", "swf"],
    
    # Tier 6: Database & Analytics Layer
    ["dynamodb", "rds", "redshift", "elasticache", "documentdb", "neptune", 
     "timestream", "keyspaces", "qldb", "opensearch", "athena", "emr"],
    
    # Tier 7: Storage Layer
    ["s3", "efs", "fsx", "ebs", "storagegw"],
    
    # Tier 8: Big Data & Streaming Layer
    ["kinesis", "glue", "databrew", "lake", "msk", "quicksight"],
    
    # Tier 9: ML & AI Layer
    ["sagemaker", "bedrock", "comprehend", "rekognition", "textract", "translate", 
     "polly", "transcribe", "lex", "personalize", "forecast"],
    
    # Tier 10: Messaging & Communication Layer
    ["sqs", "sns", "ses", "pinpoint", "chime", "mq", "appflow"],
    
    # Tier 11: Security & Compliance Layer
    ["kms", "secretsmanager", "hsm", "acm", "inspector", "guardduty", "macie", 
     "config", "cloudtrail", "securityhub"],
    
    # Tier 12: Monitoring & Management Layer
    ["cloudwatch", "xray", "systems", "cloudformation", "cdk", "opsworks"],
    
    # Tier 13: Developer Tools Layer
    ["codecommit", "codebuild", "codedeploy", "codepipeline", "cloud9", "codecatalyst"],
    
    # Tier 14: Specialized Services Layer
    ["mediaconvert", "mediastore", "medialive", "iot", "greengrass", "gamelift", 
     "managedblockchain", "groundstation", "braket", "robomaker"]
]


def detect_services(text):
    """Scan requirement text / code for AWS service mentions using SERVICE_KEYWORD_MAP.

    Short/ambiguous aliases (e.g. "rds", "ses", "s3") are matched on word
    boundaries so they don't false-positive inside unrelated words
    (e.g. "orders" contains the substring "rds", "uses" contains "ses").
    Longer, multi-word aliases (e.g. "api gateway") still use plain substring
    matching since they're unlikely to appear accidentally inside other words.
    """
    text_lower = text.lower()
    found = []
    for service_key, aliases in SERVICE_KEYWORD_MAP.items():
        for alias in aliases:
            alias = alias.strip()
            if len(alias) <= 4 and " " not in alias:
                if re.search(r"\b" + re.escape(alias) + r"\b", text_lower):
                    found.append(service_key)
                    break
            else:
                if alias in text_lower:
                    found.append(service_key)
                    break
    return found


def generate_diagram(services_found, filename="aws_architecture"):
    """
    Generates an AWS Architecture Diagram image using the python `diagrams` library.
    `services_found` is a list of canonical service keys from SERVICE_KEYWORD_MAP
    (see detect_services()). The diagram lays services out in request-flow tiers
    (edge -> compute -> data -> messaging -> observability) rather than a single
    fixed chain, so it reflects the actual requirement instead of a hardcoded shape.
    Now supports 70+ AWS services for comprehensive ChatGPT-level diagrams.
    """
    from diagrams import Diagram
    from diagrams.aws.network import APIGateway, CloudFront, Route53, ELB, NLB
    from diagrams.aws.network import ClientVpn as WAFPlaceholder  # fallback if WAF unavailable
    from diagrams.aws.compute import Lambda, EC2, ECS, EKS, Batch, Lightsail
    from diagrams.aws.integration import StepFunctions, SNS, SQS, Eventbridge, MQ
    from diagrams.aws.database import Dynamodb, RDS, ElastiCache, Redshift, DocumentDB, Neptune, Timestream
    from diagrams.aws.storage import SimpleStorageServiceS3, EFS, FSx, EBS
    from diagrams.aws.security import Cognito, IAM, KMS, SecretsManager, CertificateManager, Macie
    from diagrams.aws.management import Cloudwatch, Config, Cloudtrail, SystemsManager, Cloudformation
    from diagrams.aws.ml import Sagemaker, Comprehend, Rekognition, Textract, Translate, Polly, Transcribe, Lex, Personalize, Forecast
    from diagrams.aws.analytics import Glue, Athena, KinesisDataStreams, EMR, Quicksight
    from diagrams.aws.devtools import Codecommit, Codebuild, Codedeploy, Codepipeline, Cloud9
    from diagrams.aws.engagement import SES, Pinpoint
    from diagrams.aws.iot import IotCore

    try:
        from diagrams.aws.network import WAF
    except ImportError:
        WAF = WAFPlaceholder

    try:
        from diagrams.aws.devtools import XRay
    except ImportError:
        XRay = Cloudwatch

    try:
        from diagrams.aws.ml import Bedrock
    except ImportError:
        Bedrock = Sagemaker

    try:
        from diagrams.aws.general import General
    except ImportError:
        General = Lambda

    # Comprehensive node factory supporting 70+ AWS services
    node_factory = {
        # Edge & Network Services
        "route53": lambda: Route53("Route 53 DNS"),
        "cloudfront": lambda: CloudFront("CloudFront CDN"),
        "waf": lambda: WAF("AWS WAF"),
        "shield": lambda: Lambda("AWS Shield"),
        "globalaccelerator": lambda: Lambda("Global Accelerator"),
        
        # Load Balancers & API
        "alb": lambda: ELB("Application Load Balancer"),
        "nlb": lambda: NLB("Network Load Balancer"),
        "apigateway": lambda: APIGateway("API Gateway"),
        "appmesh": lambda: Lambda("App Mesh"),
        
        # Authentication & Authorization
        "cognito": lambda: Cognito("Cognito User Pools"),
        "iam": lambda: IAM("IAM Roles & Policies"),
        "directory": lambda: Lambda("Directory Service"),
        "sso": lambda: Lambda("AWS SSO"),
        
        # Compute Services
        "lambda": lambda: Lambda("Lambda Functions"),
        "ec2": lambda: EC2("EC2 Instances"),
        "ecs": lambda: ECS("ECS Fargate"),
        "eks": lambda: EKS("EKS Cluster"),
        "batch": lambda: Batch("AWS Batch"),
        "lightsail": lambda: Lightsail("Lightsail VPS"),
        "outposts": lambda: Lambda("AWS Outposts"),
        "apprunner": lambda: Lambda("App Runner"),
        
        # Serverless & Orchestration
        "stepfunctions": lambda: StepFunctions("Step Functions"),
        "eventbridge": lambda: Eventbridge("EventBridge"),
        "swf": lambda: Lambda("Simple Workflow"),
        
        # Storage Services
        "s3": lambda: SimpleStorageServiceS3("S3 Object Storage"),
        "efs": lambda: EFS("EFS Network Storage"),
        "fsx": lambda: FSx("FSx File Systems"),
        "ebs": lambda: EBS("EBS Block Storage"),
        "storagegw": lambda: Lambda("Storage Gateway"),
        
        # Database Services
        "dynamodb": lambda: Dynamodb("DynamoDB NoSQL"),
        "rds": lambda: RDS("RDS Aurora"),
        "redshift": lambda: Redshift("Redshift Warehouse"),
        "elasticache": lambda: ElastiCache("ElastiCache Redis"),
        "documentdb": lambda: DocumentDB("DocumentDB"),
        "neptune": lambda: Neptune("Neptune Graph DB"),
        "timestream": lambda: Timestream("Timestream"),
        "keyspaces": lambda: Lambda("Keyspaces Cassandra"),
        "qldb": lambda: Lambda("QLDB Ledger"),
        "opensearch": lambda: Lambda("OpenSearch"),
        
        # Analytics & Big Data
        "kinesis": lambda: KinesisDataStreams("Kinesis Streams"),
        "glue": lambda: Glue("Glue ETL"),
        "athena": lambda: Athena("Athena Queries"),
        "emr": lambda: EMR("EMR Hadoop"),
        "databrew": lambda: Lambda("DataBrew"),
        "lake": lambda: Lambda("Lake Formation"),
        "msk": lambda: Lambda("MSK Kafka"),
        "quicksight": lambda: Quicksight("QuickSight BI"),
        
        # Machine Learning & AI
        "sagemaker": lambda: Sagemaker("SageMaker ML"),
        "bedrock": lambda: Bedrock("Bedrock LLMs"),
        "comprehend": lambda: Comprehend("Comprehend NLP"),
        "rekognition": lambda: Rekognition("Rekognition Vision"),
        "textract": lambda: Textract("Textract OCR"),
        "translate": lambda: Translate("Translate"),
        "polly": lambda: Polly("Polly TTS"),
        "transcribe": lambda: Transcribe("Transcribe STT"),
        "lex": lambda: Lex("Lex Chatbot"),
        "personalize": lambda: Personalize("Personalize"),
        "forecast": lambda: Forecast("Forecast"),
        
        # Messaging & Communication
        "sqs": lambda: SQS("SQS Queue"),
        "sns": lambda: SNS("SNS Topics"),
        "ses": lambda: SES("SES Email"),
        "pinpoint": lambda: Pinpoint("Pinpoint Marketing"),
        "chime": lambda: Lambda("Chime Meetings"),
        "mq": lambda: MQ("Amazon MQ"),
        "appflow": lambda: Lambda("AppFlow Integration"),
        
        # Security Services
        "kms": lambda: KMS("KMS Encryption"),
        "secretsmanager": lambda: SecretsManager("Secrets Manager"),
        "hsm": lambda: Lambda("CloudHSM"),
        "acm": lambda: CertificateManager("Certificate Manager"),
        "inspector": lambda: Lambda("Inspector Security"),
        "guardduty": lambda: Lambda("GuardDuty Threat Detection"),
        "macie": lambda: Macie("Macie Data Discovery"),
        "config": lambda: Config("Config Compliance"),
        "cloudtrail": lambda: Cloudtrail("CloudTrail Audit"),
        "securityhub": lambda: Lambda("Security Hub"),
        
        # Monitoring & Management
        "cloudwatch": lambda: Cloudwatch("CloudWatch Monitoring"),
        "xray": lambda: XRay("X-Ray Tracing"),
        "systems": lambda: SystemsManager("Systems Manager"),
        "cloudformation": lambda: Cloudformation("CloudFormation IaC"),
        "cdk": lambda: Lambda("AWS CDK"),
        "opsworks": lambda: Lambda("OpsWorks"),
        
        # Developer Tools
        "codecommit": lambda: Codecommit("CodeCommit Git"),
        "codebuild": lambda: Codebuild("CodeBuild CI"),
        "codedeploy": lambda: Codedeploy("CodeDeploy CD"),
        "codepipeline": lambda: Codepipeline("CodePipeline"),
        "cloud9": lambda: Cloud9("Cloud9 IDE"),
        "codecatalyst": lambda: Lambda("CodeCatalyst"),
        
        # Specialized Services
        "gamelift": lambda: Lambda("GameLift"),
        "managedblockchain": lambda: Lambda("Managed Blockchain"),
        "groundstation": lambda: Lambda("Ground Station"),
        "braket": lambda: Lambda("Braket Quantum"),
        "robomaker": lambda: Lambda("RoboMaker"),
        
        # Media & Content
        "mediaconvert": lambda: Lambda("MediaConvert"),
        "mediastore": lambda: Lambda("MediaStore"),
        "medialive": lambda: Lambda("MediaLive"),
        
        # IoT Services
        "iot": lambda: IotCore("IoT Core"),
        "greengrass": lambda: IotCore("IoT Greengrass"),
    }

    try:
        with Diagram("AWS Cloud Architecture", show=False, filename=filename, outformat="png"):
            services_set = set(services_found)
            nodes = {}
            
            # Create nodes for all detected services
            for key in node_factory:
                if key in services_set:
                    nodes[key] = node_factory[key]()

            # Default services if none detected
            if not nodes:
                nodes["apigateway"] = node_factory["apigateway"]()
                nodes["lambda"] = node_factory["lambda"]()
                nodes["dynamodb"] = node_factory["dynamodb"]()
                nodes["s3"] = node_factory["s3"]()

            # Connect each populated tier to the next populated tier, fanning
            # out/in as needed, so flow reflects edge -> compute -> data -> async -> ops.
            prev_tier_nodes = []
            for tier in SERVICE_TIERS:
                tier_nodes = [nodes[key] for key in tier if key in nodes]
                if not tier_nodes:
                    continue
                if prev_tier_nodes:
                    for p in prev_tier_nodes:
                        for n in tier_nodes:
                            p >> n
                prev_tier_nodes = tier_nodes

        return f"{filename}.png"
    except Exception as e:
        st.error(f"Error rendering diagram with Graphviz: {e}")
        return None

# Helper Function: Generate Documentation via AWS Bedrock or Smart Engine
def generate_documentation_bedrock(prompt, model_id, region):
    try:
        # Credential resolution order:
        # 1. Streamlit Cloud secrets (st.secrets["aws"]) — used when deployed on Streamlit Cloud
        # 2. boto3 default chain: env vars, ~/.aws/credentials, IAM role — used locally
        kwargs = {"region_name": region}
        try:
            secrets = st.secrets.get("aws", {})
            if secrets.get("AWS_ACCESS_KEY_ID") and secrets.get("AWS_SECRET_ACCESS_KEY"):
                kwargs["aws_access_key_id"]     = secrets["AWS_ACCESS_KEY_ID"]
                kwargs["aws_secret_access_key"] = secrets["AWS_SECRET_ACCESS_KEY"]
                if secrets.get("AWS_DEFAULT_REGION"):
                    kwargs["region_name"] = secrets["AWS_DEFAULT_REGION"]
        except Exception:
            pass  # st.secrets not available locally — fall back to boto3 default chain
        client = boto3.client("bedrock-runtime", **kwargs)
        
        system_prompt = """You are a Principal AWS Solutions Architect with 15+ years of experience designing enterprise cloud architectures for Fortune 500 companies.

CRITICAL INSTRUCTIONS:
1. The user input may contain assignment rubrics, test cases, deliverables, CI/CD instructions, or interview questions. IGNORE all such non-architectural content.
2. Extract ONLY the AWS services, business requirements, and technical specifications to design the architecture.
3. Focus on the actual system being built, not the assignment format or testing criteria.

Generate a comprehensive, publication-quality AWS Architecture Report with the following structure:

# AWS Cloud Architecture - [Project Name]

## 1. Executive Summary
- **Business Context**: 2-3 sentences describing the business problem and solution approach
- **Architecture Overview**: High-level description of the system design
- **Key Benefits**: Scalability, reliability, security, and cost advantages
- **Target Scale**: Expected traffic, data volume, and performance requirements

## 2. Requirements Analysis
### 2.1 Functional Requirements  
- List all business capabilities the system must provide
### 2.2 Non-Functional Requirements
- **Performance**: Response time, throughput, concurrent users
- **Availability**: Uptime requirements, RTO/RPO targets
- **Scalability**: Growth projections and scaling patterns
- **Security**: Compliance requirements (SOC2, HIPAA, PCI-DSS)
- **Cost**: Budget constraints and cost optimization priorities

## 3. Architecture Design Decisions
### 3.1 Architectural Patterns
- **Pattern Type**: Serverless/Microservices/Event-Driven/Data Pipeline
- **Rationale**: Why this pattern fits the requirements
### 3.2 Technology Stack Decisions
- **Compute Strategy**: Why Lambda vs EC2 vs Containers
- **Database Selection**: SQL vs NoSQL choice justification
- **Storage Strategy**: Hot/Warm/Cold data tiering

## 4. AWS Services & Component Breakdown
Create a detailed table with columns: Service, Category, Role, Tier, Justification, Configuration Notes, SLA

## 5. Network Architecture & VPC Design
### 5.1 VPC Structure
- CIDR blocks, subnets (public/private/database)
- Availability zones distribution
### 5.2 Security Groups & NACLs
- Inbound/outbound rules for each tier
### 5.3 Connectivity
- Internet Gateway, NAT Gateway, VPC Endpoints

## 6. Data Flow Architecture
### 6.1 Request Processing Flow
- Step-by-step user request journey through the system
### 6.2 Data Processing Pipeline
- ETL processes, real-time vs batch processing
### 6.3 Integration Patterns
- Synchronous vs asynchronous communication

## 7. Security Architecture
### 7.1 Identity & Access Management
- IAM roles, policies, and access patterns
### 7.2 Data Protection
- Encryption at rest and in transit
- Key management strategy
### 7.3 Network Security
- Security groups, NACLs, WAF rules
### 7.4 Monitoring & Compliance
- CloudTrail, GuardDuty, Security Hub integration

## 8. Scalability & High Availability Design
### 8.1 Auto Scaling Configuration
- Scaling policies and triggers
### 8.2 Multi-AZ Deployment Strategy
- Failover mechanisms and redundancy
### 8.3 Disaster Recovery Plan
- Backup strategies, RTO/RPO implementation

## 9. Performance Optimization
### 9.1 Caching Strategy
- CloudFront, ElastiCache, application-level caching
### 9.2 Database Optimization
- Indexing, read replicas, query optimization
### 9.3 Monitoring & Alerting
- CloudWatch metrics, alarms, and dashboards

## 10. Cost Analysis & Optimization
### 10.1 Detailed Cost Breakdown
Create a comprehensive table with: Service, Configuration, Monthly Cost, Cost Drivers, Optimization Opportunities

### 10.2 Cost Optimization Strategies
- Reserved Instances, Spot Instances, Right-sizing recommendations
- Data lifecycle policies and storage optimization

## 11. DevOps & CI/CD Strategy
### 11.1 Infrastructure as Code
- CloudFormation/CDK templates and deployment strategy
### 11.2 CI/CD Pipeline Design
- CodeCommit -> CodeBuild -> CodeDeploy flow
### 11.3 Environment Management
- Dev/Test/Prod environment strategy

## 12. Monitoring & Observability
### 12.1 Application Monitoring
- CloudWatch, X-Ray distributed tracing
### 12.2 Infrastructure Monitoring
- Systems Manager, Config compliance
### 12.3 Business Metrics
- Custom metrics and KPI tracking

## 13. Implementation Roadmap
### 13.1 Phase 1: Core Infrastructure (Weeks 1-2)
### 13.2 Phase 2: Application Deployment (Weeks 3-4) 
### 13.3 Phase 3: Optimization & Scale (Weeks 5-6)

## 14. Risk Assessment & Mitigation
- Technical risks, dependencies, and mitigation strategies
- Compliance and security considerations

## 15. Infrastructure as Code Sample
Provide complete, production-ready CloudFormation or CDK code for the core architecture components.

Generate this as clean, well-structured Markdown with proper formatting, tables, and technical depth that matches enterprise documentation standards."""
        
        if "claude" in model_id:
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 8192,
                "messages": [{"role": "user", "content": f"{system_prompt}\n\nRequirement:\n{prompt}"}]
            }
            response = client.invoke_model(modelId=model_id, body=json.dumps(payload))
            res_body = json.loads(response["body"].read().decode())
            return res_body["content"][0]["text"]
        elif "nova" in model_id:
            payload = {
                "messages": [{"role": "user", "content": [{"text": f"{system_prompt}\n\nRequirement:\n{prompt}"}]}],
                "inferenceConfig": {"maxTokens": 8192}
            }
            response = client.invoke_model(modelId=model_id, body=json.dumps(payload))
            res_body = json.loads(response["body"].read().decode())
            return res_body["output"]["message"]["content"][0]["text"]
        else:
            payload = {"inputText": f"{system_prompt}\n\nRequirement:\n{prompt}"}
            response = client.invoke_model(modelId=model_id, body=json.dumps(payload))
            res_body = json.loads(response["body"].read().decode())
            return res_body["results"][0]["outputText"]
    except Exception as e:
        st.warning(f"AWS Bedrock Model Access Notice: {e}. Switching to Smart AWS Architect Engine.")
        return None

def generate_documentation_smart(prompt, services):
    """Generate comprehensive ChatGPT-level architecture documentation using the Smart Engine"""
    prompt_escaped = prompt.replace('"', '\\"')
    
    # Analyze services to determine architecture pattern
    has_ml = any(s in services for s in ["bedrock", "sagemaker", "comprehend", "rekognition", "textract"])
    has_analytics = any(s in services for s in ["kinesis", "glue", "athena", "emr", "redshift", "quicksight"])
    has_serverless = any(s in services for s in ["lambda", "apigateway", "dynamodb"])
    has_containers = any(s in services for s in ["ecs", "eks", "fargate"])
    has_realtime = any(s in services for s in ["kinesis", "msk", "eventbridge"])
    
    # Determine primary architecture pattern
    if has_ml and has_analytics:
        arch_pattern = "AI/ML Data Pipeline"
    elif has_analytics and has_realtime:
        arch_pattern = "Real-time Analytics Platform"
    elif has_serverless:
        arch_pattern = "Serverless Microservices"
    elif has_containers:
        arch_pattern = "Containerized Microservices"
    else:
        arch_pattern = "Cloud-Native Application"
    
    # Calculate cost estimate based on detected services
    base_cost = len(services) * 8.5  # Base cost per service
    cost_estimate = f"${base_cost:.0f}-{base_cost * 2.5:.0f}"
    
    # Generate service breakdown table
    service_details = []
    service_categories = {
        "Edge & CDN": ["route53", "cloudfront", "waf", "shield"],
        "API & Load Balancing": ["apigateway", "alb", "nlb"],
        "Authentication": ["cognito", "iam", "directory", "sso"],
        "Compute": ["lambda", "ec2", "ecs", "eks", "batch", "apprunner"],
        "Database": ["dynamodb", "rds", "redshift", "elasticache", "documentdb", "neptune"],
        "Storage": ["s3", "efs", "fsx", "ebs"],
        "Analytics": ["kinesis", "glue", "athena", "emr", "quicksight"],
        "Machine Learning": ["bedrock", "sagemaker", "comprehend", "rekognition", "textract"],
        "Messaging": ["sqs", "sns", "ses", "eventbridge", "mq"],
        "Security": ["kms", "secretsmanager", "guardduty", "inspector"],
        "Monitoring": ["cloudwatch", "xray", "cloudtrail"],
        "DevOps": ["codepipeline", "codebuild", "codecommit", "cloudformation"]
    }
    
    for category, service_list in service_categories.items():
        found_services = [s for s in service_list if s in services]
        if found_services:
            for service in found_services:
                service_name = service.replace("_", " ").title()
                service_details.append(f"| **{service_name}** | {category} | Core infrastructure component | 99.9%+ SLA |")
    
    if not service_details:
        service_details = [
            "| **API Gateway** | API & Load Balancing | Secure API entry point and routing | 99.95% SLA |",
            "| **Lambda** | Compute | Serverless business logic execution | Multi-AZ auto-scaling |",
            "| **DynamoDB** | Database | NoSQL database for high performance | 99.99% SLA |",
            "| **S3** | Storage | Object storage for assets and backups | 99.999999999% durability |"
        ]
    
    # Generate comprehensive documentation
    doc = f"""# AWS Cloud Architecture - {arch_pattern} Solution

## 1. Executive Summary

### Business Context
This architecture document presents a comprehensive **{arch_pattern}** solution designed to meet modern cloud application requirements. The system leverages AWS managed services to deliver a scalable, secure, and cost-effective platform that can handle enterprise-grade workloads while maintaining operational excellence.

### Architecture Overview
The solution implements a **multi-tier architecture** utilizing AWS best practices for security, scalability, and high availability. The design follows the **AWS Well-Architected Framework** across all five pillars: Operational Excellence, Security, Reliability, Performance Efficiency, and Cost Optimization.

### Input Requirements Analysis
> "{prompt_escaped}"

### Key Benefits
- **Scalability**: Auto-scaling capabilities handle traffic spikes from 100 to 100,000+ concurrent users
- **High Availability**: Multi-AZ deployment ensures 99.99% uptime SLA
- **Security**: Enterprise-grade security with encryption at rest and in transit
- **Cost Efficiency**: Pay-as-you-go model with optimized resource utilization
- **Performance**: Sub-100ms response times with global CDN distribution

---

## 2. Requirements Analysis

### 2.1 Functional Requirements
- **API Management**: RESTful API endpoints with authentication and authorization
- **Data Processing**: Real-time and batch data processing capabilities  
- **User Management**: Secure user registration, authentication, and profile management
- **Content Delivery**: Fast, globally distributed content and asset delivery
- **Data Persistence**: Reliable data storage with backup and recovery capabilities

### 2.2 Non-Functional Requirements
- **Performance**: < 100ms API response time, 1000+ RPS throughput capability
- **Availability**: 99.99% uptime with RTO < 1 hour, RPO < 15 minutes
- **Scalability**: Horizontal scaling to support 10x traffic growth
- **Security**: SOC 2 Type II compliance, data encryption, audit logging
- **Cost**: Target monthly operational cost under ${cost_estimate}/month at baseline load

---

## 3. Architecture Design Decisions

### 3.1 Architectural Patterns
- **Pattern**: {arch_pattern}
- **Rationale**: This pattern provides optimal balance of performance, scalability, and maintainability for the identified requirements
- **Trade-offs**: Prioritizes cloud-native services over traditional infrastructure for reduced operational overhead

### 3.2 Technology Stack Decisions
- **Compute Strategy**: Serverless-first approach with Lambda for event-driven workloads, containers for stateful services
- **Database Selection**: Multi-model approach using DynamoDB for high-performance operations, RDS for complex queries
- **Storage Strategy**: S3 with intelligent tiering for cost optimization and performance

---

## 4. AWS Services & Component Breakdown

| AWS Service | Category | Architectural Role | High Availability / SLA |
|-------------|----------|-------------------|------------------------|
{chr(10).join(service_details)}

---

## 5. Network Architecture & VPC Design

### 5.1 VPC Structure
```
Production VPC (10.0.0.0/16)
├── Public Subnet A (10.0.1.0/24) - us-east-1a
├── Public Subnet B (10.0.2.0/24) - us-east-1b  
├── Private Subnet A (10.0.10.0/24) - us-east-1a
├── Private Subnet B (10.0.20.0/24) - us-east-1b
├── Database Subnet A (10.0.100.0/24) - us-east-1a
└── Database Subnet B (10.0.200.0/24) - us-east-1b
```

### 5.2 Security Groups & Network ACLs
- **Web Tier**: HTTP/HTTPS (80, 443) from Internet Gateway
- **App Tier**: Internal communication on application ports
- **Database Tier**: Database ports only from application tier
- **Management**: SSH/RDP access restricted to bastion host

### 5.3 Connectivity Components
- **Internet Gateway**: Public internet access for web tier
- **NAT Gateway**: Outbound internet for private subnets (HA across AZs)
- **VPC Endpoints**: Private connectivity to AWS services (S3, DynamoDB)

---

## 6. Data Flow Architecture

### 6.1 Request Processing Flow
1. **Client Request**: User/application sends HTTPS request via browser or mobile app
2. **Edge Processing**: CloudFront CDN handles static content, WAF filters malicious requests  
3. **API Gateway**: Validates request, enforces rate limiting, routes to appropriate backend
4. **Authentication**: Cognito validates JWT tokens, IAM authorizes API access
5. **Business Logic**: Lambda functions execute core application logic with auto-scaling
6. **Data Layer**: DynamoDB handles high-frequency operations, RDS for complex queries
7. **Response**: JSON response cached at CDN edge locations for subsequent requests

### 6.2 Data Processing Pipeline
- **Ingestion**: Kinesis Data Streams capture real-time events and user interactions
- **Processing**: Lambda functions and Glue ETL jobs transform and enrich data
- **Storage**: Data Lake in S3 with lifecycle policies, analytics in Redshift/Athena
- **Visualization**: QuickSight dashboards for business intelligence and reporting

### 6.3 Integration Patterns
- **Synchronous**: API Gateway → Lambda → Database (real-time operations)
- **Asynchronous**: SNS/SQS messaging for decoupled microservices communication
- **Event-Driven**: EventBridge orchestrates cross-service workflows and notifications

---

## 7. Security Architecture

### 7.1 Identity & Access Management
- **User Authentication**: Cognito User Pools with MFA and social identity providers
- **Service Authorization**: IAM roles with least-privilege policies for all AWS services
- **API Security**: JWT token validation, API key management, request signing

### 7.2 Data Protection  
- **Encryption at Rest**: KMS-managed keys for S3, DynamoDB, RDS, and EBS volumes
- **Encryption in Transit**: TLS 1.3 for all API communications, SSL/SNI for web traffic
- **Key Management**: Automated key rotation, separate keys per environment and service

### 7.3 Network Security
- **Web Application Firewall**: AWS WAF with OWASP Top 10 rule sets and rate limiting
- **DDoS Protection**: AWS Shield Standard and Advanced with 24/7 DRT support  
- **Network Segmentation**: Security groups as distributed firewalls with deny-by-default

### 7.4 Monitoring & Compliance
- **Audit Logging**: CloudTrail captures all API calls across all AWS services
- **Threat Detection**: GuardDuty ML-powered threat intelligence and anomaly detection
- **Compliance**: Config rules validate resource configurations against security policies

---

## 8. Scalability & High Availability Design

### 8.1 Auto Scaling Configuration
- **Lambda**: Concurrent execution scaling from 0 to 10,000+ instances automatically
- **Database**: DynamoDB on-demand scaling, RDS read replicas for read-heavy workloads
- **Compute**: ECS/EKS horizontal pod autoscaling based on CPU and custom metrics

### 8.2 Multi-AZ Deployment Strategy  
- **Load Balancers**: Application Load Balancer distributes traffic across multiple AZs
- **Database**: RDS Multi-AZ deployment with synchronous replication and automated failover
- **Storage**: S3 automatically replicates objects across multiple facilities within a region

### 8.3 Disaster Recovery Plan
- **Backup Strategy**: Automated daily snapshots with 30-day retention, cross-region replication
- **Recovery Objectives**: RTO ≤ 1 hour, RPO ≤ 15 minutes for production workloads  
- **Failover Process**: Route 53 health checks enable automatic DNS failover to secondary region

---

## 9. Performance Optimization

### 9.1 Caching Strategy
- **CDN**: CloudFront global edge locations cache static and dynamic content
- **Database**: ElastiCache Redis cluster for session storage and frequently accessed data
- **Application**: In-memory caching within Lambda functions and container applications

### 9.2 Database Optimization
- **Indexing**: Global Secondary Indexes (GSI) on DynamoDB for efficient query patterns
- **Read Replicas**: RDS read replicas in multiple AZs for read scalability
- **Query Optimization**: Database query performance monitoring and automatic tuning

### 9.3 Monitoring & Alerting
- **Application Metrics**: Custom CloudWatch metrics for business KPIs and SLA tracking
- **Infrastructure Monitoring**: Enhanced monitoring for EC2, RDS, and Lambda performance
- **Distributed Tracing**: X-Ray integration for end-to-end request tracking and optimization

---

## 10. Cost Analysis & Optimization

### 10.1 Detailed Cost Breakdown (Monthly Estimates)

| Service Category | Configuration | Monthly Cost (USD) | Cost Drivers | Optimization Strategy |
|------------------|---------------|-------------------|--------------|----------------------|
| **Compute (Lambda)** | 10M invocations, 1GB RAM | $20.00 | Request volume, memory allocation | Right-size memory, optimize duration |
| **API Gateway** | 10M requests/month | $35.00 | API calls, data transfer | Consider ALB for high-volume APIs |  
| **Database (DynamoDB)** | On-demand, 1M RCU/WCU | $125.00 | Read/write capacity | Reserved capacity for predictable load |
| **Storage (S3)** | 1TB Standard, 10M requests | $25.00 | Storage volume, requests | Lifecycle policies, Intelligent Tiering |
| **CDN (CloudFront)** | 1TB data transfer | $85.00 | Data transfer, requests | Optimize caching policies, compression |
| **Monitoring** | CloudWatch, X-Ray | $15.00 | Log ingestion, trace volume | Log retention policies, sampling |
| **Security & Compliance** | WAF, GuardDuty, Config | $30.00 | Rule evaluations, findings | Optimize rule sets, suppress noise |
| **Networking** | NAT Gateway, data transfer | $45.00 | Data processing, transfer | VPC endpoints, traffic optimization |
| ****Total Baseline Cost**** | | **$380.00/month** | | **Potential 30-40% savings with optimization** |

### 10.2 Cost Optimization Strategies
- **Compute**: Reserved Instances for predictable EC2 workloads, Spot Instances for batch processing
- **Storage**: S3 Intelligent Tiering automatically moves data to optimal storage class
- **Database**: DynamoDB reserved capacity for consistent traffic patterns
- **Monitoring**: Log aggregation and retention policies to reduce CloudWatch costs

---

## 11. DevOps & CI/CD Strategy

### 11.1 Infrastructure as Code
```yaml
# AWS CDK Stack Definition (TypeScript)
export class ArchitectureStack extends Stack {{
  constructor(scope: Construct, id: string, props?: StackProps) {{
    super(scope, id, props);
    
    // VPC with public and private subnets
    const vpc = new ec2.Vpc(this, 'ProductionVPC', {{
      cidr: '10.0.0.0/16',
      maxAzs: 2,
      natGateways: 2
    }});
    
    // Application Load Balancer
    const alb = new elbv2.ApplicationLoadBalancer(this, 'ALB', {{
      vpc,
      internetFacing: true
    }});
  }}
}}
```

### 11.2 CI/CD Pipeline Design
```
CodeCommit → CodeBuild → CodeDeploy → Production
     ↓           ↓            ↓
   Source     Tests &     Blue/Green
  Control    Build       Deployment
```

- **Source Control**: CodeCommit Git repositories with branch protection rules
- **Build Process**: CodeBuild with automated testing, security scanning, and artifact generation
- **Deployment**: CodeDeploy blue/green deployments with automated rollback capabilities

### 11.3 Environment Management
- **Development**: Smaller instance types, single AZ deployment, reduced retention periods
- **Staging**: Production-like configuration for integration testing and performance validation
- **Production**: Full multi-AZ deployment with all security and monitoring capabilities enabled

---

## 12. Monitoring & Observability

### 12.1 Application Performance Monitoring
- **Metrics**: Response time, error rate, throughput, and business KPIs via CloudWatch
- **Logging**: Structured JSON logging with correlation IDs for distributed tracing
- **Alerting**: PagerDuty integration for critical alerts, Slack for informational notifications

### 12.2 Infrastructure Monitoring  
- **Systems Manager**: Patch management, configuration compliance, and operational insights
- **Config**: Resource configuration tracking and compliance validation
- **Trusted Advisor**: Cost optimization, security recommendations, and service limit monitoring

### 12.3 Security Monitoring
- **CloudTrail**: Complete audit trail of all AWS API calls and user activities
- **GuardDuty**: ML-powered threat detection for malicious activity and compromised instances
- **Security Hub**: Centralized security posture dashboard with compliance scoring

---

## 13. Implementation Roadmap

### 13.1 Phase 1: Foundation Infrastructure (Weeks 1-2)
- Deploy VPC, subnets, security groups, and networking components
- Set up IAM roles, policies, and initial security configurations
- Implement basic monitoring and alerting with CloudWatch

### 13.2 Phase 2: Core Application Services (Weeks 3-4)  
- Deploy API Gateway, Lambda functions, and database infrastructure
- Implement authentication with Cognito and integrate with application
- Set up CI/CD pipeline with automated testing and deployment

### 13.3 Phase 3: Advanced Features & Optimization (Weeks 5-6)
- Enable advanced monitoring with X-Ray distributed tracing
- Implement caching strategies and performance optimizations  
- Complete security hardening and compliance validation

---

## 14. Risk Assessment & Mitigation

### Technical Risks
- **Vendor Lock-in**: Mitigated by using standard APIs and containerized applications where possible
- **Service Limits**: Monitoring of service quotas with automated limit increase requests
- **Data Loss**: Multi-region backup strategy and point-in-time recovery capabilities

### Security Risks  
- **Data Breach**: Defense-in-depth with WAF, encryption, IAM, and monitoring
- **DDoS Attacks**: AWS Shield Advanced with dedicated response team support
- **Insider Threats**: Principle of least privilege, audit logging, and access reviews

### Operational Risks
- **Service Outages**: Multi-AZ deployment and disaster recovery procedures
- **Configuration Drift**: Infrastructure as Code with automated compliance checking
- **Skill Gaps**: Comprehensive documentation and AWS training for operations team

---

## 15. Infrastructure as Code - Production Ready Sample

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Production AWS Architecture - Core Infrastructure'

Parameters:
  Environment:
    Type: String
    Default: 'prod'
    AllowedValues: ['dev', 'staging', 'prod']

Resources:
  # VPC Configuration
  ProductionVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${{Environment}}-vpc'

  # API Gateway
  RestAPI:
    Type: AWS::ApiGateway::RestApi
    Properties:
      Name: !Sub '${{Environment}}-api'
      Description: 'Production REST API'
      EndpointConfiguration:
        Types:
          - REGIONAL

  # Lambda Function
  BackendFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub '${{Environment}}-backend'
      Runtime: python3.11
      Handler: index.handler
      Code:
        ZipFile: |
          def handler(event, context):
              return {{
                  'statusCode': 200,
                  'body': 'Architecture successfully deployed!'
              }}
      Environment:
        Variables:
          ENVIRONMENT: !Ref Environment
      
  # DynamoDB Table
  ApplicationTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${{Environment}}-data'
      BillingMode: ON_DEMAND
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
      KeySchema:
        - AttributeName: id
          KeyType: HASH
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true

Outputs:
  APIGatewayURL:
    Description: 'API Gateway endpoint URL'
    Value: !Sub 'https://${{RestAPI}}.execute-api.${{AWS::Region}}.amazonaws.com/${{Environment}}'
    Export:
      Name: !Sub '${{Environment}}-api-url'
```

---

## Conclusion

This comprehensive AWS architecture provides a robust, scalable, and secure foundation for modern cloud applications. The design follows AWS best practices and the Well-Architected Framework to ensure operational excellence, security, reliability, performance efficiency, and cost optimization.

The modular approach allows for iterative deployment and continuous improvement, while the comprehensive monitoring and automation capabilities enable efficient operations at scale. This architecture can support growth from startup to enterprise scale while maintaining security and compliance requirements.

**Next Steps:**
1. Review and approve architecture design
2. Set up AWS accounts and initial security configurations  
3. Deploy Phase 1 infrastructure using provided CloudFormation templates
4. Begin application development and integration testing
5. Implement monitoring and alerting before production deployment

*Generated by AI AWS Architecture & Documentation Generator - Enterprise Edition*"""
    
    return doc

# Helper Function: Generate PDF
class ArchitecturePDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(255, 153, 0)  # AWS Orange
        self.cell(self.epw, 8, "AWS Architecture & Technical Report", border=False, new_x="LMARGIN", new_y="NEXT", align="R")
        self.set_draw_color(230, 230, 230)
        self.line(10, 14, 200, 14)
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(230, 230, 230)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(self.epw / 2, 10, "Generated by AI AWS Architecture & Documentation Generator", align="L")
        self.set_x(self.l_margin)
        self.cell(self.epw, 10, f"Page {self.page_no()}", align="R")


def _clean(text):
    """Encode text safely for the core Helvetica font set."""
    return text.encode("latin-1", "replace").decode("latin-1")


def _ensure_space(pdf, min_space_mm):
    """Force a page break now if less than min_space_mm remains before the
    bottom margin, so headings never get orphaned from their content."""
    remaining = pdf.page_break_trigger - pdf.get_y()
    if remaining < min_space_mm:
        pdf.add_page()


def _render_inline(pdf, text, size=10, color=(40, 40, 40), line_h=5.2):
    """
    Render a line of text, honoring **bold** spans and `code` spans inline,
    wrapping naturally via multiple cell() calls joined on one visual line.
    """
    text = _clean(text)
    tokens = re.split(r"(\*\*.*?\*\*|`.*?`)", text)
    pdf.set_text_color(*color)
    for i, tok in enumerate(tokens):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            pdf.set_font("Helvetica", "B", size)
            pdf.write(line_h, tok[2:-2])
        elif tok.startswith("`") and tok.endswith("`"):
            pdf.set_font("Courier", "", size - 0.5)
            pdf.set_fill_color(240, 240, 240)
            pdf.write(line_h, tok[1:-1])
        else:
            pdf.set_font("Helvetica", "", size)
            pdf.write(line_h, tok)
    pdf.ln(line_h)


def _draw_table_row(pdf, cells, col_width, font_style, font_size, text_color, fill_color, line_h=5.0, pad=1.5):
    """Draw one table row with per-cell text wrapping and a uniform row height."""
    pdf.set_font("Helvetica", font_style, font_size)
    # Determine how many wrapped lines each cell needs, so the whole row shares one height.
    line_counts = []
    for cell in cells:
        lines = pdf.multi_cell(col_width - 2 * pad, line_h, cell, dry_run=True, output="LINES")
        line_counts.append(max(1, len(lines)))
    row_h = max(line_counts) * line_h + 2 * pad

    # Page-break safety: never split a single row across two pages.
    if pdf.get_y() + row_h > pdf.page_break_trigger:
        pdf.add_page()

    x_start = pdf.get_x()
    y_start = pdf.get_y()
    pdf.set_fill_color(*fill_color)
    pdf.set_text_color(*text_color)

    for idx, cell in enumerate(cells):
        x = x_start + idx * col_width
        pdf.rect(x, y_start, col_width, row_h, style="DF" if fill_color else "D")
        pdf.set_xy(x + pad, y_start + pad)
        pdf.multi_cell(col_width - 2 * pad, line_h, cell, border=0, align="C")

    pdf.set_xy(x_start, y_start + row_h)


def _render_table(pdf, rows):
    """Render a GitHub-style markdown table (header + separator + rows) as a bordered grid
    with per-cell text wrapping so long content never overlaps adjacent columns."""
    if len(rows) < 2:
        return
    headers = [_clean(c.strip().replace("**", "")) for c in rows[0].strip("|").split("|")]
    data_rows = [r for r in rows[2:] if r.strip()]
    col_count = len(headers)
    col_width = pdf.epw / col_count

    pdf.set_draw_color(220, 220, 220)
    _draw_table_row(pdf, headers, col_width, "B", 9, (255, 255, 255), (255, 153, 0))

    fill = False
    for row in data_rows:
        cells = [_clean(c.strip().replace("**", "")) for c in row.strip("|").split("|")]
        if len(cells) != col_count:
            continue
        is_total_row = any("Total" in c for c in cells)
        font_style = "B" if is_total_row else ""
        fill_color = (255, 240, 214) if is_total_row else ((248, 249, 250) if fill else (255, 255, 255))
        _draw_table_row(pdf, cells, col_width, font_style, 9, (40, 40, 40), fill_color)
        fill = not fill
    pdf.ln(4)


def _render_code_block(pdf, code_lines):
    """Render a fenced code block in a shaded, monospaced box, wrapping long lines
    so content never runs past the page margin."""
    pad = 3
    line_h = 4.6
    box_w = pdf.epw
    inner_w = box_w - 2 * pad
    pdf.set_font("Courier", "", 8.5)

    # Pre-compute wrapped line count to size the box before drawing (avoids mid-box breaks).
    wrapped_lines = []
    for line in code_lines:
        text = _clean(line) if line.strip() else " "
        wrapped = pdf.multi_cell(inner_w, line_h, text, dry_run=True, output="LINES")
        wrapped_lines.extend(wrapped if wrapped else [" "])

    box_h = max(line_h, len(wrapped_lines) * line_h + 2 * pad)

    # Page-break safety: start a new page if the box won't fit in the remaining space.
    if pdf.get_y() + box_h > pdf.page_break_trigger:
        pdf.add_page()

    x0 = pdf.l_margin
    y0 = pdf.get_y()

    pdf.set_fill_color(245, 246, 248)
    pdf.set_draw_color(220, 220, 220)
    pdf.rect(x0, y0, box_w, box_h, style="DF")

    pdf.set_text_color(50, 50, 50)
    pdf.set_xy(x0 + pad, y0 + pad)
    for text_line in wrapped_lines:
        pdf.set_x(x0 + pad)
        pdf.cell(inner_w, line_h, text_line, new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(x0, y0 + box_h)
    pdf.ln(4)


def render_markdown_to_pdf(pdf, markdown_text):
    lines = markdown_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            _render_code_block(pdf, code_lines)
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?[\s:|-]+\|?$", lines[i + 1].strip()):
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_rows.append(lines[i].strip())
                i += 1
            _ensure_space(pdf, 20)
            _render_table(pdf, table_rows)
            continue

        if stripped.startswith("# "):
            i += 1
            continue
        elif stripped.startswith("## "):
            # Keep headings attached to their following content: force a page
            # break now rather than let the heading render as an orphan at the
            # bottom of the page with its content pushed to the next page.
            _ensure_space(pdf, 28)
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(255, 153, 0)
            pdf.cell(pdf.epw, 8, _clean(stripped[3:]), new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(255, 153, 0)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 30, pdf.get_y())
            pdf.ln(3)
        elif stripped.startswith("### "):
            _ensure_space(pdf, 22)
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(35, 47, 62)
            pdf.cell(pdf.epw, 7, _clean(stripped[4:]), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_x(pdf.l_margin + 4)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(255, 153, 0)
            pdf.cell(5, 5.2, "-")
            pdf.set_x(pdf.l_margin + 9)
            _render_inline(pdf, stripped[2:])
        elif re.match(r"^\d+\.\s", stripped):
            num, rest = stripped.split(".", 1)
            pdf.set_x(pdf.l_margin + 4)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(255, 153, 0)
            pdf.cell(7, 5.2, f"{num}.")
            pdf.set_x(pdf.l_margin + 11)
            _render_inline(pdf, rest.strip())
        elif stripped == "---":
            pdf.ln(2)
            pdf.set_draw_color(230, 230, 230)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pdf.epw, pdf.get_y())
            pdf.ln(4)
        elif stripped == "":
            pdf.ln(2)
        else:
            pdf.set_x(pdf.l_margin)
            _render_inline(pdf, stripped)
        i += 1


def _sanitize_filename(name, fallback="AWS_Architecture_Report"):
    """Strip characters that aren't safe in a filename, keeping it usable across OSes."""
    name = (name or "").strip()
    name = re.sub(r'[\\/:*?"<>|]+', "", name)
    name = re.sub(r"\s+", "_", name)
    return name or fallback


# ---------------------------------------------------------------------------
# Mermaid / Draw.io diagram helpers
# ---------------------------------------------------------------------------

# Comprehensive service metadata for Mermaid diagrams - supports 70+ AWS services
MERMAID_SERVICE_META = {
    # Edge & Network Services
    "route53":        ("Route 53 DNS",           "Edge"),
    "cloudfront":     ("CloudFront CDN",         "Edge"),
    "waf":            ("AWS WAF",                "Edge"),
    "shield":         ("AWS Shield",             "Edge"),
    "globalaccelerator": ("Global Accelerator", "Edge"),
    
    # Load Balancers & API
    "alb":            ("Application Load Balancer", "API Gateway"),
    "nlb":            ("Network Load Balancer",     "API Gateway"),
    "apigateway":     ("API Gateway",               "API Gateway"),
    "appmesh":        ("App Mesh",                  "API Gateway"),
    
    # Authentication & Authorization
    "cognito":        ("Cognito Auth",           "Authentication"),
    "iam":            ("IAM",                    "Authentication"),
    "directory":      ("Directory Service",      "Authentication"),
    "sso":            ("AWS SSO",                "Authentication"),
    
    # Compute Services
    "lambda":         ("Lambda Functions",       "Compute"),
    "ec2":            ("EC2 Instances",          "Compute"),
    "ecs":            ("ECS Fargate",            "Compute"),
    "eks":            ("EKS Cluster",            "Compute"),
    "batch":          ("AWS Batch",              "Compute"),
    "lightsail":      ("Lightsail VPS",          "Compute"),
    "outposts":       ("AWS Outposts",           "Compute"),
    "apprunner":      ("App Runner",             "Compute"),
    
    # Orchestration
    "stepfunctions":  ("Step Functions",         "Orchestration"),
    "eventbridge":    ("EventBridge",            "Orchestration"),
    "swf":            ("Simple Workflow",        "Orchestration"),
    
    # Database Services
    "dynamodb":       ("DynamoDB NoSQL",         "Database"),
    "rds":            ("RDS Aurora",             "Database"),
    "redshift":       ("Redshift Warehouse",     "Database"),
    "elasticache":    ("ElastiCache Redis",      "Database"),
    "documentdb":     ("DocumentDB",             "Database"),
    "neptune":        ("Neptune Graph DB",       "Database"),
    "timestream":     ("Timestream",             "Database"),
    "keyspaces":      ("Keyspaces Cassandra",    "Database"),
    "qldb":           ("QLDB Ledger",            "Database"),
    "opensearch":     ("OpenSearch",             "Database"),
    
    # Storage Services
    "s3":             ("S3 Object Storage",      "Storage"),
    "efs":            ("EFS Network Storage",    "Storage"),
    "fsx":            ("FSx File Systems",       "Storage"),
    "ebs":            ("EBS Block Storage",      "Storage"),
    "storagegw":      ("Storage Gateway",        "Storage"),
    
    # Analytics & Big Data
    "kinesis":        ("Kinesis Streams",        "Analytics"),
    "glue":           ("Glue ETL",               "Analytics"),
    "athena":         ("Athena Queries",         "Analytics"),
    "emr":            ("EMR Hadoop",             "Analytics"),
    "databrew":       ("DataBrew",               "Analytics"),
    "lake":           ("Lake Formation",         "Analytics"),
    "msk":            ("MSK Kafka",              "Analytics"),
    "quicksight":     ("QuickSight BI",          "Analytics"),
    
    # Machine Learning & AI
    "sagemaker":      ("SageMaker ML",           "Machine Learning"),
    "bedrock":        ("Bedrock LLMs",           "Machine Learning"),
    "comprehend":     ("Comprehend NLP",         "Machine Learning"),
    "rekognition":    ("Rekognition Vision",     "Machine Learning"),
    "textract":       ("Textract OCR",           "Machine Learning"),
    "translate":      ("Translate",              "Machine Learning"),
    "polly":          ("Polly TTS",              "Machine Learning"),
    "transcribe":     ("Transcribe STT",         "Machine Learning"),
    "lex":            ("Lex Chatbot",            "Machine Learning"),
    "personalize":    ("Personalize",            "Machine Learning"),
    "forecast":       ("Forecast",               "Machine Learning"),
    
    # Messaging & Communication
    "sqs":            ("SQS Queue",              "Messaging"),
    "sns":            ("SNS Topics",             "Messaging"),
    "ses":            ("SES Email",              "Messaging"),
    "pinpoint":       ("Pinpoint Marketing",     "Messaging"),
    "chime":          ("Chime Meetings",         "Messaging"),
    "mq":             ("Amazon MQ",              "Messaging"),
    "appflow":        ("AppFlow Integration",    "Messaging"),
    
    # Security Services
    "kms":            ("KMS Encryption",         "Security"),
    "secretsmanager": ("Secrets Manager",        "Security"),
    "hsm":            ("CloudHSM",               "Security"),
    "acm":            ("Certificate Manager",    "Security"),
    "inspector":      ("Inspector Security",     "Security"),
    "guardduty":      ("GuardDuty Threat Detection", "Security"),
    "macie":          ("Macie Data Discovery",   "Security"),
    "config":         ("Config Compliance",      "Security"),
    "cloudtrail":     ("CloudTrail Audit",       "Security"),
    "securityhub":    ("Security Hub",           "Security"),
    
    # Monitoring & Management
    "cloudwatch":     ("CloudWatch Monitoring", "Observability"),
    "xray":           ("X-Ray Tracing",          "Observability"),
    "systems":        ("Systems Manager",        "Management"),
    "cloudformation": ("CloudFormation IaC",     "Management"),
    "cdk":            ("AWS CDK",                "Management"),
    "opsworks":       ("OpsWorks",               "Management"),
    
    # Developer Tools
    "codecommit":     ("CodeCommit Git",         "DevOps"),
    "codebuild":      ("CodeBuild CI",           "DevOps"),
    "codedeploy":     ("CodeDeploy CD",          "DevOps"),
    "codepipeline":   ("CodePipeline",           "DevOps"),
    "cloud9":         ("Cloud9 IDE",             "DevOps"),
    "codecatalyst":   ("CodeCatalyst",           "DevOps"),
    
    # Media & Content
    "mediaconvert":   ("MediaConvert",           "Media"),
    "mediastore":     ("MediaStore",             "Media"),
    "medialive":      ("MediaLive",              "Media"),
    
    # IoT Services
    "iot":            ("IoT Core",               "IoT"),
    "greengrass":     ("IoT Greengrass",         "IoT"),
    
    # Specialized Services
    "gamelift":       ("GameLift",               "Gaming"),
    "managedblockchain": ("Managed Blockchain", "Blockchain"),
    "groundstation":  ("Ground Station",         "Satellite"),
    "braket":         ("Braket Quantum",         "Quantum"),
    "robomaker":      ("RoboMaker",              "Robotics"),
}

# Updated tier order for better Mermaid diagram flow
MERMAID_TIER_ORDER = [
    "Edge", "API Gateway", "Authentication", "Compute", "Orchestration", 
    "Database", "Storage", "Analytics", "Machine Learning", "Messaging", 
    "Security", "Observability", "Management", "DevOps", "Media", "IoT", 
    "Gaming", "Blockchain", "Satellite", "Quantum", "Robotics"
]


def generate_mermaid_smart(services_found):
    """Build a Mermaid flowchart from detected services, grouped by tier."""
    if not services_found:
        services_found = ["apigateway", "lambda", "dynamodb", "s3"]

    tiers = {}
    for key in services_found:
        if key in MERMAID_SERVICE_META:
            label, tier = MERMAID_SERVICE_META[key]
            tiers.setdefault(tier, []).append((key, label))

    lines = ["graph LR"]

    # Build subgraphs
    for tier in MERMAID_TIER_ORDER:
        if tier not in tiers:
            continue
        lines.append(f"    subgraph {tier} Tier")
        for key, label in tiers[tier]:
            safe_id = key.upper()
            lines.append(f"        {safe_id}[{label}]")
        lines.append("    end")

    # Connect tiers in order
    prev_keys = []
    for tier in MERMAID_TIER_ORDER:
        if tier not in tiers:
            continue
        curr_keys = [k.upper() for k, _ in tiers[tier]]
        if prev_keys:
            for p in prev_keys:
                for c in curr_keys:
                    lines.append(f"    {p} --> {c}")
        prev_keys = curr_keys

    return _sanitize_mermaid("\n".join(lines))


def _sanitize_mermaid(text):
    """
    Clean up Mermaid code returned by the model so it renders without syntax errors.

    Fixes applied line-by-line:
    1. Strip markdown fences (```mermaid / ```)
    2. Discard any prose before the graph directive
    3. Force-quote ALL node labels — even ones without special characters —
       so slashes, parentheses, colons, CIDRs like 10.0.1.0/24, paths like /api/*
       never break the Mermaid parser
    4. Sanitize node IDs: replace spaces and illegal chars with underscores
    5. Collapse blank lines
    """
    # 1. Strip fences
    text = re.sub(r"```mermaid", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text).strip()

    # 2. Discard everything before the graph/flowchart directive
    match = re.search(r"((?:graph|flowchart)\s+(?:LR|TD|TB|RL|BT).+)", text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1).strip()

    # 3. Process line by line
    clean_lines = []
    for line in text.splitlines():
        line = _fix_mermaid_line(line)
        clean_lines.append(line)

    # 4. Collapse excess blank lines
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(clean_lines)).strip()
    return result


def _fix_mermaid_line(line):
    """
    Fix a single Mermaid line:
    - Sanitize node IDs (no spaces/special chars)
    - Force double-quote all node labels (so /api/*, 10.0.1.0/24, (parens) never break parser)
    - Leave subgraph, end, graph, %% comment lines and arrows untouched
    """
    stripped = line.strip()

    # Leave directive lines, subgraph/end, comments, and blank lines alone
    if (not stripped
            or stripped.lower().startswith("graph ")
            or stripped.lower().startswith("flowchart ")
            or stripped.lower().startswith("subgraph")
            or stripped.lower() == "end"
            or stripped.startswith("%%")):
        return line

    # Fix arrow lines: nodeA --> nodeB  (no labels on these — just clean IDs)
    # We only fix node definitions that have bracket labels
    # Pattern: nodeID[label]  nodeID["label"]  nodeID[(label)]  nodeID{{label}}
    def fix_node_def(m):
        raw_id    = m.group(1)
        open_br   = m.group(2)   # [  [(  {{  >  etc.
        raw_label = m.group(3)
        close_br  = m.group(4)   # ]  )]  }}  etc.

        # Sanitize node ID: replace anything not alphanumeric/underscore with _
        clean_id = re.sub(r'[^a-zA-Z0-9_]', '_', raw_id)
        clean_id = re.sub(r'_+', '_', clean_id).strip('_') or "node"

        # Strip existing quotes from label, we'll re-add them uniformly
        label = raw_label.strip().strip('"').strip("'")

        # Always wrap label in double quotes — safe for ALL content
        return f'{clean_id}{open_br}"{label}"{close_br}'

    # Match node definitions: word chars followed by brackets containing a label
    # Handles: id[label], id["label"], id[(label)], id{{label}}, id>label]
    line = re.sub(
        r'([\w][\w\-\.]*)\s*(\[{1,2}|\{{2}|>)\s*([^\]\}]+?)\s*(\]{1,2}|\}{2}|])',
        fix_node_def,
        line
    )

    return line


def generate_mermaid_bedrock(prompt, model_id, region):
    """Ask Bedrock to generate valid Mermaid flowchart code for the given requirement."""
    mermaid_prompt = (
        "You are a Senior AWS Solutions Architect.\n\n"
        "IMPORTANT: The input may contain assignment rubrics, test cases, intern tasks, deliverables, "
        "or non-architectural content. IGNORE all of that. Focus ONLY on the AWS services and data flows "
        "described to extract the architecture.\n\n"
        "Generate ONLY valid Mermaid.js flowchart code (no explanation, no markdown fences).\n\n"
        "STRICT SYNTAX RULES (violations cause render errors — follow exactly):\n"
        "1. Start with: graph LR\n"
        "2. Node IDs must be simple alphanumeric strings with underscores only — NO spaces, slashes, "
        "parentheses, brackets, or colons (e.g. edge_cf, alb1, ec2_fleet, rds_db).\n"
        "3. ALL node display labels MUST be wrapped in double quotes:\n"
        '   Correct:   edge_cf["CloudFront CDN"]\n'
        '   Correct:   api1["API Gateway (/api/*)"]\n'
        '   Correct:   sub1["Public Subnet (10.0.1.0/24)"]\n'
        "   Wrong:     CloudFront[CloudFront CDN]\n"
        "   Wrong:     api1[API Gateway (/api/*)]\n"
        "4. Use only simple arrows: -->\n"
        "5. Group services into subgraph blocks matching the tiers present "
        "(e.g. Edge Tier, Frontend, Ingress & Compute, Data Tier, DevOps & Ops).\n"
        "6. Subgraph names may contain spaces and special characters — only node IDs must be clean.\n"
        "7. Include EVERY AWS service mentioned in the architecture.\n"
        "8. Output ONLY the raw Mermaid code, nothing else — no explanation, no fences.\n\n"
        f"Requirement:\n{prompt}"
    )
    try:
        kwargs = {"region_name": region}
        try:
            secrets = st.secrets.get("aws", {})
            if secrets.get("AWS_ACCESS_KEY_ID") and secrets.get("AWS_SECRET_ACCESS_KEY"):
                kwargs["aws_access_key_id"]     = secrets["AWS_ACCESS_KEY_ID"]
                kwargs["aws_secret_access_key"] = secrets["AWS_SECRET_ACCESS_KEY"]
                if secrets.get("AWS_DEFAULT_REGION"):
                    kwargs["region_name"] = secrets["AWS_DEFAULT_REGION"]
        except Exception:
            pass
        client = boto3.client("bedrock-runtime", **kwargs)
        if "claude" in model_id:
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,
                "messages": [{"role": "user", "content": mermaid_prompt}]
            }
            response = client.invoke_model(modelId=model_id, body=json.dumps(payload))
            text = json.loads(response["body"].read().decode())["content"][0]["text"]
        elif "nova" in model_id:
            payload = {
                "messages": [{"role": "user", "content": [{"text": mermaid_prompt}]}],
                "inferenceConfig": {"maxTokens": 2048}
            }
            response = client.invoke_model(modelId=model_id, body=json.dumps(payload))
            text = json.loads(response["body"].read().decode())["output"]["message"]["content"][0]["text"]
        else:
            return None

        return _sanitize_mermaid(text)
    except Exception:
        return None


def render_mermaid(mermaid_code):
    """Render a Mermaid diagram live in the browser via streamlit.components.v1.html."""
    escaped = mermaid_code.replace("`", "&#96;").replace("</", "<\\/")
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{ margin: 0; padding: 12px; font-family: sans-serif; background: #ffffff; }}
        .mermaid {{ text-align: center; }}
        svg {{ max-width: 100%; height: auto; }}
      </style>
    </head>
    <body>
      <div class="mermaid">
{mermaid_code}
      </div>
      <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{
          startOnLoad: true,
          theme: 'neutral',
          flowchart: {{ curve: 'basis', padding: 20 }}
        }});
      </script>
    </body>
    </html>
    """
    components.html(html, height=500, scrolling=True)


def create_pdf_report(prompt_text, doc_markdown, image_path):
    pdf = ArchitecturePDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # --- Cover title block ---
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(35, 47, 62)
    pdf.cell(pdf.epw, 12, "AWS Architecture Report", new_x="LMARGIN", new_y="NEXT")

    pdf.set_draw_color(255, 153, 0)
    pdf.set_line_width(0.8)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 40, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(4)

    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    prompt_preview = prompt_text if len(prompt_text) <= 300 else prompt_text[:300] + "..."
    pdf.multi_cell(pdf.epw, 5, _clean(f'Generated based on prompt: "{prompt_preview}"'))
    pdf.ln(6)

    # --- Diagram section ---
    if image_path and os.path.exists(image_path):
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(255, 153, 0)
        pdf.cell(pdf.epw, 9, "Visual Architecture Diagram", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(255, 153, 0)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 30, pdf.get_y())
        pdf.ln(4)

        try:
            img = Image.open(image_path)
            img_w, img_h = img.size
            display_w = pdf.epw
            display_h = display_w * (img_h / img_w)
            max_h = 110
            if display_h > max_h:
                display_h = max_h
                display_w = display_h * (img_w / img_h)
            x_offset = pdf.l_margin + (pdf.epw - display_w) / 2

            pdf.set_draw_color(220, 220, 220)
            pdf.rect(x_offset - 2, pdf.get_y() - 2, display_w + 4, display_h + 4)
            pdf.image(image_path, x=x_offset, w=display_w, h=display_h)
            pdf.ln(display_h + 8)
        except Exception as e:
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(pdf.epw, 8, _clean(f"[Diagram image omitted: {e}]"), new_x="LMARGIN", new_y="NEXT")

        pdf.add_page()

    # --- Documentation section ---
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(255, 153, 0)
    pdf.cell(pdf.epw, 9, "Architecture Documentation", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(255, 153, 0)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 30, pdf.get_y())
    pdf.ln(5)

    render_markdown_to_pdf(pdf, doc_markdown)

    pdf_filename = os.path.join(tempfile.gettempdir(), "aws_architecture_report.pdf")
    pdf.output(pdf_filename)
    return pdf_filename

# ── Hero Banner ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
  <div class="hero-badge">⚡ Powered by Amazon Bedrock Claude & 70+ AWS Services</div>
  <div class="hero-title">☁️ Enterprise AWS Architecture Generator</div>
  <div class="hero-subtitle">Transform complex requirements into ChatGPT-quality AWS diagrams, 
  comprehensive technical documentation, and production-ready infrastructure code — delivering 
  enterprise-grade architecture reports in seconds.</div>
</div>
""", unsafe_allow_html=True)

# ── 1-Click Preset Buttons ────────────────────────────────────────────────────
st.markdown("##### 💡 Quick-Start Presets")
p_col1, p_col2, p_col3 = st.columns(3)

PRESET_ECOMMERCE = (
    "Design a comprehensive serverless e-commerce platform with microservices architecture. "
    "Customers browse products via CloudFront-cached React frontend hosted on S3. Product searches "
    "use Amazon OpenSearch Service. User authentication through Cognito User Pools with social logins. "
    "Shopping cart state stored in DynamoDB with ElastiCache Redis for session management. "
    "Order processing workflow orchestrated by Step Functions: API Gateway → Lambda validates payments via Stripe, "
    "stores orders in DynamoDB, generates PDF receipts using Lambda layers, uploads to S3, "
    "sends confirmations via SES, and triggers inventory updates via EventBridge. "
    "Real-time order tracking using Kinesis Data Streams. ML-powered product recommendations via SageMaker. "
    "CI/CD pipeline with CodeCommit → CodeBuild → CodeDeploy. Monitor with CloudWatch and X-Ray distributed tracing."
)

PRESET_RAG = (
    "Build an enterprise-grade Generative AI Retrieval-Augmented Generation (RAG) architecture for intelligent document analysis. "
    "Documents uploaded via secure API Gateway with Cognito authentication flow into S3 data lake. "
    "Lambda functions trigger AWS Textract for OCR, Comprehend for entity extraction, and store embeddings in OpenSearch Serverless. "
    "User queries processed by API Gateway → Lambda → retrieve relevant context from OpenSearch vector database, "
    "augment prompts with retrieved documents, send to Amazon Bedrock Claude/Nova models for generation. "
    "Conversation history tracked in DynamoDB with ElastiCache for fast retrieval. "
    "Real-time chat interface via WebSocket API Gateway connections. SageMaker endpoints for custom embedding models. "
    "GuardDuty for security, CloudTrail for audit logging, CloudWatch for monitoring token usage and costs. "
    "Multi-region deployment with Route 53 health checks and automated failover."
)

PRESET_ANALYTICS = (
    "Design a real-time clickstream analytics and machine learning pipeline for e-commerce personalization. "
    "Mobile and web applications stream user events (page views, clicks, purchases, cart abandons) to Amazon Kinesis Data Streams. "
    "Real-time Lambda functions process events for immediate fraud detection using SageMaker endpoints. "
    "Kinesis Data Firehose delivers raw clickstream to S3 Data Lake partitioned by date/hour. "
    "AWS Glue Catalog automatically discovers schema and creates tables. Glue ETL jobs run nightly to clean data, "
    "calculate user segments, and prepare ML features. Amazon Athena enables ad-hoc SQL queries on the data lake. "
    "ML pipeline: SageMaker processes historical data to train recommendation models, deploys to real-time endpoints. "
    "Amazon Redshift Serverless for complex analytics and reporting. QuickSight dashboards for business intelligence. "
    "EventBridge orchestrates pipeline scheduling. SNS alerts for job failures. CloudWatch monitors all components. "
    "Real-time recommendations served via DynamoDB for sub-10ms latency. ElastiCache Redis for user session caching."
)

if p_col1.button("🛒 Serverless E-Commerce", use_container_width=True):
    st.session_state["preset_prompt"] = PRESET_ECOMMERCE
if p_col2.button("🤖 GenAI RAG Pipeline", use_container_width=True):
    st.session_state["preset_prompt"] = PRESET_RAG
if p_col3.button("📊 Real-Time Analytics", use_container_width=True):
    st.session_state["preset_prompt"] = PRESET_ANALYTICS

# ── Input Area ────────────────────────────────────────────────────────────────
input_type = st.radio(
    "Select Input Mode",
    ["Project Idea / Requirements", "Code / IaC Snippet"],
    horizontal=True
)

_default_text = st.session_state.get(
    "preset_prompt",
    "I need a scalable web application with an API Gateway, Lambda backend, DynamoDB database, and S3 for static assets."
)
if input_type == "Code / IaC Snippet" and "preset_prompt" not in st.session_state:
    _default_text = 'provider "aws" {\n  region = "us-east-1"\n}\n\nresource "aws_s3_bucket" "b" {}\nresource "aws_lambda_function" "f" {}\nresource "aws_dynamodb_table" "d" {}'

user_input = st.text_area("Architecture Input Prompt / Source Code", value=_default_text, height=140)

if st.button("🚀 Generate Architecture & Documentation"):
    if not user_input.strip():
        st.warning("Please enter a valid project prompt or code snippet.")
    else:
        with st.spinner("Analyzing requirements & generating AWS architecture..."):
            # Remove diagram PNGs from previous runs so they don't accumulate on disk.
            for old_file in glob.glob("aws_architecture_*.png"):
                try:
                    os.remove(old_file)
                except OSError:
                    pass

            detected_services = detect_services(user_input)
            # Use a unique filename per generation (instead of a fixed name) so each
            # run produces its own file on disk and there's no ambiguity about
            # whether the displayed image is stale vs. freshly generated.
            unique_diagram_name = f"aws_architecture_{uuid.uuid4().hex[:8]}"
            img_path = generate_diagram(detected_services, filename=unique_diagram_name)
            
            doc_markdown = None
            if "Bedrock" in ai_engine:
                doc_markdown = generate_documentation_bedrock(
                    user_input, bedrock_model, aws_region
                )

            if not doc_markdown:
                doc_markdown = generate_documentation_smart(user_input, detected_services)

            # Generate Mermaid diagram code (live interactive view + Draw.io export)
            mermaid_code = None
            if "Bedrock" in ai_engine:
                mermaid_code = generate_mermaid_bedrock(user_input, bedrock_model, aws_region)
            if not mermaid_code:
                mermaid_code = generate_mermaid_smart(detected_services)

            st.session_state["doc_markdown"] = doc_markdown
            st.session_state["img_path"] = img_path
            st.session_state["user_input"] = user_input
            st.session_state["mermaid_code"] = mermaid_code
            st.success("Architecture successfully generated!")


if "doc_markdown" in st.session_state:
    st.divider()

    # ── Filename input ────────────────────────────────────────────────────────
    base_name = st.text_input(
        "📁 File name for downloads",
        value="AWS_Architecture_Report",
        help="Base name used for PNG, Markdown, and PDF downloads."
    )
    base_name = _sanitize_filename(base_name)

    # ── Metrics bar ───────────────────────────────────────────────────────────
    detected = detect_services(st.session_state.get("user_input", ""))
    svc_count = max(len(detected), 1)
    # Simple heuristic cost tier based on service count
    cost_tier = "< $5/mo" if svc_count <= 3 else ("< $15/mo" if svc_count <= 6 else "< $50/mo")

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-value">{svc_count}</div><div class="metric-label">AWS Services</div></div>', unsafe_allow_html=True)
    m2.markdown('<div class="metric-card"><div class="metric-value">98/100</div><div class="metric-label">Security Score</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-value">{cost_tier}</div><div class="metric-label">Est. Monthly Cost</div></div>', unsafe_allow_html=True)
    m4.markdown('<div class="metric-card"><div class="metric-value">Multi-AZ</div><div class="metric-label">HA Architecture</div></div>', unsafe_allow_html=True)

    st.write("")

    # ── Tabbed results ────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Interactive Diagram (Draw.io)",
        "🖼️ AWS Icons Diagram (PNG)",
        "📄 Architecture Specification",
        "📥 Export & Download"
    ])

    mermaid_code = st.session_state.get("mermaid_code", "")
    img_p        = st.session_state.get("img_path")
    doc_md       = st.session_state["doc_markdown"]

    with tab1:
        st.subheader("Live Interactive Draw.io / Mermaid Diagram")
        if mermaid_code:
            render_mermaid(mermaid_code)
            with st.expander("📋 Copy code for Draw.io / edit mode"):
                st.code(mermaid_code, language="text")
                st.caption(
                    "To edit in Draw.io: open **app.diagrams.net** → Extras → Edit Diagram "
                    "→ select **Mermaid** tab → paste the code above."
                )
        else:
            st.info("No Mermaid code available for this run.")

    with tab2:
        st.subheader("Official AWS Architecture Diagram")
        if img_p and os.path.exists(img_p):
            st.image(img_p, caption="AWS Cloud Architecture", width="stretch")
        else:
            st.warning("PNG diagram could not be rendered. Make sure Graphviz is installed.")

    with tab3:
        st.subheader("Architecture Specification")
        st.markdown(doc_md)

    with tab4:
        st.subheader("Export Architecture Artifacts")
        pdf_path = create_pdf_report(
            st.session_state["user_input"],
            doc_md,
            img_p
        )

        dl1, dl2, dl3 = st.columns(3)

        if img_p and os.path.exists(img_p):
            with open(img_p, "rb") as img_f:
                dl1.download_button(
                    label="📥 Download Diagram (PNG)",
                    data=img_f,
                    file_name=f"{base_name}.png",
                    mime="image/png",
                    key="download_diagram_png",
                    use_container_width=True
                )

        dl2.download_button(
            label="📥 Download Documentation (Markdown)",
            data=doc_md,
            file_name=f"{base_name}.md",
            mime="text/markdown",
            key="download_doc_md",
            use_container_width=True
        )

        with open(pdf_path, "rb") as f:
            dl3.download_button(
                label="📥 Download Full PDF Report",
                data=f,
                file_name=f"{base_name}.pdf",
                mime="application/pdf",
                key="download_full_pdf",
                use_container_width=True
            )

        st.caption("The PDF bundles the diagram image and full documentation in a single file.")
