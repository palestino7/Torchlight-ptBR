; ==============================================================================
; Torchlight pt-BR - Inno Setup 6 Script
; Tradução Completa para Português do Brasil - Torchlight (Steam Build 17685)
; Desenvolvido por Palestino7
; ==============================================================================

#define MyAppName "Torchlight Tradução pt-BR"
#define MyAppVersion "1.3.0"
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
VersionInfoVersion=1.3.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Instalador da Tradução de Torchlight para Português do Brasil
VersionInfoProductVersion=1.3.0.0
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
; 1. Deploy translation and UI layouts to game directory {app}
Source: "..\..\translation_ptbr\translations\*"; DestDir: "{app}\translations"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\translation_ptbr\media\*"; DestDir: "{app}\media"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "steam_appid.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "patch_torchlight.exe"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall

; 2. Deploy translation as an engine mod to %APPDATA%\runic games\torchlight\mods\Traducao_ptBR
Source: "..\..\translation_ptbr\translations\*"; DestDir: "{userappdata}\runic games\torchlight\mods\Traducao_ptBR\translations"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\translation_ptbr\media\*"; DestDir: "{userappdata}\runic games\torchlight\mods\Traducao_ptBR\media"; Flags: ignoreversion recursesubdirs createallsubdirs

[Run]
Filename: "{tmp}\patch_torchlight.exe"; Parameters: """{app}\Torchlight.exe"""; Flags: runhidden; StatusMsg: "Aplicando localização nas opções gráficas..."

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
// Safety Backup & Setup Routine
// ==============================================================================

procedure PerformSafetyBackup();
var
  AppDir, BackupDir, TransFile, BackupTrans, AdmFile, AppDataAdm: String;
  CfgFile, BackupCfg: String;
begin
  AppDir := ExpandConstant('{app}');
  BackupDir := AddBackslash(AppDir) + 'backup_ptbr';
  TransFile := AddBackslash(AppDir) + 'translations\translation.dat';
  BackupTrans := AddBackslash(BackupDir) + 'translation.dat';
  CfgFile := AddBackslash(AppDir) + 'resources.cfg';
  BackupCfg := AddBackslash(BackupDir) + 'resources.cfg';

  // 1. Back up existing translation.dat if present
  if FileExists(TransFile) then
  begin
    if not DirExists(BackupDir) then
      CreateDir(BackupDir);
    if not FileExists(BackupTrans) then
      FileCopy(TransFile, BackupTrans, False);
  end;

  // 2. Back up resources.cfg if present
  if FileExists(CfgFile) then
  begin
    if not DirExists(BackupDir) then
      CreateDir(BackupDir);
    if not FileExists(BackupCfg) then
      FileCopy(CfgFile, BackupCfg, False);
  end;

  // 3. Delete any stale or truncated TRANSLATION.DAT.adm cache files
  AdmFile := AddBackslash(AppDir) + 'translations\TRANSLATION.DAT.adm';
  if FileExists(AdmFile) then
    DeleteFile(AdmFile);

  AdmFile := AddBackslash(AppDir) + 'translations\translation.dat.adm';
  if FileExists(AdmFile) then
    DeleteFile(AdmFile);

  AppDataAdm := ExpandConstant('{userappdata}\runic games\torchlight\mods\Traducao_ptBR\translations\TRANSLATION.DAT.adm');
  if FileExists(AppDataAdm) then
    DeleteFile(AppDataAdm);
end;

// ==============================================================================
// Post-Install Engine & Mod Registration
// ==============================================================================

procedure ConfigureEngineAndMods();
var
  AppDir, CfgFile: String;
  Lines: TArrayOfString;
  NewLines: TArrayOfString;
  I: Integer;
  HasMedia, HasTranslations: Boolean;
  ModDir, ModsDatPath, ModsContent: String;
