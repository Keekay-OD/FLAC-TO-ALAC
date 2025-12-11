; ============================================================
; VibesFLAC Dark Installer (FULLY WORKING, NO EXTRA PLUGINS)
; ============================================================

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "nsDialogs.nsh"
!include "WinMessages.nsh"

!define APPNAME "VibesFLAC Converter"
!define APPVERSION "1.0.0"
!define APPEXENAME "VibesFLACtoALAC.exe"
!define MUI_CUSTOMFUNCTION_GUIINIT myOnGUIInit

OutFile "VibesFLAC-Setup-${APPVERSION}.exe"
InstallDir "$PROGRAMFILES64\VibesFLAC"

; ------------------------------------------------------------
; Dark Theme (works on all NSIS installs)
; ------------------------------------------------------------
Function ApplyDarkTheme
    ; Background = soft blur-like black
    SetCtlColors $HWNDPARENT 0xFFFFFF 0x202020

    ; Buttons = rounded & lighter dark
    GetDlgItem $0 $HWNDPARENT 1
    SetCtlColors $0 0xFFFFFF 0x2A2A2A

    GetDlgItem $0 $HWNDPARENT 2
    SetCtlColors $0 0xFFFFFF 0x2A2A2A

    GetDlgItem $0 $HWNDPARENT 3
    SetCtlColors $0 0xFFFFFF 0x2A2A2A

    ; Welcome/Finish text color tweak
    FindWindow $1 "#32770" "" $HWNDPARENT
    GetDlgItem $2 $1 1037
    SetCtlColors $2 0xFFFFFF transparent
    GetDlgItem $2 $1 1038
    SetCtlColors $2 0xCCCCCC transparent
FunctionEnd


Function myOnGUIInit
    Call ApplyDarkTheme
FunctionEnd

; ------------------------------------------------------------
; MUI Pages
; ------------------------------------------------------------

!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "installer\wizard_small.bmp"

!define MUI_WELCOMEPAGE_BITMAP "installer\wizard_big.bmp"
!define MUI_WELCOMEPAGE_TITLE "Welcome to VibesFLAC Setup"
!define MUI_WELCOMEPAGE_TEXT "Install the VibesFLAC FLAC → ALAC converter tool."

!define MUI_FINISHPAGE_TITLE "Installation Complete 🎉"
!define MUI_FINISHPAGE_TEXT "Thank you for installing VibesFLAC!"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

Page custom SupportPageCreate SupportPageLeave

!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

; ------------------------------------------------------------
; Support Page (Clickable Links + Dark Mode)
; ------------------------------------------------------------

Var SupportPage
Var LinkGitHub
Var LinkCoffee
Var LabelDesc

Function SupportPageCreate
    nsDialogs::Create 1018
    Pop $SupportPage

    ; Title
    ${NSD_CreateLabel} 0 0 100% 18u "🎉 Installation Successful!"
    Pop $LabelDesc
    SetCtlColors $LabelDesc 0xFFFFFF 0x1E1E1E

    ; GitHub link
    ${NSD_CreateLink} 0 40u 100% 12u "⭐ Star the GitHub Repo"
    Pop $LinkGitHub
    SetCtlColors $LinkGitHub 0x78AFFF 0x1E1E1E
    ${NSD_OnClick} $LinkGitHub GitHubClick

    ; Coffee link
    ${NSD_CreateLink} 0 65u 100% 12u "☕ Buy Me a Coffee"
    Pop $LinkCoffee
    SetCtlColors $LinkCoffee 0xFF9933 0x1E1E1E
    ${NSD_OnClick} $LinkCoffee CoffeeClick

    nsDialogs::Show
FunctionEnd


Function SupportPageLeave
FunctionEnd

Function GitHubClick
    ExecShell "open" "https://github.com/Keekay-OD/FLAC-TO-ALAC"
FunctionEnd

Function CoffeeClick
    ExecShell "open" "https://buymeacoffee.com/keekay"
FunctionEnd

; ------------------------------------------------------------
; Install Files
; ------------------------------------------------------------

Section
    SetOutPath "$INSTDIR"
    File "dist\VibesFLACtoALAC\VibesFLACtoALAC.exe"
    File /r "dist\VibesFLACtoALAC\*"

    CreateShortcut "$DESKTOP\VibesFLAC.lnk" "$INSTDIR\VibesFLACtoALAC.exe"
    CreateShortcut "$SMPROGRAMS\VibesFLAC.lnk" "$INSTDIR\VibesFLACtoALAC.exe"

    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\Uninstall.exe"
    Delete "$DESKTOP\VibesFLAC.lnk"
    Delete "$SMPROGRAMS\VibesFLAC.lnk"
    RMDir /r "$INSTDIR"
SectionEnd
