; file: read_mouse_point_pos_hotkeys.ahk
; AHK v1.x. F7=LeftTop, F8=RightBottom, F10 토글, F9 복사, Esc 종료.

#NoEnv
#SingleInstance, Force
SetBatchLines, -1
ListLines, Off

CoordMode, Mouse, Screen
CoordMode, Pixel, Screen

g_On := true
g_Interval := 30
g_pos := "bottom_center"   ; 초기 위치: 하단 중앙
SetTimer, __SHOW, %g_Interval%
return

; --- 위치 전환 핫키 ---
F7::                     ; 화면 좌상단
    g_pos := "left_top"
return

F8::                     ; 화면 우하단
    g_pos := "right_bottom"
return

; --- 표시 토글 ---
F10::
    g_On := !g_On
    if (g_On) {
        SetTimer, __SHOW, %g_Interval%
    } else {
        SetTimer, __SHOW, Off
        ToolTip
    }
return

; --- 좌표/색상 복사 ---
F9::
    MouseGetPos, sx, sy, hwnd
    PixelGetColor, rgb, %sx%, %sy%, RGB
    r := (rgb & 0xFF0000) >> 16
    g := (rgb & 0x00FF00) >> 8
    b := (rgb & 0x0000FF)
    WinGetTitle, title, ahk_id %hwnd%
    clip := "Screen=(" . sx . "," . sy . ")  RGB=#" . __Hex6(rgb)
    clip := clip . " (" . r . "," . g . "," . b . ")  Title=""" . title . """"
    Clipboard := clip
return

Esc::ExitApp

; --- HUD 갱신 ---
__SHOW:
    MouseGetPos, sx, sy, hwnd, ctrl
    PixelGetColor, rgb, %sx%, %sy%, RGB
    r := (rgb & 0xFF0000) >> 16
    g := (rgb & 0x00FF00) >> 8
    b := (rgb & 0x0000FF)

    CoordMode, Mouse, Window
    MouseGetPos, wx, wy
    CoordMode, Mouse, Screen

    WinGetTitle, title, ahk_id %hwnd%
    WinGetClass, cls, ahk_id %hwnd%

    line1 := "Screen=(" . sx . "," . sy . ")  |  Window=(" . wx . "," . wy . ")"
    line2 := "RGB=#" . __Hex6(rgb) . "  (" . r . "," . g . "," . b . ")"
    line3 := "hwnd=0x" . __Hex8(hwnd) . "   class=" . cls . "   ctrl=" . ctrl

    ; --- 위치 계산: 모드별 좌표 ---
    marginX := 20
    marginY := 20

    if (g_pos = "left_top") {
        cx := marginX
        cy := marginY
    } else if (g_pos = "right_bottom") {
        cx := A_ScreenWidth - 360    ; 가로 폭 대략치 보정
        if (cx < marginX)
            cx := marginX
        cy := A_ScreenHeight - 60    ; 하단 여백
        if (cy < marginY)
            cy := marginY
    } else {
        ; bottom_center (default)
        cx := A_ScreenWidth // 2 - 180
        cy := A_ScreenHeight - 60
    }

    ToolTip, % line1 . "`n" . line2 . "`n" . line3, %cx%, %cy%
return

; --- HEX 포맷 보조 ---
__Hex6(val) {
    SetFormat, IntegerFast, Hex
    v := val + 0
    SetFormat, IntegerFast, D
    v := SubStr(v, 3)
    StringUpper, v, v
    if (StrLen(v) < 6)
        v := SubStr("000000" . v, -5)
    return v
}

__Hex8(val) {
    SetFormat, IntegerFast, Hex
    v := val + 0
    SetFormat, IntegerFast, D
    v := SubStr(v, 3)
    StringUpper, v, v
    if (StrLen(v) < 8)
        v := SubStr("00000000" . v, -7)
    return v
}
