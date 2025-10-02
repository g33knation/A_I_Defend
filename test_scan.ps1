$result = Invoke-RestMethod -Uri 'http://localhost:8000/api/scans/start' -Method Post -ContentType 'application/json' -InFile 'test_scan.json'
Write-Output "Scan started:"
Write-Output $result
Start-Sleep -Seconds 3
Write-Output "`nChecking scan status:"
Invoke-RestMethod -Uri "http://localhost:8000/api/scans/$($result.scan_id)" -Method Get
