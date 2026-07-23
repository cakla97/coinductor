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
#define AppVersion "0.1.0"
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
