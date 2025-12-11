; ============================================================
; VibesFLAC Installer – Custom Branded, Dark Theme + Support Page
; Developer: Keekay / YKTV Studios
; ============================================================

#define MyAppName "VibesFLAC"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "YKTV Studios"
#define MyAppURL "https://github.com/Keekay-OD/FLAC-TO-ALAC"
#define MyAppSupport "https://buymeacoffee.com/keekay"
#define MyAppExeName "VibesFLACtoALAC.exe"

[Setup]
AppId={{4A14EE15-4A62-4D4C-BC7E-9781CA543A15}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppSupport}
AppUpdatesURL={#MyAppURL}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

OutputDir=installer_output
OutputBaseFilename=VibesFLAC-Setup-v{#MyAppVersion}

WizardStyle=modern
WizardImageFile=installer\wizard_big.bmp
WizardSmallImageFile=installer\wizard_small.bmp
SetupIconFile=icon.ico

Compression=lzma2/ultra
SolidCompression=yes

PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

DisableFinishedPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\VibesFLACtoALAC\VibesFLACtoALAC.exe"; DestDir: "{app}"
Source: "dist\VibesFLACtoALAC\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create Desktop Icon"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch VibesFLAC"; Flags: nowait postinstall skipifsilent


; ============================================================
; SUPPORT PAGE CODE (WORKING + DARK + CLICKABLE LINKS)
; ============================================================

[Code]

var
  SupportPage: TWizardPage;
  GitHubLink, CoffeeLink: TNewStaticText;

procedure OpenURL(URL: String);
var Error: Integer;
begin
  ShellExec('open', URL, '', '', SW_SHOWNORMAL, ewNoWait, Error);
end;

procedure GitHubClick(Sender: TObject);
begin
  OpenURL('https://github.com/Keekay-OD/FLAC-TO-ALAC');
end;

procedure CoffeeClick(Sender: TObject);
begin
  OpenURL('https://buymeacoffee.com/keekay');
end;

procedure InitializeWizard;
begin
  { Allowed dark-theme modifications }
  WizardForm.Color := $1E1E1E;
  WizardForm.NextButton.Font.Color := clWhite;
  WizardForm.BackButton.Font.Color := clWhite;
  WizardForm.CancelButton.Font.Color := clWhite;

  { Create Support Page after installation }
  SupportPage := CreateCustomPage(
    wpFinished,
    'Support VibesFLAC ❤️',
    'Thank you for installing VibesFLAC!'
  );

  SupportPage.Surface.Color := $1E1E1E;

  { Header text }
  with TNewStaticText.Create(SupportPage) do
  begin
    Parent := SupportPage.Surface;
    Caption := '🎉 Installation Complete!';
    Font.Color := clWhite;
    Font.Size := 14;
    Font.Style := [fsBold];
    Left := ScaleX(0);
    Top := ScaleY(10);
  end;

  { GitHub link }
  GitHubLink := TNewStaticText.Create(SupportPage);
  with GitHubLink do
  begin
    Parent := SupportPage.Surface;
    Caption := '⭐ Star the project on GitHub';
    Font.Color := $0078D7;
    Font.Style := [fsUnderline];
    Cursor := crHand;
    Left := ScaleX(0);
    Top := ScaleY(60);
    OnClick := @GitHubClick;
  end;

  { Coffee link }
  CoffeeLink := TNewStaticText.Create(SupportPage);
  with CoffeeLink do
  begin
    Parent := SupportPage.Surface;
    Caption := '☕ Buy Me a Coffee – Support Development';
    Font.Color := $FF8133;
    Font.Style := [fsUnderline];
    Cursor := crHand;
    Left := ScaleX(0);
    Top := ScaleY(100);
    OnClick := @CoffeeClick;
  end;
end;

procedure CurPageChanged(PageID: Integer);
begin
  if PageID = wpFinished then
  begin
    WizardForm.InnerNotebook.ActivePage := SupportPage.Surface;
    WizardForm.NextButton.Caption := 'Finish';
    WizardForm.BackButton.Enabled := False;
  end;
end;
