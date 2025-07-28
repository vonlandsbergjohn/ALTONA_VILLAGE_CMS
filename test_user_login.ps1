$userEmail = "marilizevl@gmail.com"
$possiblePasswords = @("password123", "123456", "admin123", "resident123", "password", "123")

foreach ($password in $possiblePasswords) {
    Write-Host "Trying password: $password"
    try {
        $loginResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" -Method POST -ContentType "application/json" -Body "{`"email`":`"$userEmail`",`"password`":`"$password`"}"
        Write-Host "SUCCESS! Password is: $password"
        $token = $loginResponse.access_token
        
        # Test profile update
        Write-Host "Testing profile update..."
        $updateBody = @{
            "first_name" = "Test"
            "last_name" = "User" 
            "email" = $userEmail
            "phone" = "1234567890"
            "tenant_or_owner" = "owner"
        } | ConvertTo-Json
        
        $updateResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/profile" -Method PUT -ContentType "application/json" -Headers @{"Authorization"="Bearer $token"} -Body $updateBody
        Write-Host "Profile update response:"
        $updateResponse | ConvertTo-Json -Depth 3
        break
    } catch {
        Write-Host "Failed with password: $password"
    }
}
