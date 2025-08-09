# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Stripe dashboard application built with Python, using FastAPI and Streamlit for creating a web-based dashboard to visualize Stripe data with Pandas and Plotly. The application provides financial analytics for Team Orlando Water Polo Club with transaction tracking, customer management, and subscription analytics.

## Development Commands

### Environment Setup
```bash
# Install dependencies using uv (preferred package manager)
uv sync

# Alternative: install with pip
pip install -e .
```

### Running the Application
```bash
# Run the Streamlit dashboard (primary application)
uv run streamlit run app.py

# Alternative: Run with specific port
uv run streamlit run app.py --server.port 8501

# Run the basic hello world app
python main.py
```

### Dashboard Access
Once running, access the dashboard at: **http://localhost:8501**

## Features Overview 🔧 IN DEVELOPMENT

### 3-Tab Dashboard Interface:

#### 📊 **Transactions Tab**
- **Real-time Analytics**: Revenue charts, product breakdown, payment method analysis
- **Advanced Filtering**: Payment status, amount ranges, date filtering with smart presets
- **Standardized Quick Actions**: Refresh data, export to CSV/Excel
- **Performance**: Auto-pagination handles unlimited transactions, intelligent 5-minute caching

#### 👥 **Customers Tab** 
- **Customer Management**: Complete customer profiles with contact info, payment history
- **Advanced Search**: Filter by status, tags, search by name/email
- **Standardized Quick Actions**: Refresh data, export to CSV/Excel
- **Customer Details**: Individual customer drill-down with payment history

#### 🔄 **Subscriptions Tab**
- **MRR/ARR Analytics**: Real-time recurring revenue calculations
- **Churn Analysis**: Churn rates, trial conversion metrics, plan performance
- **Subscription Management**: Filter by status, plan type, billing cycles
- **Visual Analytics**: Status breakdown charts, revenue by plan analysis
- **Standardized Quick Actions**: Refresh data, export to CSV/Excel


## Architecture & Performance

### Core Files:
- **app.py**: Complete dashboard application with optimized Stripe API integration (2,220+ lines)
- **main.py**: Simple entry point for testing
- **data/**: Local data storage for customer tags and notes (JSON-based)
- **pyproject.toml**: Complete dependency management

### Performance Optimizations:
- **Auto-Pagination**: Handles unlimited Stripe records automatically
- **Intelligent Caching**: 5-minute cache for transactions, 10-minute for customers/subscriptions  
- **Data Expansion**: Single API calls with relationship expansion (60-70% API call reduction)
- **Rate Limiting**: Built-in Stripe API rate limit protection
- **Memory Efficiency**: Stream processing for large datasets

### Technology Stack:
- **Backend**: Streamlit with FastAPI components
- **Data Processing**: Pandas for analytics, Plotly for visualizations
- **External APIs**: Stripe SDK
- **Caching**: Streamlit session-based intelligent caching

## Key Dependencies

- **stripe**: Official Stripe Python library for API integration
- **fastapi + uvicorn**: Modern web framework for building APIs
- **streamlit**: Framework for building data applications
- **pandas**: Data analysis and manipulation
- **plotly**: Interactive plotting library
- **python-dotenv**: Environment variable management

## Environment Variables

This project requires environment variables configured in the `.env` file:

### Required Variables:
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

The `.env` file is already configured for this project. The `.env.example` file shows the format for reference.

## MCP Servers Configuration

### Configured MCP Servers:
1. **Stripe MCP** (`https://mcp.stripe.com`) - ✅ Connected
   - Direct Stripe API access through MCP tools
   - Authenticated with project's Stripe test API key
   
2. **Ref MCP** (`https://api.ref.tools/mcp`) - ✅ Connected  
   - Documentation and reference tools
   - Code examples and development assistance

Both MCP servers are production-ready and enhance development capabilities beyond the existing dashboard functionality.

## Current Project Status

### 🔧 IN DEVELOPMENT - Key Achievements:
- **Core Feature Set**: Transaction tracking, customer management, subscription analytics
- **Performance Optimized**: 60-70% reduction in API calls through intelligent caching and data expansion
- **Production Scale**: Handles unlimited transactions via auto-pagination
- **Clean Architecture**: Modular design with separation of concerns

### Current Focus Areas:
- Enhanced transaction filtering and analysis
- Improved customer management features  
- Subscription analytics and tracking
- Additional usability improvements

**Status**: Core functionality complete, preparing for Streamlit Cloud deployment.

## 🚀 Streamlit Cloud Deployment Plan

### Deployment Phases:

#### Phase 1: Authentication & Security
- **Task**: Implement username/password authentication system
- **Reason**: Protect sensitive financial data in cloud environment
- **Implementation**: Session-based authentication with Streamlit state management

#### Phase 2: Secrets Management
- **Task**: Configure secure API key storage for cloud deployment
- **Files**: Create `.streamlit/secrets.toml` for local testing
- **Cloud**: Configure secrets in Streamlit Cloud dashboard
- **Environment**: Support both `.env` (local) and Streamlit secrets (cloud)

#### Phase 3: Cloud Compatibility
- **Task**: Create `requirements.txt` for Streamlit Cloud dependency management
- **Task**: Update `config/settings.py` to handle both local and cloud environments
- **Task**: Add `.streamlit/config.toml` for optimized cloud performance

#### Phase 4: Deployment & Testing
- **Task**: Test locally with cloud-like configuration
- **Task**: Deploy to Streamlit Cloud with GitHub integration
- **Task**: Verify all dashboard functionality in production environment
- **Task**: Configure optional custom domain

### Required Files for Deployment:
```
.streamlit/
├── secrets.toml     # Local secrets (git-ignored)
└── config.toml      # Streamlit app configuration

requirements.txt     # Cloud dependencies
```

### Authentication Implementation:
- Simple username/password protection
- Session-based access control
- Automatic logout on browser close
- Secure credential handling via Streamlit secrets

### Cloud Benefits:
- **Free hosting** for personal projects
- **Automatic HTTPS** and security
- **GitHub integration** for continuous deployment
- **Built-in secrets management**
- **No server maintenance** required

### Deployment Readiness:
- ✅ Core application stable and tested
- ✅ Modular architecture cloud-ready
- 🔄 Authentication system (in progress)
- 🔄 Secrets management configuration (in progress)
- ⏳ Cloud deployment testing (pending)