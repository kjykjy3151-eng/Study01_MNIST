<#
.SYNOPSIS
    손글씨 숫자 인식 앱의 바로 가기를 만듭니다.

.DESCRIPTION
    바탕 화면과 프로젝트 폴더에 바로 가기(.lnk)를 하나씩 만듭니다.
    만들어진 바로 가기는 다음 세 가지를 갖춥니다.

      1. pythonw.exe 를 직접 가리켜, 실행해도 검은 콘솔 창이 뜨지 않습니다.
      2. 아이콘.ico 가 적용됩니다.
      3. AppUserModelID 가 기록되어 작업 표시줄에 고정할 수 있습니다.
         이 값은 app.py 의 앱_아이디 와 반드시 같아야 하며,
         다르면 고정한 아이콘과 실행 중인 창이 따로 표시됩니다.

    바로 가기 파일에는 만든 PC의 절대 경로와 컴퓨터 이름이 들어가기 때문에
    저장소에는 포함하지 않습니다. 내려받은 뒤 이 스크립트를 한 번 실행하세요.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File 바로가기_만들기.ps1
#>

param(
    # 바탕 화면에는 만들지 않고 프로젝트 폴더에만 만들고 싶을 때 사용합니다.
    [switch]$바탕화면제외
)

$ErrorActionPreference = "Stop"

# 이 스크립트가 있는 폴더를 프로젝트 폴더로 삼습니다.
$프로젝트폴더 = Split-Path -Parent $MyInvocation.MyCommand.Definition
$실행기 = Join-Path $프로젝트폴더 ".venv\Scripts\pythonw.exe"
$아이콘 = Join-Path $프로젝트폴더 "아이콘.ico"
$앱아이디 = "MNIST.HandwrittenDigitRecognizer.1"   # app.py 의 앱_아이디 와 같은 값
$설명 = "마우스로 그린 숫자를 인식하는 앱"

if (-not (Test-Path $실행기)) {
    Write-Error "가상환경을 찾을 수 없습니다: $실행기`n먼저 README 의 설치 절차를 따라 .venv 를 만들어 주세요."
}
if (-not (Test-Path $아이콘)) {
    Write-Warning "아이콘.ico 가 없습니다. python 아이콘_만들기.py 를 먼저 실행하면 아이콘이 적용됩니다."
    $아이콘 = ""
}

