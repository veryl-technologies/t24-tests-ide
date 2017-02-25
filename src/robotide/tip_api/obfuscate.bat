SET tmpFile=c:\temp\pym.py
for /f "delims=" %%a in ('dir /B "*.py"') do (
    pyminifier "%%a" >> %tmpFile% 
    copy /Y %tmpFile% "%%a" 
    del %tmpFile%
)