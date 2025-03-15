:: V1.1

@echo off

setlocal EnableDelayedExpansion

call _start_CMD.cmd NO_CMD

set DEV=1

IF EXIST .\VSCODE_PROFILE (
	set /p profile=<.\VSCODE_PROFILE
	set profilearg= --profile "!profile!"
)

FOR /F "tokens=* USEBACKQ" %%F IN (`where code.cmd`) DO (
	SET vscodepath=%%F\..\..
	goto breakLoop
)
:breakLoop

set VSCODE_DEV=
set ELECTRON_RUN_AS_NODE=1
start "" "%vscodepath%\\Code.exe" "%vscodepath%\resources\app\out\cli.js" . -n %profilearg%