# PowerShell 의 형변환 연산자는 COM 객체에 QueryInterface 를 하지 않습니다.
# 그래서 [IShellLinkW]$obj 같은 캐스팅이 실패하므로, 실제 작업은 C# 안에서 합니다.
$소스 = @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class 바로가기제작기
{
    [ComImport, Guid("00021401-0000-0000-C000-000000000046")]
    private class CShellLink { }

    [ComImport, Guid("000214F9-0000-0000-C000-000000000046"),
     InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IShellLinkW
    {
        void GetPath([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder f, int c, IntPtr d, int fl);
        void GetIDList(out IntPtr p);
        void SetIDList(IntPtr p);
        void GetDescription([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder n, int c);
        void SetDescription([MarshalAs(UnmanagedType.LPWStr)] string n);
        void GetWorkingDirectory([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder d, int c);
        void SetWorkingDirectory([MarshalAs(UnmanagedType.LPWStr)] string d);
        void GetArguments([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder a, int c);
        void SetArguments([MarshalAs(UnmanagedType.LPWStr)] string a);
        void GetHotkey(out short h);
        void SetHotkey(short h);
        void GetShowCmd(out int c);
        void SetShowCmd(int c);
        void GetIconLocation([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder i, int c, out int ix);
        void SetIconLocation([MarshalAs(UnmanagedType.LPWStr)] string i, int ix);
        void SetRelativePath([MarshalAs(UnmanagedType.LPWStr)] string r, int res);
        void Resolve(IntPtr hwnd, int fl);
        void SetPath([MarshalAs(UnmanagedType.LPWStr)] string p);
    }

    [ComImport, Guid("0000010b-0000-0000-C000-000000000046"),
     InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IPersistFile
    {
        void GetClassID(out Guid c);
        [PreserveSig] int IsDirty();
        void Load([MarshalAs(UnmanagedType.LPWStr)] string f, int mode);
        void Save([MarshalAs(UnmanagedType.LPWStr)] string f, [MarshalAs(UnmanagedType.Bool)] bool remember);
        void SaveCompleted([MarshalAs(UnmanagedType.LPWStr)] string f);
        void GetCurFile([MarshalAs(UnmanagedType.LPWStr)] out string f);
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct PROPERTYKEY { public Guid fmtid; public uint pid; }

    [StructLayout(LayoutKind.Sequential)]
    private struct PROPVARIANT
    {
        public ushort vt; public ushort r1; public ushort r2; public ushort r3;
        public IntPtr p; public IntPtr p2;
    }

    [ComImport, Guid("886d8eeb-8cf2-4446-8d02-cdba1dbdcf99"),
     InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IPropertyStore
    {
        void GetCount(out uint c);
        void GetAt(uint i, out PROPERTYKEY k);
        void GetValue(ref PROPERTYKEY k, out PROPVARIANT v);
        void SetValue(ref PROPERTYKEY k, ref PROPVARIANT v);
        void Commit();
    }

    [DllImport("ole32.dll")]
    private static extern int PropVariantClear(ref PROPVARIANT pv);

    public static void 만들기(string 저장경로, string 대상, string 인수,
                              string 작업폴더, string 설명, string 아이콘경로, string 앱아이디)
    {
        object 링크 = new CShellLink();
        IShellLinkW 셸링크 = (IShellLinkW)링크;

        셸링크.SetPath(대상);
        if (!string.IsNullOrEmpty(인수))       셸링크.SetArguments(인수);
        if (!string.IsNullOrEmpty(작업폴더))   셸링크.SetWorkingDirectory(작업폴더);
        if (!string.IsNullOrEmpty(설명))       셸링크.SetDescription(설명);
        if (!string.IsNullOrEmpty(아이콘경로)) 셸링크.SetIconLocation(아이콘경로, 0);
        셸링크.SetShowCmd(1); // SW_SHOWNORMAL

        if (!string.IsNullOrEmpty(앱아이디))
        {
            IPropertyStore 저장소 = (IPropertyStore)링크;
            PROPERTYKEY 키 = new PROPERTYKEY();
            키.fmtid = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"); // PKEY_AppUserModel_ID
            키.pid = 5;
            PROPVARIANT 값 = new PROPVARIANT();
            값.vt = 31; // VT_LPWSTR
            값.p = Marshal.StringToCoTaskMemUni(앱아이디);
            저장소.SetValue(ref 키, ref 값);
            저장소.Commit();
            PropVariantClear(ref 값);
        }

        IPersistFile 파일 = (IPersistFile)링크;
        파일.Save(저장경로, true);
        Marshal.ReleaseComObject(링크);
    }
}
"@

if (-not ("바로가기제작기" -as [type])) {
    Add-Type -TypeDefinition $소스 -Language CSharp
}

$만들목록 = @()
if (-not $바탕화면제외) {
    $만들목록 += Join-Path ([Environment]::GetFolderPath("Desktop")) "손글씨 숫자 인식기.lnk"
}
$만들목록 += Join-Path $프로젝트폴더 "손글씨 숫자 인식기.lnk"

foreach ($저장경로 in $만들목록) {
    [바로가기제작기]::만들기($저장경로, $실행기, '"app.py"', $프로젝트폴더, $설명, $아이콘, $앱아이디)
    Write-Host "바로 가기 생성 완료 -> $저장경로"
}

Write-Host ""
Write-Host "작업 표시줄에 고정하려면 바로 가기에서 마우스 오른쪽 버튼을 누른 뒤"
Write-Host "'작업 표시줄에 고정'을 선택하세요."
Write-Host "(Windows 11 에서는 '추가 옵션 표시'를 먼저 눌러야 할 수 있습니다)"
