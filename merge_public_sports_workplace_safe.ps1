# ============================================================
# Public Sports M3U merge - Workplace PC / SAFE / EPG / JRA 8ch
#
# ・一旦 temporary ファイルへ生成
# ・途中失敗 / ボート0ch の場合は public_sports.m3u を上書きしない
# ・正常生成時のみ public_sports.m3u を置き換える
# ・置換前の public_sports.m3u は public_sports_backup.m3u に保存
# ・中央競馬は HQ 4ch + LQ 4ch
# ・HQ/LQ は同じ tvg-id を共有し、同じEPGを表示
# ============================================================

$ErrorActionPreference = "Stop"

$base = $PSScriptRoot
$outPath    = Join-Path $base "public_sports.m3u"
$tempPath   = Join-Path $base "public_sports_new.m3u"
$backupPath = Join-Path $base "public_sports_backup.m3u"
$boatPath   = Join-Path $base "boatrace_today.m3u"

$root = "https://raw.githubusercontent.com/earphone1981/public-sports-iptv/main"
$epgUrl = "$root/epg.xml"

$remote = @(
    @{ Label="競輪";       File="keirin_master.m3u" },
    @{ Label="地方競馬";   File="keiba_master.m3u" },
    @{ Label="オートレース"; File="autorace_master.m3u" }
)

# HQ/LQで Id を同じにすることで同じEPGを表示
$jra = @(
    @{ Id="jra.gch";      TvgName="グリーンチャンネル"; Name="グリーンチャンネル（高画質）"; File="gchmain.m3u8" },
    @{ Id="jra.gch";      TvgName="グリーンチャンネル"; Name="グリーンチャンネル（低画質）"; File="gchmain_LQ.m3u8" },

    @{ Id="jra.east";     TvgName="JRA EAST"; Name="JRA EAST（高画質）"; File="EAST_test.m3u8" },
    @{ Id="jra.east";     TvgName="JRA EAST"; Name="JRA EAST（低画質）"; File="EAST_test_LQ.m3u8" },

    @{ Id="jra.west";     TvgName="JRA WEST"; Name="JRA WEST（高画質）"; File="WEST_master .m3u8" },
    @{ Id="jra.west";     TvgName="JRA WEST"; Name="JRA WEST（低画質）"; File="WEST_master_LQ.m3u8" },

    @{ Id="jra.hokkaido"; TvgName="JRA HOKKAIDO"; Name="JRA HOKKAIDO（高画質）"; File="hokaido_master (1).m3u8" },
    @{ Id="jra.hokkaido"; TvgName="JRA HOKKAIDO"; Name="JRA HOKKAIDO（低画質）"; File="hokaido_master_LQ.m3u8" }
)

function Encode-FileName([string]$name) {
    return [System.Uri]::EscapeDataString($name).Replace("%2F","/")
}

