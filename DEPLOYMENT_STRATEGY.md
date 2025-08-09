# 🚀 Cloud Deployment Strategy - Stripe Dashboard

> **Reference Document**: Future cloud deployment options for Team Orlando Water Polo Club Stripe Dashboard

**Document Status**: Planning/Reference  
**Current Project Status**: Local Development  
**Created**: August 8, 2025  

---

## 🎯 Executive Summary

This document outlines cloud deployment strategies for migrating the Stripe Dashboard from local development to production cloud hosting. Analysis covers both AWS and GCP options, with **GCP emerging as the clear winner** due to existing Google Workspace non-profit benefits.

**Key Finding**: GCP deployment would be essentially **FREE** (~$0-2/month) vs AWS ($5-30/month) due to:
- Google for Nonprofits $10,000/month credits
- Existing Google Workspace unlimited storage  
- Seamless integration with current Google Sheets export functionality

---

## 🏗️ Current Application Architecture Analysis

### Application Characteristics
- **Framework**: Streamlit web application (single-user, session-based)
- **Compute**: Stateless with temporary caching (5-10 minute TTL)
- **Dependencies**: Stripe API, Anthropic AI, Google Sheets API
- **Storage**: Local JSON files for customer tags/notes (`data/tags_and_notes.json`)
- **Resources**: Minimal CPU/memory requirements (Python 3.11)

### Modular Structure (Post-Refactoring)
```
stripe-dashboard/
├── app.py                    # Main entry point (96 lines)
├── config/settings.py        # Environment configuration
├── services/                 # API integrations & caching
├── models/                   # Data models & customer management
├── analytics/                # Business metrics & calculations
├── dashboard/                # UI components
├── exports/                  # Report generation
├── utils/                    # Utilities & formatters
└── tests/                    # Comprehensive test suite
```

---

## ☁️ AWS Deployment Options

### Option 1: Serverless-First Architecture
**Core Services:**
- **AWS Lambda** + **API Gateway**: Convert Streamlit to FastAPI backend
- **AWS Amplify** or **S3 + CloudFront**: Static frontend hosting
- **DynamoDB**: Replace local JSON with serverless NoSQL
- **Systems Manager Parameter Store**: Secure environment variables
- **CloudWatch**: Logging and monitoring

**Required Changes:**
```python
# Backend restructure needed - separate frontend/backend
├── lambda/
│   ├── transactions_api.py      # GET /transactions
│   ├── customers_api.py         # GET/POST /customers  
│   ├── analytics_api.py         # GET /analytics
│   └── reports_api.py           # GET/POST /reports

# Frontend: React/Vue.js hosted on S3/Amplify
├── frontend/
│   ├── components/
│   │   ├── TransactionDashboard.js
│   │   ├── CustomerManagement.js
│   │   └── AnalyticsCharts.js
```

**Monthly Cost**: ~$5-10/month for low usage

### Option 2: Container-Based (ECS Fargate)
**Core Services:**
- **ECS Fargate**: Serverless container hosting
- **Application Load Balancer**: HTTPS termination  
- **EFS**: Shared file storage for data persistence
- **Secrets Manager**: API key management
- **Route 53**: Custom domain

**Required Changes:**
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```python
# config/aws_settings.py
def get_secret_value(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

STRIPE_SECRET_KEY = get_secret_value('/stripe-dashboard/stripe-secret-key')
DATA_DIR = '/mnt/efs/data'  # EFS mount point
```

**Monthly Cost**: ~$22-32/month

### Option 3: Scheduled Batch Processing (Ultra Low Cost)
**Perfect for "once daily" usage pattern**

**Core Services:**
- **EventBridge**: Daily trigger (6 AM EST)
- **Lambda**: Generate and store reports
- **S3**: Static report storage
- **SES**: Email reports to stakeholders
- **CloudFront**: Secure report access

**Architecture Flow:**
```python
# EventBridge → Lambda → Generate Reports → S3 → Email
def lambda_handler(event, context):
    # Run analytics pipeline
    transactions = get_stripe_data()
    report = generate_daily_report(transactions)
    
    # Store in S3
    s3_key = f"reports/{date.today()}/daily-report.pdf"
    s3.put_object(Bucket='reports-bucket', Key=s3_key, Body=report)
    
    # Email to stakeholders
    send_email_report(report, recipients=['finance@team.com'])
```

**Monthly Cost**: ~$1.30/month (**Most cost-effective AWS option**)

---

## 🏆 GCP Deployment Options (RECOMMENDED)

### Major Advantages with Google Workspace Non-Profit Account
✅ **Google for Nonprofits**: $10,000/month in free GCP credits  
✅ **Seamless Google Sheets Integration**: Already implemented in current app!  
✅ **Workspace SSO**: Easy authentication integration  
✅ **Massive Storage**: Leverage existing Google Drive unlimited storage  
✅ **Gmail Integration**: Built-in email for report delivery  

