param(
  [ValidateSet('zip','dir')]
  [string]$Out = 'zip',
  [string]$OutName = 'hr-logbook-package'
)

Write-Host "Exporting database..."
.\export_db.ps1 -OutFile hr_logbook_db.sql

$items = @('app.py','routes','templates','models','Employees','resources','requirements.txt','.env.example','hr_logbook_db.sql')
if ($Out -eq 'zip') {
  $zip = "$OutName.zip"
  if (Test-Path $zip) { Remove-Item $zip }
  Compress-Archive -Path $items -DestinationPath $zip -Force
  Write-Host "Created $zip"
} else {
  $dir = "$OutName"
  if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
  New-Item -Path $dir -ItemType Directory
  foreach ($i in $items) { Copy-Item $i -Destination $dir -Recurse -Force }
  Write-Host "Created folder $dir"
}
