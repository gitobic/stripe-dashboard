# Project Requirements Document (PRD)
## Stripe Dashboard

### 🎯 PROJECT STATUS: PREPARING FOR DEPLOYMENT 🚀
**Last Updated:** August 9, 2025  
**Current Phase:** Streamlit Cloud Deployment Preparation  
**Overall Completion:** Core features complete, deployment in progress

**Quick Summary:**
- ✅ Core transaction tracking implemented
- ✅ Customer management features implemented
- ✅ Subscription analytics implemented
- ✅ Standardized Quick Actions across all tabs
- 🚀 **Preparing for Streamlit Cloud deployment**

### 🌟 **Next Milestone: Cloud Deployment**
**Target:** Deploy to Streamlit Cloud for production use by Team Orlando Water Polo Club
**Timeline:** Authentication → Secrets → Deploy → Test

---

### 1. Project Overview

**Project Name:** Stripe Reporting Dashboard

**Project Description:** 
The tool will be browser based.  It will let me connect to my Stripe account and have multiple configurable views. It will allow visiblity into the financial data for the Team Orlando Water Polo Club.

**Target Users:**
Board of Directors, Finance Team

**Business Objectives:**
This tool will give visibility into the financials of the Team Orlando Water Polo Club

### 2. Core Features
Transactions Dashboard
Let users filter and explore financial transactions:
    Filters:
        Date range
        Payment type (one-time, recurring)
        Status (paid, failed, refunded, etc.)
        Amount (min/max)
    Sorting by:
        Date
        Amount
        Customer
    Grouping (by month, by product, by customer)
    Pagination & search.
    
    Data shown:
    Customer name/email
    Amount
    Fee breakdown (Stripe fee, net, etc.)
    Payment method
    Invoice/subscription info

Customers View
    List all customers.
    Filter by active/inactive, high spenders, last payment.
    View customer profile:
        Contact info
        Payment history
        Subscriptions
        Refunds/disputes

Subscriptions View
    Filter by:
        Active/canceled/trialing
        Plan type
        Created date
    Metrics:
        MRR / ARR (Monthly/Annual Recurring Revenue)
        Churn rate estimate
        Trial conversion rate

Reports & Exports
    Export current view as:
        Google Sheet (via API)
        CSV/Excel
    “Generate Summary Report”:
        Uses Claude to create plain-English summary: “In the last 30 days, you had 27 new customers, 3 refunds, and net revenue of $4,893.”
    Scheduled reports:
        Automatically email/export every week/month.

Custom Tags & Notes
    Add notes/tags to customers or transactions.
    Search/filter based on tags (e.g., “VIP,” “Refund Risk”).

Forecasting / Predictive Revenue
    Use simple modeling to:
        Forecast next month's revenue.
        Estimate lifetime value of customers.
        Predict subscription renewals or cancellations.

Pricing & Fee Analyzer
    See total fees paid to Stripe over time.
    Effective rate (%) per transaction.
    Compare pricing models (e.g., flat vs usage-based).        

Claude Recommendations
    Use Claude to make recommendtions on prices and fee controls to minimize losses

#### 2.1 Data Visualization ✅ COMPLETED
- [x] Revenue analytics (daily revenue line chart)
- [x] Revenue by product breakdown (bar chart)  
- [x] Transaction volume trends (metrics display)
- [x] Multiple chart view options (single/side-by-side)
- [ ] Payment method breakdown
- [ ] Geographic distribution

#### 2.2 Time Period Controls ✅ COMPLETED
- [x] Date range picker (custom start/end dates)
- [x] Predefined periods (7 days, 30 days, 90 days, 1 year quick buttons)
- [x] Auto-detection of data range for smart defaults
- [x] Real-time data fetching with loading indicators

#### 2.3 Transaction Details ✅ COMPLETED  
- [x] Recent transactions table
- [x] Customer name resolution (name/email/ID)
- [x] Product information display
- [x] Payment status and currency
- [x] Date/time formatting

