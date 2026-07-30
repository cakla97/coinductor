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
#define AppVersion "0.1.13"
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
; Upgrading over a running Coinductor locks its .exe. Restart Manager offers to
; close it instead of demanding a reboot; it is the Inno 6 default, but stated
; here so a future default cannot silently take it away.
CloseApplications=yes
; The [Run] entry below already offers to launch after installing. Letting
; Restart Manager relaunch as well would open two copies.
RestartApplications=no
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

var
  DataCheckBox, KeysCheckBox: TNewCheckBox;
  RemoveData, RemoveKeys: Boolean;

procedure DeleteStoredCredentials();
var
  Keys: TArrayOfString;
  ResultCode, I: Integer;
  Command: String;
begin
  Keys := StringSplit(ManagedKeys, [','], stExcludeEmpty);
  // One shell invocation rather than eleven: fewer processes, and nothing to
  // flicker on screen even if a shield blocks the hidden-window flag.
  Command := '/C';
  for I := 0 to GetArrayLength(Keys) - 1 do
    Command := Command + ' cmdkey /delete:' + Keys[I] + '@{#AppName} >nul 2>&1 &';
  Command := Command + ' cmdkey /delete:{#AppName} >nul 2>&1';
  Exec(ExpandConstant('{cmd}'), Command, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// Asked once, up front, instead of a chain of Yes/No prompts where "No" read as
// if it might cancel the whole uninstall. Nothing ticked removes the app only.
function AskWhatElseToRemove(): Boolean;
var
  Form: TSetupForm;
  Intro, Footer, DataNote, KeysNote: TNewStaticText;
  OkButton, KeepButton: TNewButton;
begin
  Form := CreateCustomForm(ScaleX(470), ScaleY(300), False, False);
  try
    Form.Caption := 'Uninstall {#AppName}';

    Intro := TNewStaticText.Create(Form);
    Intro.Parent := Form;
    Intro.Left := ScaleX(16);
    Intro.Top := ScaleY(16);
    Intro.Width := Form.ClientWidth - ScaleX(32);
    Intro.WordWrap := True;
    Intro.AutoSize := True;
    Intro.Caption :=
      '{#AppName} will be removed.' + #13#10#13#10 +
      'Tick anything you also want deleted. Leave both unticked to remove the' +
      ' program only and keep everything else, for example if you plan to reinstall.';

    // A TNewCheckBox caption does not wrap, so a long one is simply clipped at
    // the default window width. Keep the caption to a label and put the detail
    // in a wrapped static text underneath.
    DataCheckBox := TNewCheckBox.Create(Form);
    DataCheckBox.Parent := Form;
    DataCheckBox.Left := ScaleX(16);
    DataCheckBox.Top := Intro.Top + Intro.Height + ScaleY(14);
    DataCheckBox.Width := Form.ClientWidth - ScaleX(32);
    DataCheckBox.Height := ScaleY(18);
    DataCheckBox.Checked := False;
    DataCheckBox.Caption := 'Delete local data';

    DataNote := TNewStaticText.Create(Form);
    DataNote.Parent := Form;
    DataNote.Left := ScaleX(34);
    DataNote.Top := DataCheckBox.Top + DataCheckBox.Height + ScaleY(2);
    DataNote.Width := Form.ClientWidth - ScaleX(50);
    DataNote.WordWrap := True;
    DataNote.AutoSize := True;
    DataNote.Caption :=
      'Portfolio state, run history, reports, profile and config, from' + #13#10 +
      ExpandConstant('{localappdata}\{#AppName}');

    KeysCheckBox := TNewCheckBox.Create(Form);
    KeysCheckBox.Parent := Form;
    KeysCheckBox.Left := ScaleX(16);
    KeysCheckBox.Top := DataNote.Top + DataNote.Height + ScaleY(12);
    KeysCheckBox.Width := Form.ClientWidth - ScaleX(32);
    KeysCheckBox.Height := ScaleY(18);
    KeysCheckBox.Checked := False;
    KeysCheckBox.Caption := 'Delete API keys';

    KeysNote := TNewStaticText.Create(Form);
    KeysNote.Parent := Form;
    KeysNote.Left := ScaleX(34);
    KeysNote.Top := KeysCheckBox.Top + KeysCheckBox.Height + ScaleY(2);
    KeysNote.Width := Form.ClientWidth - ScaleX(50);
    KeysNote.WordWrap := True;
    KeysNote.AutoSize := True;
    KeysNote.Caption :=
      'Your Binance and AI keys, from Windows Credential Manager.' + #13#10 +
      'Binance shows a secret only once, so these cannot be recovered here.';

    Footer := TNewStaticText.Create(Form);
    Footer.Parent := Form;
    Footer.Left := ScaleX(16);
    Footer.Top := KeysNote.Top + KeysNote.Height + ScaleY(14);
    Footer.Width := Form.ClientWidth - ScaleX(32);
    Footer.WordWrap := True;
    Footer.AutoSize := True;
    Footer.Caption :=
      'Nothing ticked removes the program only.';

    KeepButton := TNewButton.Create(Form);
    KeepButton.Parent := Form;
    KeepButton.Width := ScaleX(96);
    KeepButton.Height := ScaleY(26);
    KeepButton.Left := Form.ClientWidth - ScaleX(16) - KeepButton.Width;
    KeepButton.Top := Form.ClientHeight - ScaleY(16) - KeepButton.Height;
    KeepButton.Caption := 'Cancel';
    KeepButton.ModalResult := mrCancel;
    KeepButton.Cancel := True;

    OkButton := TNewButton.Create(Form);
    OkButton.Parent := Form;
    OkButton.Width := ScaleX(96);
    OkButton.Height := ScaleY(26);
    OkButton.Left := KeepButton.Left - ScaleX(8) - OkButton.Width;
    OkButton.Top := KeepButton.Top;
    OkButton.Caption := 'Uninstall';
    OkButton.ModalResult := mrOk;
    OkButton.Default := True;

    Form.FlipAndCenterIfNeeded(True, nil, False);
    Result := Form.ShowModal = mrOk;
    if Result then
    begin
      RemoveData := DataCheckBox.Checked;
      RemoveKeys := KeysCheckBox.Checked;
    end;
  finally
    Form.Free;
  end;
end;

function InitializeUninstall(): Boolean;
begin
  RemoveData := False;
  RemoveKeys := False;
  if UninstallSilent then
    Result := True
  else
    Result := AskWhatElseToRemove();
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep <> usPostUninstall then
    Exit;
  if RemoveData then
    DelTree(ExpandConstant('{localappdata}\{#AppName}'), True, True, True);
  if RemoveKeys then
    DeleteStoredCredentials();
end;
