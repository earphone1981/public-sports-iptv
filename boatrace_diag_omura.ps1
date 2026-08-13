# BOAT RACE 大村 Playback API 診断
# GitHub Actions (pwsh) 用

$ErrorActionPreference = "Continue"

$jst = [System.TimeZoneInfo]::FindSystemTimeZoneById("Asia/Tokyo")
$nowJst = [System.TimeZoneInfo]::ConvertTime([DateTimeOffset]::UtcNow, $jst)
$d = $nowJst.ToString("yyyyMMdd")

$code = "24omura"
$url = "https://playback.api.streaks.jp/v1/projects/cp-boatrace-prod/medias/ref:lm-br-$code-tokyo-$d`?audio_only=false"

$headers = @{
    "Origin"     = "https://front.player.boatrace-cdn.jp"
    "Referer"    = "https://front.player.boatrace-cdn.jp/"
    "User-Agent" = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
    "Accept"     = "application/json, text/plain, */*"
}

Write-Host "=========================================="
Write-Host " BOAT RACE Playback API 診断 - 大村"
Write-Host " JST日付 : $d"
Write-Host " URL     : $url"
Write-Host "=========================================="

try {
    $r = Invoke-WebRequest `
        -Uri $url `
        -Headers $headers `
        -Method Get `
        -TimeoutSec 30 `
        -SkipHttpErrorCheck

    Write-Host ""
    Write-Host "HTTP Status : $($r.StatusCode)"
    Write-Host "Content-Type: $($r.Headers.'Content-Type')"
    Write-Host "Server      : $($r.Headers.Server)"

    $body = [string]$r.Content
    Write-Host "Body length : $($body.Length)"

    Write-Host ""
    Write-Host "----- BODY先頭 最大1500文字 -----"
    if ($body.Length -gt 1500) {
        Write-Host $body.Substring(0,1500)
    } else {
        Write-Host $body
    }
    Write-Host "----- BODYここまで -----"

    Write-Host ""
    try {
        $j = $body | ConvertFrom-Json -ErrorAction Stop
        Write-Host "JSON parse  : OK" -ForegroundColor Green

        if ($null -ne $j.sources) {
            Write-Host "sources     : EXISTS"
            Write-Host "sources数   : $(@($j.sources).Count)"

            $i = 0
            foreach ($s in @($j.sources)) {
                $i++
                Write-Host "source[$i] type: $($s.type)"
                Write-Host "source[$i] src : $($s.src)"
            }
        } else {
            Write-Host "sources     : NOT FOUND" -ForegroundColor Yellow
        }

        if ($j.message) { Write-Host "message     : $($j.message)" }
        if ($j.error)   { Write-Host "error       : $($j.error)" }
        if ($j.code)    { Write-Host "code        : $($j.code)" }
    }
    catch {
        Write-Host "JSON parse  : FAILED" -ForegroundColor Red
        Write-Host "Parse error : $($_.Exception.Message)"
    }
}
catch {
    Write-Host ""
    Write-Host "REQUEST EXCEPTION" -ForegroundColor Red
    Write-Host $_.Exception.Message

    if ($_.Exception.Response) {
        try {
            Write-Host "Status: $([int]$_.Exception.Response.StatusCode)"
        } catch {}
    }
}

Write-Host ""
Write-Host "=========================================="
Write-Host " 診断終了"
Write-Host "=========================================="
