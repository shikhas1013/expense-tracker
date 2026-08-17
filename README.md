# Expense Tracker AI Agent

A multi-agent expense tracking system built with the OpenAI Agents SDK. Features natural language querying, spending analysis, and a reflection loop for response quality verification.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                         │
│                  (Streamlit / CLI)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Coordinator Agent                        │
│            Routes requests to specialists                   │
└───────┬─────────────────┬─────────────────┬─────────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  Query Agent  │ │ Analyst Agent │ │ Budget Agent  │
│               │ │               │ │               │
│ • get_expenses│ │ • analyze_    │ │ • get_budget  │
│ • get_summary │ │   trends      │ │ • set_budget  │
│ • get_categories│ • identify_  │ │ • check_status│
└───────────────┘ │   unusual     │ └───────────────┘
                  │ • suggest_    │
                  │   savings     │
                  └───────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Reflection Agent                          │
│         Evaluates response quality and triggers             │
│         refinement if needed                                │
└─────────────────────────────────────────────────────────────┘
```

## Features

- **Multi-Agent Orchestration**: Coordinator routes requests to specialized agents
- **10 Function Tools**: Query, analyze, and manage expenses
- **Reflection Loop**: Automatic quality verification and response refinement
- **Session Memory**: Maintains conversation context across queries
- **Gmail Integration**: Auto-ingests bank transaction emails (DBS/PayNow/PayLah)
- **Dual Interface**: Streamlit web app and CLI

## Tools

| Tool | Agent | Description |
|------|-------|-------------|
| `get_expenses` | Query | Retrieve expenses with filters (date, category, merchant) |
| `get_spending_summary` | Query | Aggregate spending by category/merchant/month |
| `get_categories` | Query | List all expense categories |
| `analyze_spending_trends` | Analyst | Month-over-month spending patterns |
| `identify_unusual_expenses` | Analyst | Flag anomalous transactions |
| `suggest_savings` | Analyst | Actionable cost reduction recommendations |
| `get_budget` | Budget | View budget limits |
| `set_budget` | Budget | Set monthly budget for a category |
| `check_budget_status` | Budget | Compare spending vs budget |
| `update_expense_category` | Query | Recategorize an expense |

## Setup

### Prerequisites

- Python 3.9+
- AWS account (for DynamoDB)
- OpenAI API key
- Gmail API credentials (for email ingestion)

### Installation

```bash
# Clone the repository
git clone https://github.com/shikhas1013/expense-tracker.git
cd expense-tracker

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key
USER_ID=your_username

# AWS Configuration
AWS_REGION=ap-southeast-2
TABLE_NAME=ExpenseTracker
BUDGETS_TABLE=ExpenseBudgets

# Optional: AWS credentials (if not using AWS CLI profile)
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
```

### AWS Setup

Create the DynamoDB tables:

```bash
# Expenses table
aws dynamodb create-table \
  --table-name ExpenseTracker \
  --attribute-definitions \
    AttributeName=userId,AttributeType=S \
    AttributeName=expenseDate,AttributeType=S \
  --key-schema \
    AttributeName=userId,KeyType=HASH \
    AttributeName=expenseDate,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region ap-southeast-2

# Budgets table
aws dynamodb create-table \
  --table-name ExpenseBudgets \
  --attribute-definitions \
    AttributeName=userId,AttributeType=S \
    AttributeName=category,AttributeType=S \
  --key-schema \
    AttributeName=userId,KeyType=HASH \
    AttributeName=category,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region ap-southeast-2
```

## Usage

### CLI

```bash
python cli_agent.py
```

```
Expense Tracker Multi-Agent System
Type 'exit' or 'quit' to leave
----------------------------------------
Enable reflection loop? (y/n): y

You: What's my biggest spending category and how can I reduce it?

[Coordinator] Generating initial response...
[Initial Response] Your biggest spending category is...
[Reflection] Iteration 1/2 - Evaluating response quality...
[Reflection] APPROVED - Response includes specific numbers and actionable advice
[Complete] Final response ready

Agent: Your biggest spending category is **uncategorized** at SGD 203.40...
```

### Streamlit

```bash
streamlit run app.py
```

## Project Structure

```
ExpenseTracker/
├── app.py                    # Streamlit web interface
├── cli_agent.py              # Command-line interface
│
├── orchestration/            # Multi-agent system
│   ├── __init__.py
│   ├── coordinator.py        # Coordinator + reflection loop
│   └── specialists.py        # Query, Analyst, Budget agents
│
├── tools/                    # Function tools for agents
│   ├── __init__.py
│   ├── db.py                 # DynamoDB connection
│   ├── expenses.py           # Expense retrieval
│   ├── summary.py            # Spending aggregation
│   ├── budgets.py            # Budget management
│   ├── categories.py         # Category operations
│   └── analysis.py           # Trend analysis
│
├── ingestion/                # Data ingestion pipeline
│   ├── __init__.py
│   ├── gmail_reader.py       # Gmail API integration
│   └── lambda_function.py    # AWS Lambda handler
│
└── utils/                    # Shared utilities
    ├── __init__.py
    └── monitoring.py         # Logging and retry logic
```

## Example Queries

```
"Show me my last 10 expenses"
"What did I spend at NTUC last month?"
"Break down my spending by category"
"Analyze my spending trends over the last 3 months"
"Are there any unusual expenses I should know about?"
"How can I save money this month?"
"Set a budget of 300 for food"
"Am I over budget on anything?"
```

## Tech Stack

- **Agent Framework**: OpenAI Agents SDK
- **Database**: AWS DynamoDB
- **Serverless**: AWS Lambda
- **Email**: Gmail API
- **Frontend**: Streamlit
- **Language**: Python 3.9+

## License

MIT
