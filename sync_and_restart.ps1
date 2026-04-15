# OpenHarness Enterprise - Sync and Restart Script
# Server: 10.1.7.155 (ai-app / asb#1234)

$HostIP = "10.1.7.155"
$User = "ai-app"
$Password = "asb#1234"
$LocalFile = "D:\openharness-enterprise\.env"
$RemotePath = "/home/ai-app/oh-enterprise-1.0.0/.env"

Write-Host "[*] Step 1: Upload .env file to server"
Write-Host "    Run this command manually (password will be prompted):"
Write-Host ""
Write-Host "    scp $LocalFile ${User}@${HostIP}:${RemotePath}"
Write-Host ""
Write-Host "    Password: $Password"
Write-Host ""

Write-Host "[*] Step 2: SSH to server and restart service"
Write-Host "    Run these commands manually:"
Write-Host ""
Write-Host "    ssh ${User}@${HostIP}"
Write-Host "    Password: $Password"
Write-Host ""
Write-Host "    Then on server:"
Write-Host "    cd /home/ai-app/oh-enterprise-1.0.0"
Write-Host "    pkill -f 'oh-enterprise'"
Write-Host "    nohup uv run oh-enterprise start --port 8000 > logs/server.log 2>&1 &"
Write-Host ""

# Try automatic if SSH key is available
$sshKey = "$env:USERPROFILE\.ssh\id_rsa"
if (Test-Path $sshKey) {
    Write-Host "[*] SSH key found, attempting automatic sync..."
    
    # Try scp
    $scpResult = scp $LocalFile "${User}@${HostIP}:${RemotePath}" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] File uploaded successfully"
        
        # Try ssh
        ssh ${User}@${HostIP} "cd /home/ai-app/oh-enterprise-1.0.0 && pkill -f 'oh-enterprise' ; nohup uv run oh-enterprise start --port 8000 > logs/server.log 2>&1 &"
        Write-Host "[OK] Service restart command sent"
    } else {
        Write-Host "[!] Automatic sync failed, please use manual steps above"
        Write-Host $scpResult
    }
} else {
    Write-Host "[!] No SSH key found, please use manual steps above"
}