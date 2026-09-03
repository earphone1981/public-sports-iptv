param(
    [string]$PublicPath = "public_sports.m3u",
    [string]$BoatPath = "boatrace_today.m3u"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $PublicPath)) { throw "Missing $PublicPath" }
if (!(Test-Path $BoatPath)) { throw "Missing $BoatPath" }

$public = Get-Content $PublicPath -Raw -Encoding UTF8
$boat = Get-Content $BoatPath -Raw -Encoding UTF8

$boatBody = ($boat -replace '^\uFEFF?#EXTM3U\s*', '').Trim()
if (-not $boatBody) { throw "BOAT playlist is empty" }

$section = "## ボートレース`n$boatBody`n"

# Replace the existing BOAT section up to the next ## heading (or EOF).
$pattern = '(?ms)^## ボートレース\s*\r?\n.*?(?=^## |\z)'
if ([regex]::IsMatch($public, $pattern)) {
    $public = [regex]::Replace($public, $pattern, $section, 1)
}
else {
    $public = $public.TrimEnd() + "`n`n" + $section
}

$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Resolve-Path $PublicPath), $public.TrimEnd() + "`n", $utf8)

$count = ([regex]::Matches($boatBody, '(?m)^#EXTINF:')).Count
Write-Host "Merged BOAT into public_sports.m3u: entries=$count"
