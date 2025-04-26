#!/bin/bash

REPO_URL="git@github.com:Prokope45/DF.git"

# Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    git init
    echo "Initialized new Git repository"
fi

# Configure remote repository
git remote remove origin 2>/dev/null
git remote add origin $REPO_URL
echo "Added remote repository: $REPO_URL"

# Add all files in the current directory
git add "/Users/pengchen/Documents/DataFest_2025/tech_hub_analysis.py"
echo "Added all files to staging area"

# Prompt for commit message
echo "Enter commit message:"
read commit_message

# Commit changes with the provided message
git commit -m "$commit_message"
echo "Committed changes with message: $commit_message"

# Push changes to remote repository
echo "Pushing changes to remote repository..."
git push -u origin main || git push -u origin master

echo "Done! Your changes have been pushed to the repository."