function Get-Entries([string[]]$lines) {
    $result = New-Object System.Collections.Generic.List[object]

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i].Trim()

        if ($line.StartsWith("#EXTINF:")) {
            for ($j = $i + 1; $j -lt $lines.Count; $j++) {
                $n = $lines[$j].Trim()

                if (-not $n) { continue }
                if ($n.StartsWith("#EXTINF:")) { break }

                if (-not $n.StartsWith("#")) {
                    $result.Add([PSCustomObject]@{
                        ExtInf = $line
                        Url    = $n
                    })
                    break
                }
            }
        }
    }

    return $result
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$out = New-Object System.Collections.Generic.List[string]
$out.Add("#EXTM3U url-tvg=`"$epgUrl`"")
$out.Add("")

$total = 0

try {
    # --------------------------------------------------------
    # 競輪・地方競馬・オート
    # --------------------------------------------------------
    foreach ($r in $remote) {
        $url = "$root/$(Encode-FileName $r.File)"

        Write-Host "$($r.Label): GitHubから取得中 ... " -NoNewline

        $text = (Invoke-WebRequest `
            -Uri $url `
            -UseBasicParsing `
            -TimeoutSec 30 `
            -ErrorAction Stop
        ).Content

        $entries = Get-Entries ($text -replace "`r`n","`n" -split "`n")

        if ($entries.Count -eq 0) {
            throw "$($r.Label) が0chです。更新を中止します。"
        }

        Write-Host "$($entries.Count) ch" -ForegroundColor Green

        $out.Add("## $($r.Label)")

        foreach ($e in $entries) {
            $out.Add($e.ExtInf)
            $out.Add($e.Url)
            $out.Add("")
        }

        $total += $entries.Count
    }

    # --------------------------------------------------------
    # ボート
    # --------------------------------------------------------
    if (-not (Test-Path $boatPath)) {
        throw "boatrace_today.m3u がありません。更新を中止します。"
    }

    $boatText = [System.IO.File]::ReadAllText($boatPath)

    if ($boatText -match 'これは昨日のリプレイです') {
        throw "ボートが前回リプレイ状態です。本日分取得後に再実行してください。"
    }

    $boatEntries = Get-Entries ($boatText -replace "`r`n","`n" -split "`n")

    if ($boatEntries.Count -eq 0) {
        throw "ボートが0chです。public_sports.m3u は前回版を保持します。"
    }

    Write-Host "ボートレース: $($boatEntries.Count) ch（当日取得分）" -ForegroundColor Green

    $out.Add("## ボートレース")

    foreach ($e in $boatEntries) {
        $out.Add($e.ExtInf)
        $out.Add($e.Url)
        $out.Add("")
    }

    $total += $boatEntries.Count

    # --------------------------------------------------------
    # 中央競馬 HQ4 + LQ4
    # --------------------------------------------------------
    $out.Add("## 中央競馬")

    foreach ($c in $jra) {
        $url = "$root/$(Encode-FileName $c.File)"

        $out.Add(
            "#EXTINF:-1 tvg-id=`"$($c.Id)`" tvg-name=`"$($c.TvgName)`" group-title=`"中央競馬`",$($c.Name)"
        )
        $out.Add($url)
        $out.Add("")

        Write-Host "中央競馬: $($c.Name) <- $($c.File)"
        $total++
    }

    # --------------------------------------------------------
    # 一旦 temporary に生成
    # --------------------------------------------------------
    [System.IO.File]::WriteAllText(
        $tempPath,
        (($out -join "`r`n").TrimEnd() + "`r`n"),
        $utf8NoBom
    )

    if (-not (Test-Path $tempPath)) {
        throw "一時ファイル生成に失敗しました。"
    }

    $tempInfo = Get-Item $tempPath

    if ($tempInfo.Length -lt 1000) {
        throw "生成結果が小さすぎるため更新を中止しました。"
    }

    # --------------------------------------------------------
    # 正常時だけ置換
    # --------------------------------------------------------
    if (Test-Path $outPath) {
        Copy-Item $outPath $backupPath -Force
    }

    Move-Item $tempPath $outPath -Force

    Write-Host ""
    Write-Host "=============================================="
    Write-Host " public_sports.m3u 安全更新 完了！" -ForegroundColor Green
    Write-Host " 合計チャンネル数: $total"
    Write-Host " ボート当日取得: $($boatEntries.Count) ch"
    Write-Host " 中央競馬: 8 ch（高画質4 + 低画質4）"
    Write-Host " EPG: $epgUrl"
    Write-Host " 出力: $outPath"

    if (Test-Path $backupPath) {
        Write-Host " バックアップ: $backupPath"
    }

    Write-Host "=============================================="
}
catch {
    if (Test-Path $tempPath) {
        Remove-Item $tempPath -Force -ErrorAction SilentlyContinue
    }

    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Yellow
    Write-Host " public_sports.m3u は更新しませんでした。" -ForegroundColor Yellow
    Write-Host " 前回版をそのまま保持します。" -ForegroundColor Cyan
    Write-Host " 理由: $($_.Exception.Message)"
    Write-Host "==============================================" -ForegroundColor Yellow

    exit 0
}

exit 0
