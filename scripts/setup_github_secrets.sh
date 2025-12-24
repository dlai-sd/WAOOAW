#!/bin/bash
# Setup GitHub Secrets for WAOOAW Infrastructure
# Run this script locally, NOT in GitHub Actions

set -e

REPO="dlai-sd/WAOOAW"

echo "🔐 Setting up GitHub Secrets for WAOOAW infrastructure..."

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not found. Install it first:"
    echo "   https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI"
    echo "   Run: gh auth login"
    exit 1
fi

echo ""
echo "📝 Adding DATABASE_URL secret..."
gh secret set DATABASE_URL \
    --repo "$REPO" \
    --body "postgresql://postgres:20251212SD*&!@db.xgxhumsivyikvxzgueho.supabase.co:5432/postgres"

echo "✅ DATABASE_URL added"

echo ""
echo "📝 Adding PINECONE_API_KEY secret..."
gh secret set PINECONE_API_KEY \
    --repo "$REPO" \
    --body "pcsk_1rCgp_KFw1Eab2dPbTJ82Xf8sbvgP1UVkTFmi9APATPoYeGmfD9ziEc8s4pH4LGtk1zZu"

echo "✅ PINECONE_API_KEY added"

echo ""
echo "📝 Adding PINECONE_INDEX_HOST secret..."
gh secret set PINECONE_INDEX_HOST \
    --repo "$REPO" \
    --body "wowvision-memory-hf97t0h.svc.aped-4627-b74a.pinecone.io"

echo "✅ PINECONE_INDEX_HOST added"

echo ""
echo "📝 Adding PINECONE_INDEX_NAME secret..."
gh secret set PINECONE_INDEX_NAME \
    --repo "$REPO" \
    --body "wowvision-memory"

echo "✅ PINECONE_INDEX_NAME added"

echo ""
echo "✅ All secrets configured successfully!"
echo ""
echo "⏸️  ANTHROPIC_API_KEY not added yet (waiting for credit card)"
echo "   Add it later with:"
echo "   gh secret set ANTHROPIC_API_KEY --repo $REPO --body 'sk-ant-api03-...'"
echo ""
echo "🎉 Infrastructure secrets ready!"
