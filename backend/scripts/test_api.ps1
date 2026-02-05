$Base = "http://127.0.0.1:5000/api"
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

function Post-Json($url, $obj) {
  $json = $obj | ConvertTo-Json -Depth 10
  Write-Host "`nPOST $url" -ForegroundColor Cyan
  try {
    Invoke-RestMethod -Method Post -Uri $url -ContentType "application/json" -Body $json -WebSession $session
  } catch {
    Write-Host "ERROR:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
      Write-Host $_.ErrorDetails.Message
    }
    throw
  }
}

function Get-Json($url) {
  Write-Host "`nGET $url" -ForegroundColor Cyan
  try {
    Invoke-RestMethod -Method Get -Uri $url -WebSession $session
  } catch {
    Write-Host "ERROR:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
      Write-Host $_.ErrorDetails.Message
    }
    throw
  }
}

# ---------- 1) REGISTER ----------
$registerBody = @{
  name      = "Alexis"
  email    = "alexis.test59@local.dev"
  password = "Test1234!"
  pro      = $false
}

Post-Json "$Base/auth/register" $registerBody

# ---------- 2) LOGIN ----------
$loginBody = @{
  email    = "alexis.test59@local.dev"
  password = "Test1234!"
}

Post-Json "$Base/auth/login" $loginBody

# ---------- 3) TEST “ME” / PROFIL (si tu as une route) ----------
# Essaie un de ces endpoints selon ton projet (garde celui qui existe)
# Get-Json "$Base/auth/me"
# Get-Json "$Base/users/me"
# Get-Json "$Base/me"
