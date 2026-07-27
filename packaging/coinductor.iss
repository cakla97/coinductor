; Inno Setup script for Coinductor.
; Wraps the PyInstaller onedir bundle (dist\Coinductor) into a per-user
; installer with a Start Menu shortcut and an uninstaller.
;
; Build the bundle first:
;   python -m PyInstaller --noconfirm --distpath dist --workpath build packaging\coinductor.spec
; Then compile this script:
;   "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" packaging\coinductor.iss
;
; Unsigned for now: Windows SmartScreen will warn on first run until a
; code-signing certificate is added (out of scope for this step).

#define AppName "Coinductor"
#define AppVersion "0.1.1"
#define AppPublisher "Coinductor"
#define AppExeName "Coinductor.exe"

[Setup]
; A stable AppId keeps upgrades and uninstall correct across versions.
AppId={{6F3B9C24-8A1E-4C7D-9E2F-1A5B7C3D8E90}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
; Per-user install: no admin rights, no UAC prompt.
PrivilegesRequired=lowest
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExeName}
OutputDir=..\dist\installer
OutputBaseFilename=Coinductor-{#AppVersion}-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\coinductor\coinductor.ico
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Recursively bundle the whole PyInstaller onedir output.
Source: "..\dist\Coinductor\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[Code]
// Uninstalling removes the program only. Portfolio state, reports and API keys
// survive on purpose, so reinstalling or upgrading does not wipe a user's
// history - but leaving Binance credentials in the OS vault after someone
// removed the app would be a nasty surprise, so offer to clear them too.
//
// The keys must match secret_store.MANAGED_KEYS; a test holds the two together.
const
  ManagedKeys =
    'BINANCE_API_KEY,BINANCE_API_SECRET,' +
    'BINANCE_TESTNET_API_KEY,BINANCE_TESTNET_API_SECRET,' +
    'BINANCE_LIVE_TRADE_API_KEY,BINANCE_LIVE_TRADE_API_SECRET,' +
    'LLM_API_KEY,LLM_BASE_URL,LLM_MODEL,LLM_VISION_MODEL';

procedure DeleteStoredCredentials();
var
  Keys: TArrayOfString;
  ResultCode, I: Integer;
begin
  Keys := StringSplit(ManagedKeys, [','], stExcludeEmpty);
  for I := 0 to GetArrayLength(Keys) - 1 do
    Exec(ExpandConstant('{cmd}'), '/C cmdkey /delete:' + Keys[I] + '@{#AppName}',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  // keyring also writes one bare service-named entry.
  Exec(ExpandConstant('{cmd}'), '/C cmdkey /delete:{#AppName}',
       '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if CurUninstallStep <> usPostUninstall then
    Exit;
  if UninstallSilent then
    Exit;

  DataDir := ExpandConstant('{localappdata}\{#AppName}');
  if MsgBox(
       'Also delete your Coinductor data and API keys?' + #13#10#13#10 +
       'This removes:' + #13#10 +
       '  - ' + DataDir + #13#10 +
       '    (portfolio state, run history, reports, your profile and config)' + #13#10 +
       '  - your Binance and AI keys from Windows Credential Manager' + #13#10#13#10 +
       'Choose No to keep everything, for example if you plan to reinstall.',
       mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
  begin
    DelTree(DataDir, True, True, True);
    DeleteStoredCredentials();
  end;
end;
