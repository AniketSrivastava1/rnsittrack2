Write-Host "========================================="
Write-Host "DevReady: Real-World Experience Simulator"
Write-Host "========================================="
Write-Host ""
Write-Host "1. Installing 'devready' CLI globally via pip..."
pip install -e .
Write-Host ""

Write-Host "2. Scaffolding the 'cursed' mock project..."
python create_simulation.py
Write-Host ""

Write-Host "3. Done! Please dive into the project and try it out:"
Write-Host "---------------------------------------------------"
Write-Host "  cd ~\devready_cursed_project"
Write-Host "  devready scan"
Write-Host "  devready fix"
Write-Host "---------------------------------------------------"
