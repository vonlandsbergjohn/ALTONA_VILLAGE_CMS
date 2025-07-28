$loginResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"vonlandsbergjohn@gmail.com","password":"dGdFHLCJxx44ykq"}'
$token = $loginResponse.access_token
$userId = "0a026592-74f2-4880-bf66-124b1fc258c2"

Write-Host "Testing resident status update for user: $userId"

# Test updating resident status
try {
    $updateBody = @{
        "resident_status_change" = "resident"
    } | ConvertTo-Json
    
    Write-Host "Sending update with body: $updateBody"
    
    $updateResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/admin/residents/$userId" -Method PUT -ContentType "application/json" -Headers @{"Authorization"="Bearer $token"} -Body $updateBody
    
    Write-Host "Update Response:"
    $updateResponse | ConvertTo-Json -Depth 3
    
} catch {
    Write-Host "Update Error: $_"
    Write-Host "Error Details: $($_.Exception.Response)"
}
