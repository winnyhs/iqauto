
# Concept
| 객체                      | 설명                          | 주 용도                                                 |
| ----------------------- | --------------------------- | ---------------------------------------------------- |
| **HWND (int)**          | Win32 API 레벨의 “윈도우 핸들”      | `win32gui`, `win32api` 와 같은 native Windows 호출        |
| **WindowSpecification** | “어떤 윈도우를 찾을지”에 대한 조건 (lazy) | `app.window(title="...")` 단계                         |
| **WindowWrapper**       | 실제 윈도우에 대한 조작기 (handle 포함)  | `.click_input()`, `.set_focus()`, `.move_window()` 등 |


# HWND <--> WindowSpecification <--> WindowWrapper
| 변환                                      | 방법                                          | 코드 예시                                                                                                                    |
| --------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **HWND → WindowWrapper**                | `WindowSpecification._create_wrapper(hwnd)` | `wrapper = WindowSpecification({'handle': hwnd}).wrapper_object()` or `pywinauto.controls.hwndwrapper.HwndWrapper(hwnd)` |
| **HWND → WindowSpecification**          | `app.window(handle=hwnd)`                   | `spec = app.window(handle=hwnd)`                                                                                         |
| **WindowSpecification → HWND**          | `.wrapper_object().handle`                  | `hwnd = spec.wrapper_object().handle`                                                                                    |
| **WindowSpecification → WindowWrapper** | `.wrapper_object()`                         | `wrapper = spec.wrapper_object()`                                                                                        |
| **WindowWrapper → HWND**                | `.handle`                                   | `hwnd = wrapper.handle`                                                                                                  |
| **WindowWrapper → WindowSpecification** | `app.window(handle=wrapper.handle)`         | `spec = app.window(handle=wrapper.handle)`                                                                               |
