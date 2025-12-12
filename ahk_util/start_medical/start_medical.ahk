;@Ahk2Exe-AddResource start_medical_manifest.xml, 24
; ========================================
; AutoHotkey v1
; - 파일 요구사항: 
;   UTF-8 with BOM encoding으로 파일 저장 필요
;   UTF-8 은 오류 가능성 높음
; 
; - AHK compile 시 요구사항: 
;   - 이 파일 맨 위에 반드시 기재해야 함:
;     ;@Ahk2Exe-AddResource manifest.xml, 24
;   - Base File: A32 ANSI 32bit  (AHK runtime 환경; 가장 안전한 선택)
;   - manifest.xml 포함 필요 (항상 관리자 권한으로 실행되기 위함)
; ========================================
;
; Class / ClassNN
; [Main Window]
; user : 		ThunderRT6TextBox / ThunderRT6TextBox5	72, 128
; password: 	ThunderRT6TextBox / ThunderRT6TextBox4	72, 156
; login button:	ThunderRT6CommandButton / ThunderRT6CommandButton19	151, 143
; square-wave:	ThunderRT6OptionButton / ThunderRT6OptionButton1	593, 606
; 복합파동:		ThunderRT6CheckBox / ThunderRT6CheckBox3		806, 569
; 읽기:		ThunderRT6CommandButton / ThunderRT6CommandButton22	732, 594
; 전사:		ThunderRT6CommandButton / ThunderRT6CommandButton12	742, 58
; 
; [Read Window]
; 저장시간:		Edit	/ Edit1
; 읽기:		ThunderRT6CommandButton / ThunderRT6CommandButton3
; 종료:		ThunderRT6CommandButton / ThunderRT6CommandButton1Found window for medical.exe (PID: 22556)
; 
; -----------------------------
;  설정 
; -----------------------------
#NoEnv
SendMode Input
SetTitleMatchMode, 2
DetectHiddenWindows, Off

; 실행 경로 목록 (v1 배열)
exeCandidates := []
exeCandidates.Push("C:\Program Files\medical\medical.exe")
exeCandidates.Push("C:\Program Files (x86)\medical\medical.exe")
exeCandidates.Push("C:\medical\medical.exe")

; -----------------------------
; UI 요소 정의 (Constants)
; -----------------------------
mainWinTitle := "量子波動轉寫系統"
readWinTitle := "일기"

; ----- Main Window -----
userClass := "ThunderRT6TextBox5"
userX := 72
userY := 128
userValue := "user01"

passClass := "ThunderRT6TextBox4"
passX := 72
passY := 156
passValue := "user01"

loginClass := "ThunderRT6CommandButton19"
loginX := 151
loginY := 143

squareWaveClass := "ThunderRT6OptionButton1"
squareWave.X := 593
squareWave.Y := 606

compositeClass := "ThunderRT6CheckBox3"
compositeX := 806
compositeY := 569

ReadPopupClass := "ThunderRT6CommandButton22"
ReadPopuX := 732
ReadPopuY :=594

startClass := "ThunderRT6CommandButton12"
startX := 742
startY := 58

; ----- Read Window -----
readWin_saveTimeClass := "Edit1"
readWin_readBtnClass  := "ThunderRT6CommandButton3"
readWin_closeBtnClass := "ThunderRT6CommandButton1"



; -----------------------------------
; 함수 정의
; -----------------------------------
; 콘솔 로그 기능 (XP~Win10에서 100% 동작)
DllCall("AllocConsole")
log(msg) {
    global
    FileAppend, % msg "`n", CONOUT$
    ; FileAppend, % "[AHK] " msg "`n", CONOUT$
}

