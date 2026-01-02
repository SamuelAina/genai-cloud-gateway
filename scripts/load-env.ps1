$lines = Get-Content .env

foreach ($line in $lines) {
  if ($line -match "^\s*#") { continue }
  if ($line -match "^\s*$") { continue }

  $kv = $line.Split("=", 2)
  if ($kv.Count -lt 2) { continue }

  $name  = $kv[0].Trim()
  $value = $kv[1].Trim()

  # strip optional surrounding quotes
  if ($value.StartsWith('"') -and $value.EndsWith('"')) {
    $value = $value.Trim('"')
  }

  [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
}

Write-Host "Loaded .env into this PowerShell session."
