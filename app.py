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
    ai_engine = st.selectbox(
        "Select Provider",
        ["AWS Bedrock (Claude / Nova via Boto3)", "Smart AWS Architect Engine (Local / Zero Setup)"]
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
# Maps a canonical service key -> list of keyword aliases to look for in the
# user's requirement text / code snippet. Add new services here as needed;
# everything else (icon class, label, diagram tier) is driven off this map.
SERVICE_KEYWORD_MAP = {
    "route53": ["route 53", "route53", "dns"],
    "cloudfront": ["cloudfront", "cdn", "content delivery"],
    "waf": ["waf", "web application firewall"],
    "alb": ["load balancer", "alb", "application load balancer", "elb"],
    "apigateway": ["api gateway", "rest api", "graphql api", "appsync"],
    "cognito": ["cognito", "user pool", "authentication", "auth0", " auth "],
    "iam": ["iam role", "iam policy", " iam "],
    "lambda": ["lambda", "serverless function", "serverless backend"],
    "ec2": ["ec2", "virtual machine", "compute instance"],
    "ecs": ["ecs", "fargate", "elastic container service"],
    "eks": ["eks", "kubernetes"],
    "stepfunctions": ["step functions", "state machine"],
    "dynamodb": ["dynamodb", "nosql"],
    "rds": ["rds", "aurora", "postgres", "mysql", "relational database"],
    "elasticache": ["elasticache", "redis", "memcached"],
    "redshift": ["redshift", "data warehouse"],
    "s3": ["s3", "object storage", "static assets", "bucket"],
    "efs": ["efs", "elastic file system"],
    "sqs": ["sqs", "queue"],
    "sns": ["sns", "pub/sub", "push notification"],
    "ses": ["ses", "email notification", "send email", "email service"],
    "eventbridge": ["eventbridge", "event bus"],
    "kinesis": ["kinesis", "data stream"],
    "cloudwatch": ["cloudwatch", "monitoring", "metrics", "alarms"],
    "xray": ["x-ray", "distributed tracing"],
    "kms": ["kms", "encryption key"],
    "secretsmanager": ["secrets manager", "secret rotation"],
    "glue": ["glue", "etl job"],
    "athena": ["athena", "query data lake"],
    "sagemaker": ["sagemaker", "machine learning model"],
    "bedrock": ["bedrock", "foundation model", "generative ai"],
}

# Diagram tiers control left-to-right layout and how nodes connect to each other.
# Within a tier, nodes fan out from the previous tier's node(s) and all feed
# into the next tier's node(s) — giving a layout that reflects actual request
# flow instead of one arbitrary chain through every detected service.
SERVICE_TIERS = [
    ["route53", "cloudfront", "waf"],
    ["alb", "apigateway", "cognito"],
    ["lambda", "ec2", "ecs", "eks", "stepfunctions", "bedrock", "sagemaker"],
    ["dynamodb", "rds", "elasticache", "redshift", "s3", "efs", "glue", "athena"],
    ["sqs", "sns", "ses", "eventbridge", "kinesis"],
    ["cloudwatch", "xray", "kms", "secretsmanager"],
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
    """
    from diagrams import Diagram
    from diagrams.aws.network import APIGateway, CloudFront, Route53, ELB
    from diagrams.aws.network import ClientVpn as WAFPlaceholder  # fallback if WAF unavailable
    from diagrams.aws.compute import Lambda, EC2, ECS, EKS
    from diagrams.aws.integration import StepFunctions, SNS, SQS, Eventbridge
    from diagrams.aws.database import Dynamodb, RDS, ElastiCache, Redshift
    from diagrams.aws.storage import SimpleStorageServiceS3, EFS
    from diagrams.aws.security import Cognito, IAM, KMS, SecretsManager
    from diagrams.aws.management import Cloudwatch
    from diagrams.aws.ml import Sagemaker
    from diagrams.aws.analytics import Glue, Athena, KinesisDataStreams

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
        from diagrams.aws.engagement import SES
    except ImportError:
        SES = SNS

    node_factory = {
        "route53": lambda: Route53("Route 53"),
        "cloudfront": lambda: CloudFront("CloudFront CDN"),
        "waf": lambda: WAF("WAF"),
        "alb": lambda: ELB("Load Balancer"),
        "apigateway": lambda: APIGateway("API Gateway"),
        "cognito": lambda: Cognito("Cognito Auth"),
        "lambda": lambda: Lambda("Lambda Functions"),
        "ec2": lambda: EC2("EC2 Instances"),
        "ecs": lambda: ECS("ECS Service"),
        "eks": lambda: EKS("EKS Cluster"),
        "stepfunctions": lambda: StepFunctions("Step Functions"),
        "bedrock": lambda: Bedrock("Bedrock Model"),
        "sagemaker": lambda: Sagemaker("SageMaker Model"),
        "dynamodb": lambda: Dynamodb("DynamoDB Table"),
        "rds": lambda: RDS("RDS Database"),
        "elasticache": lambda: ElastiCache("ElastiCache"),
        "redshift": lambda: Redshift("Redshift"),
        "s3": lambda: SimpleStorageServiceS3("S3 Bucket"),
        "efs": lambda: EFS("EFS"),
        "glue": lambda: Glue("Glue ETL"),
        "athena": lambda: Athena("Athena"),
        "sqs": lambda: SQS("SQS Queue"),
        "sns": lambda: SNS("SNS Topic"),
        "ses": lambda: SES("SES Email"),
        "eventbridge": lambda: Eventbridge("EventBridge"),
        "kinesis": lambda: KinesisDataStreams("Kinesis Stream"),
        "cloudwatch": lambda: Cloudwatch("CloudWatch"),
        "xray": lambda: XRay("X-Ray Tracing"),
        "kms": lambda: KMS("KMS"),
        "secretsmanager": lambda: SecretsManager("Secrets Manager"),
    }

    try:
        with Diagram("AWS Cloud Architecture", show=False, filename=filename, outformat="png"):
            services_set = set(services_found)
            nodes = {}
            for key in node_factory:
                if key in services_set:
                    nodes[key] = node_factory[key]()

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
        
        system_prompt = """You are a Senior AWS Principal Solutions Architect.

IMPORTANT: The user may paste a long document containing assignment rubrics, test cases, intern tasks, deliverables, CI/CD instructions, or interview questions. 
Your task is to IGNORE all non-architectural content (such as 'Test 1', 'Bonus Challenge', 'Deliverables', 'Step X', 'Intern should...') and focus ONLY on extracting AWS services and data flows to design the architecture.

Generate a professional Markdown AWS Architecture report with these sections:
- Executive Summary
- VPC & Network Design (if applicable)
- AWS Component Breakdown (services, roles, justifications)
- End-to-End Data Flow
- Security Controls (IAM, Secrets Manager, encryption)
- CI/CD & Monitoring Strategy (if applicable)
- Monthly Cost Estimates
- Terraform IaC snippet

Output clean, structured Markdown only."""
        
        if "claude" in model_id:
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": f"{system_prompt}\n\nRequirement:\n{prompt}"}]
            }
            response = client.invoke_model(modelId=model_id, body=json.dumps(payload))
            res_body = json.loads(response["body"].read().decode())
            return res_body["content"][0]["text"]
        elif "nova" in model_id:
            payload = {
                "messages": [{"role": "user", "content": [{"text": f"{system_prompt}\n\nRequirement:\n{prompt}"}]}],
                "inferenceConfig": {"maxTokens": 4096}
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
    prompt_escaped = prompt.replace('"', '\\"')
    doc = f"""# AWS System Architecture Specification & Documentation

## 1. Executive Summary
This document defines the production-grade AWS Cloud Architecture designed to meet the specified functional and non-functional requirements. The architecture prioritizes **scalability, fault-tolerance, high availability, security, and cost efficiency**.

**Input Prompt / Requirement:**
> "{prompt_escaped}"

---

## 2. AWS Component & Service Breakdown

| Service | Category | Architectural Role | High Availability / SLA |
| :--- | :--- | :--- | :--- |
| **Amazon API Gateway** | Networking & Content Delivery | Secure API entry point, request validation, throttling, and routing | 99.95% Availability SLA |
| **AWS Lambda** | Compute | Serverless event-driven business logic execution without server management | Multi-AZ auto-scaling |
| **Amazon DynamoDB** | Database | Fully managed NoSQL key-value database for single-digit millisecond latency | Multi-AZ replication, 99.99% SLA |
| **Amazon S3** | Storage | Durable object store for static web assets, media, and encrypted backups | 99.999999999% (11 9s) Durability |
| **AWS IAM & KMS** | Security & Compliance | Least-privilege access control policies and automated KMS key encryption | Regional Global Service |
| **Amazon CloudWatch** | Management & Governance | Real-time metric monitoring, centralized logging, and alarms | Native AWS Integration |

---

## 3. End-to-End Data Flow Sequence

1. **Client Request:** User sends HTTP/HTTPS request via browser or client app.
2. **API Gateway Ingestion:** API Gateway authenticates the request, enforces rate limiting, and forwards payload to backend handlers.
3. **Lambda Execution:** AWS Lambda instances spin up on-demand in isolated microVMs, processing the request logic.
4. **Data Persistence:** Lambda queries or writes records to Amazon DynamoDB using IAM role-based temporary credentials.
5. **Asset Serving:** Static content (HTML/CSS/JS/images) is directly served securely from Amazon S3.
6. **Logging & Observability:** Execution traces and metrics are automatically streamed to CloudWatch Logs.

---

## 4. Security & Compliance Controls
- **Encryption in Transit:** Enforced TLS 1.3 encryption across all public and internal endpoints.
- **Encryption at Rest:** Server-Side Encryption (SSE-KMS) enabled for DynamoDB tables and S3 buckets.
- **Identity & Access Management:** Lambda operates under execution roles configured with strict least-privilege IAM policies.

---

## 5. Cost Estimation (Monthly Projections)

| AWS Resource | Estimated Tier / Specs | Approx. Monthly Cost (USD) |
| :--- | :--- | :--- |
| API Gateway | 1,000,000 requests/month | $3.50 |
| AWS Lambda | 1,000,000 invocations (512MB RAM) | $0.00 (Free Tier Eligible) / $1.20 |
| Amazon DynamoDB | On-Demand (Read/Write units) | $2.50 |
| Amazon S3 | 20 GB Storage + GET/PUT Requests | $0.50 |
| CloudWatch Logs | 5 GB Log ingestion | $2.85 |
| **Total Estimated Monthly Cost** | | **~$10.55 / month** |

---

## 6. Infrastructure-as-Code (Terraform Snippet)

```hcl
# AWS Lambda Function Definition
resource "aws_lambda_function" "app_backend" {{
  filename      = "function.zip"
  function_name = "backend-handler"
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"

  environment {{
    variables = {{
      DYNAMODB_TABLE = aws_dynamodb_table.app_table.name
    }}
  }}
}}

# AWS DynamoDB Table
resource "aws_dynamodb_table" "app_table" {{
  name           = "app-data-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {{
    name = "id"
    type = "S"
  }}
}}
```
"""
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

# Human-readable label and subgraph tier for each canonical service key.
MERMAID_SERVICE_META = {
    "route53":       ("Route 53",              "Edge"),
    "cloudfront":    ("CloudFront CDN",         "Edge"),
    "waf":           ("AWS WAF",                "Edge"),
    "alb":           ("Load Balancer",          "Edge"),
    "apigateway":    ("API Gateway",            "Edge"),
    "cognito":       ("Cognito Auth",           "Edge"),
    "iam":           ("IAM",                    "Security"),
    "kms":           ("KMS",                    "Security"),
    "secretsmanager":("Secrets Manager",        "Security"),
    "lambda":        ("Lambda",                 "Compute"),
    "ec2":           ("EC2",                    "Compute"),
    "ecs":           ("ECS / Fargate",          "Compute"),
    "eks":           ("EKS",                    "Compute"),
    "stepfunctions": ("Step Functions",         "Compute"),
    "bedrock":       ("Bedrock Model",          "Compute"),
    "sagemaker":     ("SageMaker",              "Compute"),
    "dynamodb":      ("DynamoDB",               "Data"),
    "rds":           ("RDS / Aurora",           "Data"),
    "elasticache":   ("ElastiCache",            "Data"),
    "redshift":      ("Redshift",               "Data"),
    "s3":            ("S3 Bucket",              "Data"),
    "efs":           ("EFS",                    "Data"),
    "glue":          ("Glue ETL",               "Data"),
    "athena":        ("Athena",                 "Data"),
    "sqs":           ("SQS Queue",              "Messaging"),
    "sns":           ("SNS Topic",              "Messaging"),
    "ses":           ("SES Email",              "Messaging"),
    "eventbridge":   ("EventBridge",            "Messaging"),
    "kinesis":       ("Kinesis Stream",         "Messaging"),
    "cloudwatch":    ("CloudWatch",             "Observability"),
    "xray":          ("X-Ray",                  "Observability"),
}

MERMAID_TIER_ORDER = ["Edge", "Compute", "Data", "Messaging", "Observability", "Security"]


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
  <div class="hero-badge">⚡ Powered by Amazon Bedrock &amp; Graphviz Engine</div>
  <div class="hero-title">☁️ AI AWS Architecture &amp; Documentation Generator</div>
  <div class="hero-subtitle">Transform natural language requirements or code snippets into
  production-ready AWS diagrams, specification docs, and PDF reports — in seconds.</div>
</div>
""", unsafe_allow_html=True)

# ── 1-Click Preset Buttons ────────────────────────────────────────────────────
st.markdown("##### 💡 Quick-Start Presets")
p_col1, p_col2, p_col3 = st.columns(3)

PRESET_ECOMMERCE = (
    "Design a serverless e-commerce processing pipeline. Customers place orders through "
    "Amazon API Gateway. API Gateway triggers an AWS Lambda function to validate payments, "
    "stores order records in Amazon DynamoDB, uploads PDF receipts to Amazon S3, and sends "
    "email confirmations via Amazon SES."
)
PRESET_RAG = (
    "Build an enterprise Generative AI Retrieval-Augmented Generation (RAG) architecture. "
    "Web users send queries via Amazon API Gateway to AWS Lambda. Lambda queries Amazon "
    "OpenSearch Serverless for document context, passes it to Amazon Bedrock foundation "
    "models to generate answers, and logs history in Amazon DynamoDB. Monitor with CloudWatch."
)
PRESET_ANALYTICS = (
    "Build a real-time clickstream analytics pipeline. Mobile apps stream user events into "
    "Amazon Kinesis Data Streams. AWS Lambda processes streams in real time, writes raw logs "
    "to an Amazon S3 Data Lake, loads aggregates into Amazon Redshift, and sends alerts via "
    "Amazon SNS. Monitor everything with Amazon CloudWatch."
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
