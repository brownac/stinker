#!/bin/bash

echo "========================================="
echo "AI Code Review Bot - Setup Script"
echo "========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3."
    exit 1
fi

echo "✅ pip3 found: $(pip3 --version)"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "⚠️  Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and add your credentials:"
    echo "   - GITHUB_TOKEN: Personal Access Token with repo access"
    echo "   - GITHUB_WEBHOOK_SECRET: Secret for webhook verification"
    echo "   - AI Provider credentials (OpenAI, Anthropic, or Custom)"
    echo ""
else
    echo "⚠️  .env file already exists. Skipping..."
    echo ""
fi

# Initialize database
echo "Initializing database..."
python3 << PYTHON
from database import Database
import os

db_path = os.getenv('DATABASE_PATH', 'ai_reviews.db')
db = Database(db_path)
print("✅ Database initialized at:", db_path)
PYTHON
echo ""

# Create data directory
mkdir -p data
echo "✅ Data directory created"
echo ""

# Display next steps
echo "========================================="
echo "Setup Complete! 🎉"
echo "========================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Configure your credentials in .env file:"
echo "   nano .env"
echo ""
echo "2. Start the application:"
echo "   source venv/bin/activate"
echo "   python3 app.py"
echo ""
echo "3. The dashboard will be available at:"
echo "   http://localhost:5000"
echo ""
echo "4. Set up GitHub webhook (see README.md for details):"
echo "   - Go to repository Settings > Webhooks > Add webhook"
echo "   - Payload URL: https://your-domain.com/webhook"
echo "   - Content type: application/json"
echo "   - Secret: [Your GITHUB_WEBHOOK_SECRET from .env]"
echo "   - Events: Pull requests"
echo ""
echo "5. Test the bot:"
echo "   - Analyze a repository to learn patterns"
echo "   - Create a PR and watch for automatic review"
echo "   - Or use manual review from dashboard"
echo ""
echo "For production deployment, see README.md"
echo ""
