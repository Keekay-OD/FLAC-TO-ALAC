; ============================================================
; VibesFLAC Installer – Fully Branded, Dark Theme, MUI2
; ============================================================

!include "MUI2.nsh"
!include "LogicLib.nsh"

!define APPNAME "VibesFLAC Converter"
!define APPVERSION "1.0.0"
!define APPEXENAME "VibesFLACtoALAC.exe"

OutFile "VibesFLAC-Setup-${APPVERSION}.exe"
InstallDir "$PROGRAMFILES64\VibesFLAC"

; ------------------------------------------------------------
; BRANDING: Custom Welcome / Finish Images
; ------------------------------------------------------------
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "installer\wizard_small.bmp"

!define MUI_WELCOMEFINISHPAGE_BITMAP "installer\wizard_big.bmp"

; ------------------------------------------------------------
; CUSTOM PAGE TEXT
; ------------------------------------------------------------
!define MUI_WELCOMEPAGE_TITLE "Welcome to VibesFLAC Converter Setup"
!define MUI_WELcomepage_TEXT "This installer will guide you through installing the VibesFLAC FLAC → ALAC converter tool."

!define MUI_FINISHPAGE_TITLE "Installation Complete 🎉"
!define MUI_FINISHPAGE_TEXT "Thank you for installing VibesFLAC! Select Finish to launch the app."

; ------------------------------------------------------------
; PAGES
; ------------------------------------------------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
Page custom SupportPageCreate SupportPageLeave
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; ------------------------------------------------------------
; INSTALL FILES
; ------------------------------------------------------------
Section "Install"
    SetOutPath "$INSTDIR"
    File /r "dist\VibesFLACtoALAC\*.*"
    CreateShortCut "$DESKTOP\VibesFLAC.lnk" "$INSTDIR\${APPEXENAME}"
SectionEnd

; ------------------------------------------------------------
; DARK THEME (Buttons + Backgrounds)
; ------------------------------------------------------------
Function ApplyDarkTheme
    SetCtlColors $mui.Button.Next 0xFFFFFF 0x1E1E1E
    SetCtlColors $mui.Button.Cancel 0xFFFFFF 0x1E1E1E
    SetCtlColors $mui.Button.Back 0xFFFFFF 0x1E1E1E

    ; Main window background
    SetBrandingImage /TRIM "installer\wizard_small.bmp"
FunctionEnd

; ------------------------------------------------------------
; SUPPORT PAGE
; ------------------------------------------------------------
Var SupportPage
Var GitHubLink
Var CoffeeLink

Function SupportPageCreate
    nsDialogs::Create 1018
    Pop $SupportPage

    ${NSD_CreateLabel} 0 0 100% 30u "Support VibesFLAC Development"
    Pop $0
    SetCtlColors $0 0xFFFFFF 0x1E1E1E

    ${NSD_CreateLabel} 0 25u 100% 30u "If you enjoy this tool, please consider supporting the project:"
    Pop $0
    SetCtlColors $0 0xDDDDDD 0x1E1E1E

    ; GitHub Link
    ${NSD_CreateLink} 0 60u 100% 12u "⭐ Star the GitHub Repo"
    Pop $GitHubLink
    SetCtlColors $GitHubLink 0x78AFFF 0x1E1E1E

    ; Buy Me A Coffee Link
    ${NSD_CreateLink} 0 85u 100% 12u "☕ Buy Me a Coffee"
    Pop $CoffeeLink
    SetCtlColors $CoffeeLink 0xFF9933 0x1E1E1E

    nsDialogs::Show
FunctionEnd

Function SupportPageLeave
    ; No action needed
FunctionEnd

; ------------------------------------------------------------
; CLICKABLE LINK HANDLERS
; ------------------------------------------------------------
Function .onGUIInit
    Call ApplyDarkTheme

    nsDialogs::OnClick $GitHubLink GitHubClick
    nsDialogs::OnClick $CoffeeLink CoffeeClick
FunctionEnd

Function GitHubClick
    ExecShell "open" "https://github.com/Keekay-OD/FLAC-TO-ALAC"
FunctionEnd

Function CoffeeClick
    ExecShell "open" "https://buymeacoffee.com/keekay"
FunctionEnd
