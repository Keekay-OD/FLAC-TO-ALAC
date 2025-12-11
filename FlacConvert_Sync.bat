@echo off
robocopy "H:\Projects Code\FlacConvert" "X:\Keekay\FlacConvert" /MIR /R:3 /W:5 /LOG:"H:\Projects Code\FlacConvert_sync.log" /NP
exit /b 0