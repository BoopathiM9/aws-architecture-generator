# ☁️ AI AWS Architecture & Documentation Generator

> **Text / IaC Code → Visual AWS Diagrams + Specification + Downloadable PDF Reports**

An AI-powered tool built with **Python**, **Streamlit**, **AWS Boto3**, **Diagrams**, and **FPDF2**. Convert natural language project requirements or Infrastructure-as-Code (IaC) snippets directly into production-ready AWS Architecture diagrams, detailed technical documentation, cost breakdowns, and downloadable PDF reports.

---

## ✨ Features

- 🧠 **AI-Powered Architecture Synthesis**: Analyzes prompt inputs (e.g., *"I need a scalable web application with API Gateway, Lambda, DynamoDB, and S3"*) or Terraform/CloudFormation code snippets.
- 🖼️ **Visual AWS Diagram Generation**: Dynamically creates AWS cloud architecture diagrams using the Python `diagrams` engine.
- 📄 **Production-Grade Documentation**: Generates detailed Markdown technical specifications covering executive summaries, service breakdowns, data flow, security/IAM controls, monthly cost estimates, and IaC snippets.
- 📥 **One-Click PDF Export**: Compiles visual diagrams and complete technical reports into formatted PDF files for clients and engineering reviews.
- ⚙️ **Multi-Engine Support**: Connects to **AWS Bedrock** (`anthropic.claude-3-5-sonnet`, `amazon.nova`, `amazon.titan`) via Boto3, with built-in zero-setup smart architect fallback.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- [Graphviz](https://graphviz.org/download/) (Required for rendering visual diagrams)
  - **Windows**: Download installer and check *"Add Graphviz to system PATH"* (or `winget install Graphviz.Graphviz`)
  - **Mac**: `brew install graphviz`
  - **Linux**: `sudo apt-get install graphviz`

### 2. Installation & Setup
```bash
# Clone the repository
git clone https://github.com/BoopathiM9/aws-architecture-generator.git
cd aws-architecture-generator

# Install Dependencies
pip install -r requirements.txt
```

### 3. AWS Credentials Setup (Optional for AWS Bedrock)
Configure AWS credentials via AWS CLI or the app's sidebar interface:
```bash
aws configure
```

### 4. Launch Application
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🛠️ Tech Stack

- **Frontend / Dashboard**: Streamlit
- **AWS SDK**: Boto3 (AWS Bedrock Runtime)
- **Diagram Generator**: Python `diagrams` library + Graphviz
- **PDF Report Builder**: `fpdf2`

---

## 📜 License
MIT License. Free for personal and commercial use.
