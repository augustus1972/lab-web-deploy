param(
    [string]$BuildNumber,
    [string]$GitCommit,
    [string]$TemplateContent
)

$hostname = $env:COMPUTERNAME
$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

try {
    $token = Invoke-RestMethod -Method PUT -Uri "http://169.254.169.254/latest/api/token" `
        -Headers @{"X-aws-ec2-metadata-token-ttl-seconds"="60"} -TimeoutSec 3
    $instance_id = Invoke-RestMethod -Uri "http://169.254.169.254/latest/meta-data/instance-id" `
        -Headers @{"X-aws-ec2-metadata-token"=$token}
    $az = Invoke-RestMethod -Uri "http://169.254.169.254/latest/meta-data/placement/availability-zone" `
        -Headers @{"X-aws-ec2-metadata-token"=$token}
} catch {
    $instance_id = "unknown"
    $az = "unknown"
}

$html = $TemplateContent `
    -replace '__HOSTNAME__', $hostname `
    -replace '__AZ__', $az `
    -replace '__INSTANCE_ID__', $instance_id `
    -replace '__BUILD_NUMBER__', $BuildNumber `
    -replace '__GIT_COMMIT__', $GitCommit.Substring(0, [Math]::Min(7, $GitCommit.Length)) `
    -replace '__DEPLOY_TIME__', $now

# Backup poprzedniej wersji
if (Test-Path "C:\inetpub\wwwroot\index.html") {
    Copy-Item "C:\inetpub\wwwroot\index.html" "C:\inetpub\wwwroot\index.html.bak" -Force
}

[System.IO.File]::WriteAllText("C:\inetpub\wwwroot\index.html", $html, (New-Object System.Text.UTF8Encoding $false))

# Health check lokalny
Start-Sleep -Seconds 2
$local = Invoke-WebRequest "http://localhost" -UseBasicParsing -TimeoutSec 5
if ($local.StatusCode -ne 200) {
    Write-Error "Local health check failed: HTTP $($local.StatusCode)"
    exit 1
}

Write-Host "OK Deployed on $hostname ($az) — build #$BuildNumber"