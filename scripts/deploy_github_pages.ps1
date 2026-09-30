# deploy_github_pages.ps1
# Automates Milestone 2 deployment tasks:
# 1. Stage and commit M1/M2 artifacts
# 2. Link/create remote GitHub repository
# 3. Push master branch
# 4. Configure GitHub Pages
# 5. Execute 89 unit tests

$ErrorActionPreference = "Continue"

Write-Host "=== 1. Staging M1 files in Git ==="
git add .gitignore .nojekyll .github/workflows/centinela_metricas.yml scripts/centinela_refresh.py hub_engine.py tests/test_hub.py
git status

Write-Host "=== 2. Committing to master ==="
git commit -m "feat(centinela): implement cloud centinela workflow and active-store shielding (§ 7)"

Write-Host "=== 3. Remote Repository Setup ==="
$remotes = git remote
if ($remotes -contains "origin") {
    Write-Host "Remote 'origin' already exists: $(git remote get-url origin)"
    git push -u origin master
} else {
    Write-Host "Creating/linking remote repository via gh..."
    gh repo create anderssonfranco78-jpg/multi_account_hub --public --source=. --remote=origin --push
    if ($LASTEXITCODE -ne 0) {
        Write-Host "gh repo create returned non-zero. Attempting git remote add & push..."
        git remote add origin https://github.com/anderssonfranco78-jpg/multi_account_hub.git
        git push -u origin master
    }
}

Write-Host "=== 4. Configuring GitHub Pages ==="
# Try POST with field parameters
gh api -X POST /repos/anderssonfranco78-jpg/multi_account_hub/pages -F "source[branch]=master" -F "source[path]=/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "POST /pages failed or already exists. Attempting PUT /pages..."
    gh api -X PUT /repos/anderssonfranco78-jpg/multi_account_hub/pages -F "source[branch]=master" -F "source[path]=/"
}

Write-Host "=== 5. Querying GitHub Pages Status ==="
gh api /repos/anderssonfranco78-jpg/multi_account_hub/pages

Write-Host "=== 6. Running Unit Tests ==="
python -m unittest discover tests

Write-Host "=== Deployment script completed ==="