#### 2.4 User Experience ✅ COMPLETED
- [x] Clean Streamlit interface with sidebar controls
- [x] Error handling with helpful messages
- [x] Loading states and progress indicators
- [x] Guidance for test data creation

### PHASE 2 - Next Priority Features

#### 2.5 Advanced Filtering ✅ MOSTLY COMPLETED
- [x] Filter by payment status (succeeded, failed, refunded)
- [ ] Filter by customer type  
- [ ] Filter by product/service
- [x] Amount range filtering (min/max)

#### 2.6 Export & Reporting ✅ COMPLETED
- [x] Export charts as images
- [x] Export data as CSV/Excel
- [x] PDF report generation
- [x] Google Sheets integration
- [x] Claude AI-powered summary reports
- [ ] Email reports (scheduled)

#### 2.7 Enhanced Analytics ✅ MOSTLY COMPLETED
- [x] Payment method breakdown
- [ ] Geographic distribution
- [x] Monthly/quarterly trends
- [x] Fee analysis
- [x] Revenue forecasting
- [x] Customer lifetime value analysis
- [x] Claude AI business recommendations

### PHASE 3 - Advanced Features ✅ COMPLETED BEYOND SCOPE

#### 3.1 Customer Management System ✅ COMPLETED
- [x] Customer tagging system with color-coded tags
- [x] Customer notes and interaction tracking
- [x] Advanced customer search and filtering
- [x] Customer lifetime value calculations
- [x] Payment history tracking per customer

#### 3.2 Subscription Management ✅ COMPLETED  
- [x] Complete MRR/ARR analytics
- [x] Subscription status tracking and filtering
- [x] Churn rate analysis
- [x] Trial conversion metrics
- [x] Plan performance analytics

#### 3.3 API Performance Optimizations ✅ COMPLETED
- [x] Auto-pagination for unlimited data retrieval
- [x] Intelligent caching system (5-10 minute TTL)
- [x] Data expansion optimization to reduce API calls
- [x] Rate limiting protection
- [x] 60-70% reduction in API calls

#### 3.4 Multi-Tab Dashboard Interface ✅ COMPLETED
- [x] Transactions analytics tab
- [x] Customer management tab  
- [x] Subscriptions analytics tab
- [x] Reports and exports tab
- [x] AI-powered analytics and insights tab

### 4. Technical Requirements

#### 4.1 Data Sources ✅ COMPLETED
**Stripe API Endpoints:**
- [x] Charges API (with auto-pagination)
- [x] Customers API (with auto-pagination)
- [x] Subscriptions API (with expanded data)
- [x] Prices API (with caching)
- [x] Products API (with caching)
- [x] Subscription Items API

#### 4.2 Performance Requirements ✅ EXCEEDED
- [x] Dashboard loads within 2-5 seconds (cached responses < 1 second)
- [x] Handles unlimited transactions via auto-pagination
- [x] Data refresh frequency: 5-10 minutes with intelligent caching
- [x] 60-70% reduction in API calls through optimization
- [x] Real-time filtering and sorting capabilities

#### 4.3 Security Requirements ✅ COMPLETED
- [x] Secure API key management via .env files
- [x] Test environment isolation
- [x] Data encryption in transit (HTTPS)
- [x] No sensitive data stored locally (except temporary caches)
- [x] MCP server authentication configured

### 4. User Experience

#### 4.1 Dashboard Layout
**Main Dashboard Sections:**
- [ ] Overview/Summary section
- [ ] Revenue charts section
- [ ] Transaction details section
- [ ] Customer insights section
- [ ] [Add other sections]

#### 4.2 Navigation
- [ ] Single-page dashboard
- [ ] Multi-page with navigation
- [ ] Mobile responsiveness
- [ ] [Add navigation requirements]

### 5. Success Metrics

**How will you measure success?**
- [ ] User adoption rate
- [ ] Time saved in reporting
- [ ] Data accuracy improvements
- [ ] [Add your success metrics]

### 6. Timeline & Milestones

