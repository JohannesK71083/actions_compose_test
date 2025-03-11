@echo off

setlocal EnableDelayedExpansion

call _start_CMD.cmd NO_CMD

set DEV=1

IF EXIST .\VSCODE_PROFILE (
	set /p profile=<.\VSCODE_PROFILE
	code . -n --profile "!profile!"
) ELSE (
	code . -n
)