### Option 1: Cloud Run + Scheduler (RECOMMENDED)
**Core Services:**
- **Cloud Run**: Serverless containerized Streamlit app
- **Cloud Scheduler**: Daily/weekly triggers  
- **Firestore**: Replace local JSON storage
- **Secret Manager**: API key storage
- **Cloud Storage**: Report storage (uses Workspace storage quota!)

**Required Changes (Minimal):**
```yaml
# cloudbuild.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/stripe-dashboard', '.']
- name: 'gcr.io/cloud-builders/docker'  
  args: ['push', 'gcr.io/$PROJECT_ID/stripe-dashboard']
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 'stripe-dashboard', 
         '--image', 'gcr.io/$PROJECT_ID/stripe-dashboard',
         '--platform', 'managed', '--region', 'us-central1']
```

```python
# config/gcp_settings.py
from google.cloud import secretmanager, firestore

def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Firestore for customer data (replaces local JSON)
db = firestore.Client()
customers_ref = db.collection('customers')
```

```dockerfile
# Dockerfile (minimal changes from current structure)
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

**Monthly Cost**: ~$0-3/month (covered by non-profit credits!) 🎉

### Option 2: Enhanced Google Workspace Integration
**Unique Advantages with Existing Google Ecosystem:**

```python
# Enhanced Google Workspace integration
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GoogleWorkspaceIntegration:
    def __init__(self):
        self.sheets_service = build('sheets', 'v4', credentials=creds)
        self.drive_service = build('drive', 'v3', credentials=creds)
        self.gmail_service = build('gmail', 'v1', credentials=creds)
    
    def publish_board_report(self, data):
        # Create new Google Sheet in shared "Board Reports" folder
        sheet_id = self.create_shared_sheet("Monthly Finance Report")
        
        # Populate with Stripe data (using existing export functionality!)
        self.populate_sheet(sheet_id, data)
        
        # Share with board members automatically
        self.share_with_board(sheet_id)
        
        # Send email notification via Gmail API
        self.send_board_notification(sheet_id)
```

**Additional Features:**
- **Board Portal in Google Sites**: Auto-generated dashboard page
- **Google Calendar Integration**: Schedule finance reviews when revenue changes
- **Google Forms Integration**: Member satisfaction surveys
- **Google Drive**: Automatic report archiving in shared folders

### Option 3: Batch Processing with Google Workspace
**Architecture Flow:**
```
Cloud Scheduler → Cloud Functions → Generate Reports → {
  ├── Google Sheets (live dashboard) - EXISTING INTEGRATION!
  ├── Google Drive (PDF storage) - FREE unlimited storage!
  ├── Gmail (email notifications) - Built into Workspace!
  └── Firestore (customer data)
}
```

```python
# main.py (Cloud Function)
def generate_daily_report(request):
    # Fetch Stripe data (existing code!)
    transactions = get_stripe_data()
    
    # Generate reports using existing export functions
    reports = {
        'sheets': export_to_google_sheets(transactions),  # Already implemented!
        'pdf': create_pdf_report(transactions),  
        'summary': generate_claude_summary(transactions)  # Already implemented!
    }
    
    # Store in Google Drive (using unlimited Workspace storage!)
    drive_folder = store_in_team_drive(reports)
    
    # Email board with links via Gmail API
    send_gmail_notification(drive_folder, reports['summary'])
    
    return {"status": "success", "reports_generated": len(reports)}
```

---

## 💰 Cost Comparison Analysis

| Service Category | AWS Cost | GCP Cost | GCP Non-Profit Advantage |
|------------------|----------|----------|--------------------------|
| **Serverless Compute** | $0.20/month | $0.10/month | **Covered by $10k credits** |
| **Storage** | $1.00/month | $0.50/month | **FREE (Workspace storage!)** |
| **Database** | $0.25/month | $0.15/month | **Covered by credits** |
| **Email/Notifications** | $0.10/month | **FREE** | **Gmail API included** |
| **Secrets Management** | $0.40/month | $0.06/month | **Covered by credits** |
| **Monitoring** | $2.00/month | $1.00/month | **Covered by credits** |
| **API Gateway** | $3.50/month | $0.00/month | **Cloud Run includes HTTP** |
| **Load Balancer** | $16.20/month | $0.00/month | **Not needed with Cloud Run** |
| **Total Monthly** | **$4-30/month** | **$0-2/month** | **🏆 Essentially FREE!** |

---

## 🎯 Deployment Recommendation

### **🏆 GCP Cloud Run + Scheduler with Google Workspace Integration**

**Why this is the clear winner for Team Orlando Water Polo Club:**

✅ **Cost**: Essentially FREE with non-profit credits vs $5-30/month on AWS  
✅ **Time to Deploy**: 1-2 days (minimal changes) vs 3-5 days (major restructure)  
✅ **Storage**: Unlimited via Workspace vs paid storage on AWS  
✅ **Integration**: Existing Google Sheets export works perfectly vs building new integrations  
✅ **Collaboration**: Built-in sharing with board members via Google Workspace  
✅ **Scalability**: Auto-scales from 0 to handle any usage spikes  
✅ **Maintenance**: Minimal ongoing maintenance vs complex AWS service management  

### Implementation Roadmap

**Phase 1: Basic Migration (1-2 days)**
1. Create `Dockerfile` (minimal changes to current structure)
2. Setup GCP project with Cloud Run service  
3. Replace local JSON storage with Firestore
4. Deploy containerized Streamlit app
5. Configure Cloud Scheduler for automated reports

**Phase 2: Enhanced Integration (2-3 days)**  
1. Expand Google Workspace integration
2. Automated Google Drive report storage
3. Gmail notification system
4. Board portal in Google Sites
5. Calendar integration for finance reviews

**Phase 3: Advanced Features (Optional)**
1. Google Forms member surveys
2. Advanced analytics with BigQuery
3. Multi-user authentication via Workspace SSO
4. Geographic customer analysis with Google Maps API

---

## 🔧 Infrastructure as Code

### GCP Terraform Configuration
```hcl
# infrastructure/terraform/gcp/main.tf
resource "google_cloud_run_service" "stripe_dashboard" {
  name     = "stripe-dashboard"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/stripe-dashboard"
        ports {
          container_port = 8080
        }
        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }
      }
    }
  }
}

