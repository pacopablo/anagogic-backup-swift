pushd C:\Development\anagogic-backup
net stop anagogicbackup
"\Program Files\Anagogic\Backup\unins000.exe" /silent
rmdir /s /q build
rmdir /s /q dist
python setup.py py2exe
pushd C:\Development\anagogic-backup\Installer
"\Program Files\Inno Setup 5\iscc.exe" Preprocessed-anagogic-backup-setup.iss
Output\anagogic-backup-setup.exe /silent
popd
python scripts\set_htdocs_reg.py
REM python scripts\set_dropbox_reg.py
REM python scripts\set_sentry_reg.py
net start anagogicbackup
popd