begin
  AppDir := ExpandConstant('{app}');
  CfgFile := AddBackslash(AppDir) + 'resources.cfg';

  // 1. Update resources.cfg to ensure FileSystem=media/ and FileSystem=translations/ are active
  if FileExists(CfgFile) then
  begin
    if LoadStringsFromFile(CfgFile, Lines) then
    begin
      HasMedia := False;
      HasTranslations := False;
      for I := 0 to GetArrayLength(Lines) - 1 do
      begin
        if Pos('media/', Lowercase(Lines[I])) > 0 then
          HasMedia := True;
        if Pos('translations/', Lowercase(Lines[I])) > 0 then
          HasTranslations := True;
      end;

      if (not HasMedia) or (not HasTranslations) then
      begin
        SetArrayLength(NewLines, GetArrayLength(Lines) + 2);
        NewLines[0] := 'FileSystem=media/';
        NewLines[1] := 'FileSystem=translations/';
        for I := 0 to GetArrayLength(Lines) - 1 do
          NewLines[I + 2] := Lines[I];
        SaveStringsToFile(CfgFile, NewLines, False);
      end;
    end;
  end;

  // 2. Configure %APPDATA%\runic games\torchlight\mods\mods.dat
  ModDir := ExpandConstant('{userappdata}\runic games\torchlight\mods\Traducao_ptBR');
  StringChangeEx(ModDir, '\', '/', True);
  ModsDatPath := ExpandConstant('{userappdata}\runic games\torchlight\mods\mods.dat');

  if not DirExists(ExpandConstant('{userappdata}\runic games\torchlight\mods')) then
    CreateDir(ExpandConstant('{userappdata}\runic games\torchlight\mods'));

  ModsContent := '[MODS]' + #13#10 +
                 '<BOOL>CHECKFORNEW:true' + #13#10 +
                 '[MOD]' + #13#10 +
                 '<STRING>DIRECTORY:' + ModDir + '/' + #13#10 +
                 '<INTEGER>PRIORITY:1' + #13#10 +
                 '<BOOL>COMPRESSED:false' + #13#10 +
                 '[/MOD]' + #13#10 +
                 '[/MODS]' + #13#10;

  SetArrayLength(NewLines, 9);
  NewLines[0] := '[MODS]';
  NewLines[1] := '<BOOL>CHECKFORNEW:true';
  NewLines[2] := '[MOD]';
  NewLines[3] := '<STRING>DIRECTORY:' + ModDir + '/';
  NewLines[4] := '<INTEGER>PRIORITY:1';
  NewLines[5] := '<BOOL>COMPRESSED:false';
  NewLines[6] := '[/MOD]';
  NewLines[7] := '[/MODS]';
  NewLines[8] := '';
  SaveStringsToFile(ModsDatPath, NewLines, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    PerformSafetyBackup();
  end
  else if CurStep = ssPostInstall then
  begin
    ConfigureEngineAndMods();
  end;
end;

// ==============================================================================
// Rollback Uninstaller Routine
// ==============================================================================

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDir, BackupDir, TransDir, TransFile, BackupTrans, AdmFile: String;
  CfgFile, BackupCfg, AppIdFile, ModDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    AppDir := ExpandConstant('{app}');
    BackupDir := AddBackslash(AppDir) + 'backup_ptbr';
    TransDir := AddBackslash(AppDir) + 'translations';
    TransFile := AddBackslash(TransDir) + 'translation.dat';
    BackupTrans := AddBackslash(BackupDir) + 'translation.dat';
    CfgFile := AddBackslash(AppDir) + 'resources.cfg';
    BackupCfg := AddBackslash(BackupDir) + 'resources.cfg';
    AppIdFile := AddBackslash(AppDir) + 'steam_appid.txt';

    // 1. Restore or clean translation.dat
    if FileExists(BackupTrans) then
    begin
      FileCopy(BackupTrans, TransFile, False);
      DeleteFile(BackupTrans);
    end
    else
    begin
      if FileExists(TransFile) then
        DeleteFile(TransFile);
    end;

    // 2. Restore resources.cfg
    if FileExists(BackupCfg) then
    begin
      FileCopy(BackupCfg, CfgFile, False);
      DeleteFile(BackupCfg);
    end;

    // 3. Remove steam_appid.txt and any .adm files
    if FileExists(AppIdFile) then
      DeleteFile(AppIdFile);

    // 4. Restore original Torchlight.exe if patched backup exists
    if FileExists(AddBackslash(AppDir) + 'Torchlight.exe.orig') then
    begin
      FileCopy(AddBackslash(AppDir) + 'Torchlight.exe.orig', AddBackslash(AppDir) + 'Torchlight.exe', False);
      DeleteFile(AddBackslash(AppDir) + 'Torchlight.exe.orig');
    end;

    AdmFile := AddBackslash(TransDir) + 'TRANSLATION.DAT.adm';
    if FileExists(AdmFile) then
      DeleteFile(AdmFile);

    if DirExists(BackupDir) then
      RemoveDir(BackupDir);

    // 5. Remove mod directory from %APPDATA%
    ModDir := ExpandConstant('{userappdata}\runic games\torchlight\mods\Traducao_ptBR');
    if DirExists(ModDir) then
      DelTree(ModDir, True, True, True);
  end;
end;
