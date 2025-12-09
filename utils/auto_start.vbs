Option Explicit

' ===== 설정 부분 =====
Const USERNAME = "user01"   ' 아이디
Const PASSWORD = "user01"   ' 비밀번호

' medical.exe가 설치되어 있을 수 있는 경로 3개
Dim exeCandidates
exeCandidates = Array( _
    "C:\Program Files\medical\medical.exe", _
    "C:\Program Files (x86)\medical\medical.exe", _
    "C:\medical\medical.exe" _
)

' medical.exe 메인 창의 제목(Title, 앞부분만 맞아도 됨)
' 실제 창 제목에 맞게 수정 (예: "MEDICAL System", "의무기록", 등)
Const MEDICAL_WINDOW_TITLE = "量子波動轉寫系統"

' 프로그램 시작 후 로그인 화면 뜰 때까지 기다리는 시간 (ms)
Const STARTUP_WAIT_MS = 8000   ' 8초

' 로그인 후 버튼 활성화까지 기다리는 시간 (ms)
Const AFTER_LOGIN_WAIT_MS = 1000

' 로그인 후 "읽기" 버튼까지 TAB 몇 번인지 (직접 확인해서 수정)
Const READ_BUTTON_TAB_COUNT = 23
Const READ_WIN_BUTTON_TAB_COUNT = 1
Const START_BUTTON_TAB_COUNT = 14

' ======================

Dim shell, fso, gLogPath
Set shell = CreateObject("WScript.Shell")
Set fso   = CreateObject("Scripting.FileSystemObject")

' 로그 파일 위치 (사용자 TEMP 폴더)
' gLogPath = shell.ExpandEnvironmentStrings("%TEMP%") & "\medical_auto_log.txt"
gLogPath = ".\medical_auto_log.txt"
Sub Log(msg)
    On Error Resume Next
    WScript.Echo Now & " - " & msg
    
    Dim f
    Set f = fso.OpenTextFile(gLogPath, 8, True) ' 8 = ForAppending
    f.WriteLine Now & " - " & msg
    f.Close
End Sub

Dim exePath, found, i, ok

Log "===== medical_auto.vbs 시작 ====="

found = False
exePath = ""

' 1) medical.exe 위치 찾기
Log "medical.exe 경로 검색 시작"

For i = 0 To UBound(exeCandidates)
    Log "경로 확인: " & exeCandidates(i)
    If fso.FileExists(exeCandidates(i)) Then
        exePath = exeCandidates(i)
        found = True
        Log "medical.exe 발견: " & exePath
        Exit For
    End If
Next

If Not found Then
    Log "medical.exe를 찾지 못함. 스크립트 종료."
    WScript.Quit
End If

' 2) 프로그램 실행
Log "프로그램 실행 시도: " & exePath
shell.Run """" & exePath & """", 1, False   ' 창 보여주고(1), 기다리지 않음(False)

' 3) 프로그램이 뜰 때까지 대기
Log "프로그램 시작 대기: " & STARTUP_WAIT_MS & " ms"
WScript.Sleep STARTUP_WAIT_MS

' 4) 창 활성화 시도
Log "창 활성화(AppActivate) 시도. 타이틀: " & MEDICAL_WINDOW_TITLE
ok = shell.AppActivate(MEDICAL_WINDOW_TITLE)
If ok Then
    Log "AppActivate 성공(1차 시도)."
Else
    Log "AppActivate 실패(1차). 5초 후 재시도."
    WScript.Sleep 5000
    ok = shell.AppActivate(MEDICAL_WINDOW_TITLE)
    If ok Then
        Log "AppActivate 성공(2차 시도)."
    Else
        Log "AppActivate 최종 실패. SendKeys는 현재 활성창으로 들어감. 스크립트 계속하지만 결과 불확실."
    End If
End If

' 5) 아이디 / 패스워드 입력
Log "아이디/비밀번호 입력 준비."
WScript.Sleep 500   ' 살짝 대기

Log "USERNAME 입력 SendKeys 시작."
shell.SendKeys USERNAME          ' 사용자 이름 입력
Log "USERNAME 입력 완료(키보드 이벤트 전송)."

Log "TAB으로 패스워드 칸 이동 SendKeys."
shell.SendKeys "{TAB}"

WScript.Sleep 200

Log "PASSWORD 입력 SendKeys 시작."
shell.SendKeys PASSWORD
Log "PASSWORD 입력 완료(키보드 이벤트 전송)."

WScript.Sleep 200

Log "ENTER로 로그인 버튼 누르기 SendKeys."
shell.SendKeys "{ENTER}"

' 6) 로그인 후 버튼 활성화 기다리기
Log "로그인 후 대기: " & AFTER_LOGIN_WAIT_MS & " ms"
WScript.Sleep AFTER_LOGIN_WAIT_MS

' 7) "읽기" 버튼으로 TAB 이동 후 Space로 클릭
Dim j
Log """읽기"" 버튼으로 TAB " & READ_BUTTON_TAB_COUNT & "회 이동 시도."

For j = 1 To READ_BUTTON_TAB_COUNT
    shell.SendKeys "{TAB}"
    Log "TAB 전송: " & j & " / " & READ_BUTTON_TAB_COUNT
    WScript.Sleep 100
Next

Log """읽기"" 버튼에 포커스가 있다고 가정하고 Space 키 전송."
shell.SendKeys " "


' 8) "읽기"창에서 맨 첫번째 프로그램을 선택
For j = 1 To READ_WIN_BUTTON_TAB_COUNT
    shell.SendKeys "{TAB}"
    WScript.Sleep 100
Next
' Space 키로 "읽기" 버튼 클릭 효과
shell.SendKeys " "

' 9) "전사" 버튼을 클릭해서 실행
For j = 1 To START_BUTTON_TAB_COUNT
    shell.SendKeys "{TAB}"
    WScript.Sleep 100
Next
' Space 키로 "읽기" 버튼 클릭 효과
shell.SendKeys " "

' ----------------------------------
' Startup 폴더에 넣기 (XP/7/10 공통)
' ----------------------------------
' 1) Win + R → 실행 창에 아래 입력 후 Enter:
' shell:startup
' 
' - XP/7/10 모두에서 현재 사용자용 시작프로그램 폴더가 열립니다.
'   (XP에서 안되면:
'    C:\Documents and Settings\<사용자이름>\시작 메뉴\프로그램\시작프로그램)
' - 위에서 만든 medical_auto.vbs 파일을 이 폴더에 복사합니다.
' 이제 컴퓨터를 켤 때마다 로그인 후 자동으로 스크립트가 실행됩니다.
' 
' 2) 여러 사용자 계정에서 공통으로 실행하고 싶으면
' shell:common startup 를 실행하거나, 아래 경로에 넣으면 됩니다.
' Win7/10:
' C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup
' 