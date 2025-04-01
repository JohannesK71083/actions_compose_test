:: V1.1

@echo off

IF EXIST .\PYTHONPATH (
	set /p PYTHONPATH=<.\PYTHONPATH
) ELSE (
	set PYTHONPATH=
)

IF EXIST .\requirements.txt (
	IF NOT EXIST .\.venv (
		echo UPGRADING PIP:
		python -m pip install --upgrade pip
		
		call :newlines
		echo CREATING VENV
		python -m venv .\.venv
		
		call :newlines
		echo UPGRADING PIP:
		python -m pip install --upgrade pip
		
		call :newlines
		echo ENTERING VENV
		call .\.venv\Scripts\activate
	) ELSE (
		echo ENTERING VENV
		call .\.venv\Scripts\activate
		
		call :newlines
		echo UPGRADING PIP:
		python -m pip install --upgrade pip
	)
	
	call :newlines
	echo INSTALLING REQUIREMENTS:
	pip install --upgrade --upgrade-strategy eager -r .\requirements.txt
)

set PYTHONDONTWRITEBYTECODE=1

IF "%1%" NEQ "NO_CMD" (
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