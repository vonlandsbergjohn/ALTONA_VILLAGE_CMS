$loginResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"vonlandsbergjohn@gmail.com","password":"dGdFHLCJxx44ykq"}'
$token = $loginResponse.access_token
Write-Host "Login successful. Token: $($token.Substring(0,50))..."

# Test getting profile
try {
    $profileResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/profile" -Headers @{"Authorization"="Bearer $token"}
    Write-Host "Profile Response:"
    $profileResponse | ConvertTo-Json -Depth 5
} catch {
    Write-Host "Profile Error: $_"
}

# Test getting residents (admin endpoint)
try {
    $residentsResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/admin/residents" -Headers @{"Authorization"="Bearer $token"}
    Write-Host "Residents Count: $($residentsResponse.Count)"
    Write-Host "First Resident:"
    if ($residentsResponse.Count -gt 0) {
        $residentsResponse[0] | ConvertTo-Json -Depth 3
    }
} catch {
    Write-Host "Residents Error: $_"
}
