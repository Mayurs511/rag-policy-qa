#!/bin/bash

# Setup script for RAG Policy Q&A System
# NeuraAI AI Engineer Intern Assignment

echo "=================================="
echo "RAG System Setup"
echo "=================================="
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
required_version="3.8"

if (( $(echo "$python_version >= $required_version" | bc -l) )); then
    echo "✓ Python $python_version detected (>= 3.8 required)"
else
    echo "✗ Python $python_version is too old. Please install Python 3.8 or newer."
    exit 1
fi

# Create virtual environment
echo ""
echo "📌 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠ Virtual environment already exists. Skipping."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "📌 Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "📌 Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"

# Install requirements
echo ""
echo "📌 Installing dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements.txt --quiet

if [ $? -eq 0 ]; then
    echo "✓ All dependencies installed successfully"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Check for API key
echo ""
echo "📌 Checking for ANTHROPIC_API_KEY..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠ ANTHROPIC_API_KEY not set"
    echo ""
    echo "Please set your API key:"
    echo "  export ANTHROPIC_API_KEY='your-api-key-here'"
    echo ""
    echo "Or add it to your ~/.bashrc or ~/.zshrc:"
    echo "  echo 'export ANTHROPIC_API_KEY=\"your-key\"' >> ~/.bashrc"
else
    echo "✓ ANTHROPIC_API_KEY is set"
fi

# Check for PDF file
echo ""
echo "📌 Checking for policy document..."
if [ -f "policy_document.pdf" ]; then
    echo "✓ policy_document.pdf found"
else
    echo "⚠ policy_document.pdf not found"
    echo ""
    echo "Please add your doTERRA policy PDF to this directory:"
    echo "  1. Place your PDF in the project root"
    echo "  2. Rename it to: policy_document.pdf"
fi

# Final instructions
echo ""
echo "=================================="
echo "Setup Complete! 🎉"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Set ANTHROPIC_API_KEY (if not already set)"
echo "  2. Add policy_document.pdf to this directory"
echo "  3. Run: python demo.py"
echo ""
echo "To activate the virtual environment later:"
echo "  source venv/bin/activate"
echo ""
echo "For more information, see README.md"
echo ""
