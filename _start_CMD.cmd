:: V1.2

@echo off

IF EXIST .\PYTHONPATH (
	set /p PYTHONPATH=<.\PYTHONPATH
) ELSE (
	set PYTHONPATH=
)

IF EXIST .\requirements.txt (
	IF NOT EXIST .\NO_VENV (
		IF NOT EXIST .\.venv (
			IF "%~2" NEQ "SKIP_PIP" (
				echo UPGRADING PIP:
				python -m pip install --upgrade pip
			)
			
			call :newlines
			echo CREATING VENV
			python -m venv .\.venv
			
			call :newlines
			echo ENTERING VENV
			call .\.venv\Scripts\activate

			IF "%~2" NEQ "SKIP_PIP" (
				call :newlines
				echo UPGRADING PIP:
				python -m pip install --upgrade pip
			)
		) ELSE (
			echo ENTERING VENV
			call .\.venv\Scripts\activate
			
			IF "%~2" NEQ "SKIP_PIP" (
				call :newlines
				echo UPGRADING PIP:
				python -m pip install --upgrade pip
			)
		)
	)
	
	IF "%~2" NEQ "SKIP_PIP" (
		call :newlines
		echo INSTALLING REQUIREMENTS:
		pip install --upgrade --upgrade-strategy eager -r .\requirements.txt

		IF EXIST .\ADDITIONAL_PIP_COMMANDS.cmd (
			call :newlines
			echo ADDITIONAL PIP COMMANDS:
			call .\ADDITIONAL_PIP_COMMANDS.cmd
		)
	)

	IF EXIST .\ADDITIONAL_CMD_COMMANDS.cmd (
		call :newlines
		echo ADDITIONAL CMD COMMANDS:
		call .\ADDITIONAL_CMD_COMMANDS.cmd
	)
)

set PYTHONDONTWRITEBYTECODE=1

IF "%~1%" NEQ "NO_CMD" (
	cls
	cmd /k
)

goto :eof


:newlines
echo:
echo:
echo:
echo:
echo:
goto :eof



:eof