; ==============================================================================
; Torchlight pt-BR - Inno Setup 6 Script
; Tradução Completa para Português do Brasil - Torchlight (Steam Build 17685)
; Desenvolvido por Palestino7
; ==============================================================================

#define MyAppName "Torchlight Tradução pt-BR"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Palestino7"
#define MyAppCopyright "Copyright (C) 2026 Palestino7"
#define MyAppURL "https://github.com/palestino7/Torchlight-ptBR"
#define MyAppExeName "Torchlight_Traducao_ptBR_Setup.exe"

[Setup]
AppId={{9F8D6E42-4A73-4D88-B4C1-3D5A7B8E9012}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright={#MyAppCopyright}
DefaultDirName={code:GetDefaultInstallDir}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=Torchlight_Traducao_ptBR_Setup
OutputDir=..\..\dist
Compression=lzma2/ultra64
SolidCompression=yes
UseSetupLdr=yes
; Explicitly disable UPX to avoid heuristic antivirus false positives (UseUPX=no)
WizardStyle=modern
WizardImageFile=wizard_large.bmp
WizardSmallImageFile=wizard_small.bmp
SetupIconFile=torchlight_ptbr.ico
UninstallDisplayIcon={app}\Torchlight.exe
VersionInfoVersion=1.1.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Instalador da Tradução de Torchlight para Português do Brasil
VersionInfoProductVersion=1.1.0.0
VersionInfoCopyright={#MyAppCopyright}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DirExistsWarning=no
EnableDirDoesntExistWarning=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Messages]
brazilianportuguese.BeveledLabel=Tradução Torchlight pt-BR • Palestino7

[Files]
; Translation files copied to game directory
Source: "..\..\translation_ptbr\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userdesktop}\Torchlight (pt-BR)"; Filename: "{app}\Torchlight.exe"; WorkingDir: "{app}"; Tasks: desktopicon; Check: FileExists(ExpandConstant('{app}\Torchlight.exe'))

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Code]
// ==============================================================================
// Steam App 41500 Auto-Detection & Path Resolution Logic
// ==============================================================================

function IsValidTorchlightDir(const Dir: String): Boolean;
begin
  Result := FileExists(AddBackslash(Dir) + 'Torchlight.exe') or
            FileExists(AddBackslash(Dir) + 'Pak.zip');
end;

function GetSteamAppInstallLocation(): String;
var
  InstallPath: String;
begin
  Result := '';
  
  // 1. Check native 64-bit/32-bit registry for Steam App 41500
  if RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 41500', 'InstallLocation', InstallPath) then
  begin
    if (InstallPath <> '') and DirExists(InstallPath) then
    begin
      Result := InstallPath;
      Exit;
    end;
  end;

  // 2. Check WOW6432Node on 64-bit Windows
  if RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 41500', 'InstallLocation', InstallPath) then
  begin
    if (InstallPath <> '') and DirExists(InstallPath) then
    begin
      Result := InstallPath;
      Exit;
    end;
  end;

  // 3. Check HKCU Steam path fallback
  if RegQueryStringValue(HKCU, 'Software\Valve\Steam', 'SteamPath', InstallPath) then
  begin
    InstallPath := AddBackslash(InstallPath) + 'steamapps\common\Torchlight';
    if DirExists(InstallPath) then
    begin
      Result := InstallPath;
      Exit;
    end;
  end;

  // 4. Standard default Steam paths
  if DirExists('C:\Program Files (x86)\Steam\steamapps\common\Torchlight') then
  begin
    Result := 'C:\Program Files (x86)\Steam\steamapps\common\Torchlight';
    Exit;
  end;

  if DirExists('C:\Program Files\Steam\steamapps\common\Torchlight') then
  begin
    Result := 'C:\Program Files\Steam\steamapps\common\Torchlight';
    Exit;
  end;

  // 5. Secondary drive common paths
  if DirExists('D:\SteamLibrary\steamapps\common\Torchlight') then
  begin
    Result := 'D:\SteamLibrary\steamapps\common\Torchlight';
    Exit;
  end;

  if DirExists('E:\SteamLibrary\steamapps\common\Torchlight') then
  begin
    Result := 'E:\SteamLibrary\steamapps\common\Torchlight';
    Exit;
  end;

  // Fallback default
  Result := 'C:\Program Files (x86)\Steam\steamapps\common\Torchlight';
end;

function GetDefaultInstallDir(Param: String): String;
begin
  Result := GetSteamAppInstallLocation();
end;

// ==============================================================================
// Installation Lifecycle & Directory Validation
// ==============================================================================

function NextButtonClick(CurPageID: Integer): Boolean;
var
  SelectedDir: String;
begin
  Result := True;
  if CurPageID = wpSelectDir then
  begin
    SelectedDir := WizardDirValue();
    if not IsValidTorchlightDir(SelectedDir) then
    begin
      if MsgBox('O executável Torchlight.exe ou Pak.zip não foi encontrado no diretório selecionado:' + #13#10 + #13#10 +
                SelectedDir + #13#10 + #13#10 +
                'Tem certeza de que deseja instalar a tradução neste diretório?',
                mbConfirmation, MB_YESNO) = IDNO then
      begin
        Result := False;
      end;
    end;
  end;
end;

// ==============================================================================
// Safety Backup Routine before Installing
// ==============================================================================

procedure PerformSafetyBackup();
var
  AppDir, BackupDir, TransFile, BackupTrans: String;
begin
  AppDir := ExpandConstant('{app}');
  BackupDir := AddBackslash(AppDir) + 'backup_ptbr';
  TransFile := AddBackslash(AppDir) + 'translations\translation.dat';
  BackupTrans := AddBackslash(BackupDir) + 'translation.dat';

  // If translation.dat already exists, back it up
  if FileExists(TransFile) then
  begin
    if not DirExists(BackupDir) then
      CreateDir(BackupDir);
    if not FileExists(BackupTrans) then
      FileCopy(TransFile, BackupTrans, False);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    PerformSafetyBackup();
  end;
end;

// ==============================================================================
// Rollback Uninstaller Routine
// ==============================================================================

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDir, BackupDir, TransDir, TransFile, BackupTrans: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    AppDir := ExpandConstant('{app}');
    BackupDir := AddBackslash(AppDir) + 'backup_ptbr';
    TransDir := AddBackslash(AppDir) + 'translations';
    TransFile := AddBackslash(TransDir) + 'translation.dat';
    BackupTrans := AddBackslash(BackupDir) + 'translation.dat';

    // 1. If backup exists, restore it cleanly
    if FileExists(BackupTrans) then
    begin
      FileCopy(BackupTrans, TransFile, False);
      DeleteFile(BackupTrans);
      RemoveDir(BackupDir);
    end
    else
    begin
      // 2. No prior translation existed: delete installed translation.dat
      if FileExists(TransFile) then
        DeleteFile(TransFile);
      if DirExists(TransDir) then
        RemoveDir(TransDir);
    end;
  end;
end;
