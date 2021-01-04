#Rogue Access DB Scan -- Requires server 2016  or WMF 5.1
$numberDays = 365*2
$cutOffDate = (Get-Date).AddDays(-$numberDays)
Get-PSDrive -PSProvider FileSystem |
ForEach-Object {Get-ChildItem -LiteralPath $_.Root -Include *.mdb,*.accdb,*.mde,*.accde -File -Recurse } |
Where-Object {$_.LastAccessTime -le $cutOffDate} |
Select-Object -Property * | Export-Excel .\RogueDBScanResults.xlsx