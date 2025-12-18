# PowerShell script to replace em dashes with LaTeX en-dashes
# This script only replaces em dashes that are surrounded by text

$projectPath = "C:\Users\oulla\Desktop\SQU\competetions\sumo robot\fyp\report"

# Get all .tex files recursively
Get-ChildItem -Path $projectPath -Filter *.tex -Recurse | ForEach-Object {
    $filePath = $_.FullName
    Write-Host "Processing: $filePath"
    
    # Read the file content
    $content = Get-Content $filePath -Raw -Encoding UTF8
    
    # Replace em dashes that are between words
    $newContent = $content -replace '(\w|\s)—(\w|\s)', '$1--$2'
    
    # Write back to file if changes were made
    if ($content -ne $newContent) {
        $newContent | Set-Content $filePath -Encoding UTF8 -NoNewline
        Write-Host "  Updated em dashes in $($_.Name)"
    } else {
        Write-Host "  No em dashes found in $($_.Name)"
    }
}

Write-Host ""
Write-Host "Done! All em dashes have been replaced."