; Usage Example: 
; ClickAndEnter(userClass, 72, 128, "ahk_pid " . targetPid)
; ClickAndEnter(ctrl, x, y, winId, winTitle, delay := 200) { ; 200ms 
ClickAndEnter(ctrl, winTitle, winId, delay := 200) { ; 200ms 
    log("ClickAndEnter " ctrl " in winTitle: " winTitle)
    ControlFocus, %ctrl%, %winId%  ;; %winTitle%   ;; Recommanded safe way
    Sleep, %delay%
    SendInput, {Space}
    Sleep, %delay%

    ; ControlSend, %ctrl%, {SPACE}, %winTitle%  ;; VB6에서는 동작안함
    ; Enter 대신 Space + ControlClick도 동작할 수 있다
    ; Click, %x%, %y%  ; 로그인 버튼 위치
    ; ControlClick, x%x% y%y%, %winId%, , Left, 1  ; %winTitle%     ;; Working
    ; Sleep, %delay%
}

ClickAndText(ctrl, value, winId, winTitle, delay := 200) {
    log("ClickAndText " ctrl " to send " value " in winId: " winId " winTitle: " winTitle)
    ControlFocus, %ctrl%, %winId% ;; %winTitle%     ;;     Working, Recommanded safe way
    ; ControlFocus, %ctrl%, %winId%      ;; Not working
    ; ControlClick, %ctrl%, %winTitle%   ;;     working
    ; ControlClick, %ctrl%, %winId%      ;; Not working
    Sleep, %delay%

    SendInput, %value%    ;;    Working
    ; ControlSend, %ctrl%, %value%, %winId%       ;; Not working in VB6
    ; ControlSetText, %ctrl%, %value%, %winTitle% ;;     Working
    ; ControlSetText, %ctrl%, %value%, %winId%    ;; Not working
    Sleep, %delay%
}

LoginByTab(userId, password) {
    SendInput, %userId%
    Sleep, 200

    SendInput, {TAB}
    Sleep, 200
    SendInput, %password%
    Sleep, 200

    SendInput, {TAB}
    Sleep, 200
    SendInput, {ENTER}
    Sleep, 1000
}

Finish() {
    log("")
    log("-----------------------------------------------------------")
    log("수고하셨습니다. ")
    log("모든 기능이 정상적으로 수행되었습니다. ")
    log("오늘도 하나님이 주시는 치유와 평안이 당신에게 머물기를 기도합니다. ")
    log("-----------------------------------------------------------")
    log("")
    log("")
    log("Enter 혹은 ESC 를 누르시면 이 창이 닫힙니다.")
}

log("medical.exe automation start")

; ----- 입력 인자 처리 -----
stopAtRead := 0
if (A_Args.Length() > 0) {
    arg := A_Args[1]
    if (arg = "1" or arg = "true")
        stopAtRead := 1
}

; ----- medical.exe 실행 파일 찾기 -----
foundExe := ""
for index, path in exeCandidates {
    if FileExist(path) {
        foundExe := path
        break
    }
}
if (foundExe = "") {
    log("medical.exe is not found")
    ; log("Press ENTER to continue.")
    ; KeyWait, Enter      ; Enter key 입력까지 기다려서, 
    ExitApp             ; 종료한다
}

log("medical.exe is found: " foundExe)

; ----- medical.exe 실행 하기 -----
Run, %foundExe%, , UseErrorLevel
Sleep, 8000     ; wait for 8s

; ----- medical.exe process 찾기 -----
ProcessPrefix := "medical.exe"   ; medical로 시작하는 EXE
targetPid := 0
for proc in ComObjGet("winmgmts:").ExecQuery("Select * from Win32_Process") {
    exe := proc.Name

    if (SubStr(exe, 1, StrLen(ProcessPrefix)) = ProcessPrefix) {
        exeName := proc.Name
        targetPid := proc.ProcessId
        break
    }
}
if (!targetPid) {
    log("[ERROR] No medical.exe PID!")
    ; log("Press ENTER to continue.")
    ; KeyWait, Enter      ; Enter key 입력까지 기다려서, 
    ExitApp               ; 종료한다
}

; ----- Window ID -----
winId = "ahk_pid " . targetPid     ;; Must be after getting process
log("Found window for " exe " (PID= " targetPid ", Name= " exeName)


; ----- medical.exe 윈도우 찾기 -----
WinWait,       ahk_pid %targetPid%, , 20
WinActivate,   ahk_pid %targetPid%
WinWaitActive, ahk_pid %targetPid%, , 2
Sleep, 500

; 창 이름 변경은 잘 안 된다. 창변경하지 말자

; ----- login -----
LoginByTab(userValue, passValue)
ClickAndText(userClass, userValue, winId, mainWinTitle)
ClickAndText(passClass, passValue, winId, mainWinTitle)
; 진짜 들어갔는지 읽어오기
; ControlGetText, curUser, %userClass%, %mainWinTitle%
; ControlGetText, curPass, %passClass%, %mainWinTitle%
ClickAndEnter(loginClass, winId, mainWinTitle)   ; 로그인 버튼
log("Logged in")
Sleep, 2000

; ----- square and composit wave
ClickAndEnter(squareWaveClass, winId, mainWinTitle)
ClickAndEnter(compositeClass, winId, mainWinTitle)

; ----- pop up the read window -----
ClickAndEnter(ReadPopupClass, winId, mainWinTitle)

; ----- check whether to stop -----
if (stopAtRead == 1) {
    log("Force to stop after poping up Read Window")
    Finish()
    ExitApp
}
Sleep, 2000  # 2s

; ----- read in the top-most program -----
ClickAndEnter(readWin_saveTimeClass, winId, readWinTitle)
ClickAndEnter(readWin_readBtnClass, winId, readWinTitle)
Sleep, 3000
ClickAndEnter(startClass, winId, mainWinTitle)
Sleep, 1000

; ----- Finish -----
Finish()


; ; 스크립트 종료를 막아서 콘솔 유지
; #Persistent
; 
; Esc::
; Enter::
;     DllCall("FreeConsole")  ; 콘솔 닫기
;     ExitApp
; return

