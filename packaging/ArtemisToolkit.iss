#define MyAppName "Artemis Toolkit"
#define MyAppVersion "0.6.1"
#define MyAppPublisher "Marius Cuzman"
#define MyAppExeName "ArtemisToolkit.exe"

[Setup]
AppId={{5F8FA0F9-88F3-4F05-950E-6DCC0DDD1279}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppVerName={#MyAppName} {#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=ArtemisToolkitSetup-v{#MyAppVersion}
SetupIconFile=..\icons\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\ArtemisToolkit\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{sys}\schtasks.exe"; Parameters: "/Create /TN ""Artemis Toolkit"" /SC ONLOGON /RU ""{username}"" /TR ""\""{app}\{#MyAppExeName}\"""" /RL LIMITED /F"; Flags: runhidden waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\schtasks.exe"; Parameters: "/Delete /TN ""Artemis Toolkit"" /F"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveArtemisToolkitStartupTask"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  MarkerPath: string;
  MarkerValue: string;
begin
  if CurStep = ssPostInstall then
  begin
    MarkerPath := ExpandConstant('{app}\first_run_reset.marker');
    MarkerValue := GetDateTimeString('yyyy-mm-dd hh:nn:ss', '-', ':');
    SaveStringToFile(MarkerPath, MarkerValue, False);
  end;
end;
