param(
  [string]$OutFile = "hr_logbook_db.sql",
  [string]$DbUser = "root",
  [string]$DbName = "hr_logbook_db"
)

Write-Host "Exporting MySQL database '$DbName' to $OutFile"
mysqldump -u $DbUser -p $DbName > $OutFile
if ($LASTEXITCODE -eq 0) { Write-Host "Export complete." } else { Write-Host "Export failed." }
