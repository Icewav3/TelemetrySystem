# PowerShell client script to send test telemetry data
param(
    #laptop vpn ip = "10.243.11.239" 
    #deskop ip = " 10.20.5.27"
    [string]$ServerIP = "10.20.5.27",
    [int]$Port = 8080,
    [string]$MachineID = $env:COMPUTERNAME,
    [int]$DurationSeconds = 60,
    [int]$IntervalMs = 100
)

$url = "http://${ServerIP}:${Port}/telemetry"
$startTime = Get-Date
$counter = 0

Write-Host "Sending telemetry to $url as $MachineID" -ForegroundColor Green
Write-Host "Duration: $DurationSeconds seconds, Interval: $IntervalMs ms" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop early`n" -ForegroundColor Yellow

try {
    while (((Get-Date) - $startTime).TotalSeconds -lt $DurationSeconds) {
        $counter++
        
        # Simulate game telemetry data via sin wave
        $telemetryData = @{
            machine_id = $MachineID
            frame = $counter
            player_pos = @{
                x = [math]::Sin($counter * 0.1) * 100
                y = [math]::Cos($counter * 0.1) * 100
                z = 0
            }
            fps = Get-Random -Minimum 55 -Maximum 65
            memory_mb = Get-Random -Minimum 2000 -Maximum 3000
            active_enemies = Get-Random -Minimum 0 -Maximum 10
        } | ConvertTo-Json -Compress
        
        # Send POST request
        try {
            $response = Invoke-WebRequest -Uri $url -Method POST -Body $telemetryData -ContentType "application/json" -UseBasicParsing -TimeoutSec 2
            
            if ($counter % 50 -eq 0) {
                Write-Host "Sent $counter packets" -ForegroundColor Green
            }
        }
        catch {
            Write-Host "Failed to send packet $counter : $_" -ForegroundColor Red
        }
        
        Start-Sleep -Milliseconds $IntervalMs
    }
}
catch {
    Write-Host "`nStopped by user" -ForegroundColor Yellow
}

Write-Host "`nTest complete. Sent $counter packets" -ForegroundColor Green