**Phase 1: MVP** (Target: [Date])
- [ ] Basic revenue visualization
- [ ] Simple date filtering
- [ ] Core Stripe data integration

**Phase 2: Enhanced Features** (Target: [Date])
- [ ] Advanced filtering
- [ ] Multiple chart types
- [ ] Export functionality

**Phase 3: Cloud Deployment** (Target: Current Phase - August 2025)
- [ ] Authentication system implementation
- [ ] Secrets management configuration
- [ ] Streamlit Cloud deployment
- [ ] Production testing and validation

### 7. 🚀 Cloud Deployment Requirements

#### 7.1 Authentication & Security
**Requirement:** Implement secure access control for production deployment
- **Task**: Username/password authentication system
- **Implementation**: Session-based authentication with Streamlit state management
- **Security**: Protect sensitive Team Orlando Water Polo Club financial data
- **User Experience**: Simple login page with automatic logout

#### 7.2 Secrets Management
**Requirement:** Secure API key storage for cloud environment
- **Local Development**: `.streamlit/secrets.toml` for local testing
- **Production**: Streamlit Cloud secrets dashboard configuration
- **Environment Support**: Dual support for `.env` (local) and Streamlit secrets (cloud)
- **Security**: No API keys in version control or logs

#### 7.3 Cloud Infrastructure
**Requirement:** Deploy to Streamlit Cloud for free hosting
- **Platform**: Streamlit Cloud (free tier for personal projects)
- **Dependencies**: `requirements.txt` for cloud dependency management
- **Configuration**: `.streamlit/config.toml` for performance optimization
- **Integration**: GitHub integration for continuous deployment

#### 7.4 Production Readiness
**Requirement:** Ensure stable operation in cloud environment
- **Testing**: Local testing with cloud-like configuration
- **Performance**: Memory and CPU optimization for cloud limits
- **Monitoring**: Error tracking and performance monitoring
- **Backup**: GitHub-based version control and rollback capability

#### 7.5 User Access
**Requirement:** Provide secure access to Team Orlando Water Polo Club stakeholders
- **URL**: Custom Streamlit Cloud URL (e.g., team-orlando-dashboard.streamlit.app)
- **Domain**: Optional custom domain configuration
- **Access Control**: Shared credentials for authorized users only
- **Availability**: 24/7 availability through Streamlit Cloud infrastructure

### 8. Deployment Timeline

**Week 1: Authentication Implementation**
- [ ] Create login/logout system
- [ ] Implement session management
- [ ] Test authentication locally

**Week 2: Secrets & Configuration** 
- [ ] Configure secrets management
- [ ] Create requirements.txt
- [ ] Set up Streamlit configuration files

**Week 3: Cloud Deployment**
- [ ] Deploy to Streamlit Cloud
- [ ] Configure production secrets
- [ ] Test all functionality in production

**Week 4: Production Validation**
- [ ] Performance testing
- [ ] User acceptance testing
- [ ] Documentation updates
- [ ] Go-live for Team Orlando Water Polo Club

### 7. Constraints & Assumptions

**Technical Constraints:**
- [ ] Stripe API rate limits
- [ ] Data storage limitations
- [ ] [Add other constraints]

**Business Constraints:**
- [ ] Budget limitations
- [ ] Resource availability
- [ ] [Add other constraints]

**Assumptions:**
- [ ] Stripe account has necessary permissions
- [ ] Users have basic dashboard experience
- [ ] [Add other assumptions]

### 8. Out of Scope

**Features explicitly NOT included in this version:**
- [ ] Multi-tenant support
- [ ] Advanced user roles
- [ ] Integration with other payment processors
- [ ] [Add other out-of-scope items]

### 9. Risk Assessment

**High Priority Risks:**
- [ ] API rate limiting issues
- [ ] Data privacy compliance
- [ ] Performance with large datasets
- [ ] [Add other risks]

**Mitigation Strategies:**
- [Fill in how you'll address each risk]

---

**Document Status:** Draft
**Last Updated:** [07/28/2025]
**Owner:** Tobey
**Stakeholders:** [List key stakeholders]