resource "google_cloud_scheduler_job" "daily_report" {
  name     = "stripe-dashboard-daily"
  schedule = "0 11 * * *"  # 6 AM EST daily
  
  http_target {
    uri    = google_cloud_run_service.stripe_dashboard.status[0].url
    method = "POST"
  }
}

resource "google_firestore_database" "dashboard_db" {
  project     = var.project_id
  name        = "(default)"
  location_id = "us-central"
  type        = "FIRESTORE_NATIVE"
}
```

### Required Environment Variables
```bash
# .env.gcp
GOOGLE_CLOUD_PROJECT=team-orlando-stripe-dashboard
STRIPE_SECRET_KEY=projects/{project}/secrets/stripe-secret/versions/latest
STRIPE_PUBLISHABLE_KEY=projects/{project}/secrets/stripe-publishable/versions/latest
ANTHROPIC_API_KEY=projects/{project}/secrets/anthropic-api/versions/latest
```

---

## 🚀 Future Growth Scenarios

### Current → Low Cloud Usage (Daily Reports)
- **Timeline**: 1-2 days
- **Cost**: $0/month  
- **Effort**: Minimal code changes

### Low → Medium Usage (Weekly Interactive Access)
- **Add**: Cloud CDN for faster loading
- **Cost**: Still $0/month (covered by credits)
- **Effort**: Configuration only

### Medium → High Usage (Daily Interactive Use)  
- **Add**: Auto-scaling, advanced monitoring
- **Cost**: $10-20/month (still within credits)
- **Effort**: Minimal - Cloud Run handles scaling

### Enterprise Scale (Multiple Organizations)
- **Migrate to**: GKE with horizontal pod autoscaling
- **Add**: Cloud SQL, advanced security, multi-tenant architecture
- **Cost**: $50-100/month
- **Effort**: Moderate refactoring for multi-tenancy

---

## 📚 Additional Resources

### Documentation Links
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google for Nonprofits](https://www.google.com/nonprofits/)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Google Workspace API Integration](https://developers.google.com/workspace)

### Migration Checklist
- [ ] Setup GCP project and billing account
- [ ] Apply for Google for Nonprofits credits
- [ ] Create service account for Google Sheets API (if not existing)
- [ ] Test containerization locally
- [ ] Setup Cloud Build for CI/CD
- [ ] Configure monitoring and alerting
- [ ] Plan data migration from local JSON to Firestore
- [ ] Setup custom domain (if desired)
- [ ] Configure backup strategies
- [ ] Plan rollback procedures

---

## 🎯 Next Steps

### When Ready to Deploy:
1. **Validate Non-Profit Credits**: Confirm Google for Nonprofits eligibility and credit availability
2. **Create GCP Project**: Setup dedicated project for Team Orlando dashboard
3. **Test Local Container**: Validate Docker container locally before cloud deployment
4. **Plan Migration Window**: Schedule downtime for data migration (minimal - just customer tags)
5. **Deploy to Cloud Run**: Single command deployment with existing code
6. **Configure Automation**: Setup Cloud Scheduler for automated report generation
7. **Train Users**: Brief introduction to new Google Workspace integrations

**Estimated Total Migration Time**: 1-2 days with current modular architecture  
**Estimated Monthly Cost**: $0-2 (covered by non-profit credits)  
**Risk Level**: Low (minimal code changes, extensive fallback options)

---

**Document Owner**: Development Team  
**Stakeholders**: Team Orlando Water Polo Club Board, Finance Team  
**Review Date**: Quarterly or when usage patterns change  
**Status**: Ready for implementation when cloud deployment is desired