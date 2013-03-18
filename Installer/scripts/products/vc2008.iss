// requires windows installer 3.0
// http://www.microsoft.com/en-us/download/details.aspx?id=29

[CustomMessages]
vc2008x86_title=Microsoft Visual C++ 2008 Service Pack 1 Redistributable Package MFC Security Update (x86)

vc2008x86_size=4.3 MB
vc2008_lcid=''

#ifdef dotnet_Passive
#define vc2008_passive "'/passive '"
#else
#define vc2008_passive "''"
#endif

[Code]
const
    vc2008x86_url = 'http://download.microsoft.com/download/5/D/8/5D8C65CB-C849-4025-8E95-C3966CAFD8AE/vcredist_x86.exe';

procedure vc2008();
var
	version: cardinal;
begin
    // x86 (32 bit) runtime
    if not RegKeyExists(HKLM,'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{9BE518E6-ECC6-35A9-88E4-87755C07200F}') then
    		AddProduct('vcredist_x86.exe',
    			CustomMessage('vc2008_lcid') + '/q ' + {#vc2008_passive} + '/norestart',
    			CustomMessage('vc2008x86_title'),
    			CustomMessage('vc2008x86_size'),
    			vc2008x86_url,false,false);
end;
