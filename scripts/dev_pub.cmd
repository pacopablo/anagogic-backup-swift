pushd C:\Development\anagogic-backup-swift
net stop anagogicbackup
"\Program Files\Anagogic\Backup\unins000.exe" /silent
rmdir /s /q build
rmdir /s /q dist
python setup.py py2exe
pushd C:\Development\anagogic-backup-swift\Installer
"\Program Files\Inno Setup 5\iscc.exe" Preprocessed-anagogic-swift-backup-setup.iss
Output\anagogic-swift-backup-setup.exe /silent
popd
python scripts\set_htdocs_reg.py
python scripts\set_swift_reg.py
REM python scripts\set_sentry_reg.py
net start anagogicbackup
popd
