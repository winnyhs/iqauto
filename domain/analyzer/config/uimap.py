# file: config/uimap.py
# -*- coding: utf-8 -*-
"""
UI mapping (Window border coordinates only) for the Medical app.
- Fill positions/sizes/titles/texts in your environment.
- No control introspection; intended for click/typing/OCR by screen coordinates.

Why screen coords? Avoid client/sizing/DPI ambiguity across windows/monitors.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Literal

from common.singleton import SingletonMeta
from common.log import logger

# ------------------------
# Basic types / aliases
# ------------------------
Point = Tuple[int, int]        # (x, y)
Size = Tuple[int, int]         # (width, height)
Rect = Tuple[int, int, int, int]  # (left, top, right, bottom)
                                  # or, (l, t, w, h)
Callback = Callable[..., Any]  # any number of input params, return any type


# ------------------------
# Base component & widgets
# ------------------------
@dataclass
class WindowMap:
    """Base popup window (Screen coords)"""
    title: str
    cclass: str
    lt: Optional[Point] = None
    # rb: Optional[Point] = None
    size: Optional[Size] = None
    ready_timeout: Optional[float] = 3.0   # time for this window to get visible

    callback: Optional[Callback] = None
    # cb_args: Optional[Tuple[Any, ...]] = field(default_factory=tuple) # allow empty tuple as well
    # cb_kwargs: Optional[Dict[str, Any]] = field(default_factory=dict)

    def call(self, win: Any, *args: Any, **kwargs: Any) -> Any:
        if not self.callback: 
            return None
        merged_args = (win, self.cb_args, *args)
        merged_kwargs = {**self.cb_kwargs, **kwargs}
        return self.callback(**merged_args, **merged_kwargs)

@dataclass
class Component:
    """Base visual component (window boarder coords)"""
    c: Optional[Point] = None  # center
    text: Optional[str] = None   # static label if any
    cclass: Optional[str] = None
    callback: Optional[Callback] = None
    # cb_args: Optional[Tuple[Any, ...]] = field(default_factory=tuple) # allow empty tuple as well
    # cb_kwargs: Optional[Dict[str, Any]] = field(default_factory=dict)

    def call(self, win=None, *args: Any, **kwargs: Any) -> Any:
        if not self.callback: 
            return None
        merged_args = (win, *self.cb_args, *args) if win else (*self.cb_args, *args) 
        merged_kwargs = {**self.cb_kwargs, **kwargs}
        return self.callback(**merged_args, **merged_kwargs)

@dataclass
class TextBox(Component):
    pass 
    # role: Literal["textbox"] = "textbox"

@dataclass
class Button(Component):
    popup: Optional[WindowMap] = None

@dataclass
class OptionButton(Component):
    pass 
    # checked: bool = False
    # role: Literal["option"] = "option"

'''-----------------------
Grid
-----------------------'''
@dataclass
class TitleCellSpec: 
    orect: Rect = None  # Original rectangle 
    rect: Rect = None  # New/adjusted rectangle

    def center(self) -> Point:
        return (self.rect[0] + self.rect[2])//2, (self.rect[1] + self.rect[3])//2

@dataclass
class AnalysisGridTitleRow: 
    name = 'grid title row'
    select: TitleCellSpec = field(default_factory=lambda: TitleCellSpec(
        orect=(11,34, 32,51), rect=(11,34,32,51) #size=(21,17)
    ))
    code: TitleCellSpec = field(default_factory=lambda: TitleCellSpec(
         orect=(32,34, 96, 51), rect=(32,34, 58, 51) # size=(61,17)
    ))
    cat: TitleCellSpec = field(default_factory=lambda: TitleCellSpec(
        orect=(58,34, 125,51), rect=(58,34, 91,51)
    ))
    subcat: TitleCellSpec = field(default_factory=lambda: TitleCellSpec(
        orect=(91,34, 158,51), rect=(91,34, 121,51)
    ))
    part: TitleCellSpec = field(default_factory=lambda: TitleCellSpec(
        orect=(121,34, 188,51), rect=(121,34, 147,51)
    ))  # shrink
    prescription: TitleCellSpec = field(default_factory=lambda: TitleCellSpec(
        orect=(147,34, 214,51), rect=(147,34, 176,51)
    ))
    picture: TitleCellSpec = field(default_factory=lambda: TitleCellSpec(
        orect=(176,34, 243,51), rect=(176,34, 206,51)
    ))  # shrink
    video: TitleCellSpec = field(default_factory=lambda: TitleCellSpec(
        orect=(206,34, 273,51), rect=(206,34, 236,51)
    ))  # shrink
    description: TitleCellSpec = field(default_factory=lambda: TitleCellSpec(
        orect=(236,34, 436,51), rect=(236,34, 436,51)
    ))

    def as_dict(self) -> Dict[str, TitleCellSpec]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__.keys()}

@dataclass
class CellSpec:
    title_spec: TitleCellSpec
    center: Point
    height: int
    # callback: Optional[Callback] = None
    # cb_args: Optional[Tuple[Any, ...]] = field(default_factory=tuple)

    def cell_center(self, row: int) -> Point: 
        l, t = self.center
        return (l, t + self.height * row)
    
@dataclass
class SelectCellSpec(CellSpec): 
    rect: Rect

    def cell_rect(self, row: int) -> Rect:
        l, t, r, b = self.rect
        return (l, t + self.height * row,   r, b + self.height * row)

@dataclass
class AnalysisGridMap(Component):
    '''
    [Facts]
    - Grid/Table :: lt=(9, 32), size=(460, 280), inner_size=(456, 276), 
            ==> border_thick=(2,2),  inner_lt=(9+2=11, 32+2=34) 
            ==> title row, row=-1 :: lt=(*, 34)
    - code_col[0], row=0,col=1 :: lt=(32, 51), size=(61, 15), ==> rb=(93,66)
    
    [draw] * means a fact
               *9 *11      *32                *93 
      (0,0) +---+-+---------+-----------------+------------> x
            |
            |
        *32 +   +-+---------+-----------------+------------
        *34 +   + +---21----+------*65--------+------------
            |   | |  select |    code         |
            |   | | [-1,0]  17   [-1,1]       |    <---- title row, [-1,*]
            |   | |         |                 |
        *51 +   + +---------+-----------------+-----------
            |   | |  [0,0]  |    [0,1]        |
            |   | |        *15                |    <---- 0th row, [0, *]
            |   | |         |                 |
        *66 +   + +---------+-----------------+-----------
            |   | |  [1,0]  |    [1,1]        |
            |   | |         |                 |
            |        ...
            |   | |         |                 |
        275 +   + +---------+-----------------------------
            |   | |         |                 |
            |   | |  [14,0] |    [14,1]       |   <----- 14th row, [14, *]
            |   | |         |                 |
       *292 |   +-+---------------------------------------
            |   | | scrollbar lt=(11,292)
            |   + +---------------------------------------
            y
            - table border size = 1
              51 + 15 * 15 = 276
              292 - 276 = 16 borders (1 for a border line)
            
            - cell height: 16
              select_cell width: 21
              code_cell width: 61
              ...

            - select[title]=select[-1]=cell[-1,0]:: lt=(11, 32), size=(21,17)
              select[0]              = cell[ 0,0]:: lt=(11, 51), size=(21,16)
              select[r]              = cell[ r,0]:: lt=(11, 51 + 16r)

              code[title]=code[-1]   = code[-1,0]:: lt=(32, 32), size=(65,17)
              code[0]                = code[ 0,0]:: lt=(32, 51), size=(65,16)
              code[r]                = code[ r,0]:: lt=(32, 51 + 16r)
    '''
    lt: Point = None
    size: Size= None
    isize: Size = None
    cell_height: int = 16  # center[1] = 59 + 16r
    row_cnt: int = 16      # 15/16 rows with/witout horizontal scrollbar
    
    image_path: str = None # 

    title_row: AnalysisGridTitleRow = field(default_factory=lambda: AnalysisGridTitleRow())

    def __post_init__(self): 
        self.select_col = SelectCellSpec(
            title_spec = self.title_row.select, center=(18,56), rect=(11,51, 29,65), #(11,51, 32,64), 
            height = self.cell_height
        )
        self.code_col = CellSpec(
            title_spec = self.title_row.code, center=(42,56), height = self.cell_height
        )
        self.cat_col = CellSpec(
            title_spec = self.title_row.cat, center=(74,56), height = self.cell_height
        )
        self.subcat_col = CellSpec(
            title_spec = self.title_row.subcat, center=(105,59), height = self.cell_height
        )
        self.part_col = CellSpec(
                title_spec = self.title_row.part, center=(132,59), height = self.cell_height
        )
        self.prescription_col = CellSpec(
            title_spec = self.title_row.prescription, center=(166,59), height = self.cell_height
        )
        self.description_col = CellSpec(
            title_spec = self.title_row.description, center=(277,59), height = self.cell_height
        )
    
    def as_dict(self) -> Dict[str, TitleCellSpec]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__.keys()}

@dataclass
class PullDown(Component):
    edit: TextBox = None        # center point
    arrow: Component = None     # center point of a pulldown arrow
    selected: Component = None  # center point
    #option = None # : Dict[str, Dict[str, int]]

@dataclass
class Region(Component): 
    rect: Rect = None
    regions: List[Rect] = None
    height: int = None

# ------------------------
# Window maps (Window Boarder coords)
# ------------------------
@dataclass
class AnalysisWindowMap(WindowMap): 
    """Components on the ANALYSIS window (Window Boarder coords)."""
    grid: AnalysisGridMap = field(default_factory=lambda: AnalysisGridMap(
        lt=(9, 32), size=(460, 280), isize=(456, 276), cell_height=16
    ))
    pulldown: PullDown = field(default_factory=lambda: PullDown(
        edit = TextBox(c=(614, 354)), 
        arrow = Component(c=(717, 355)), 
        selected = Component(c=(550, 370)), 
    ))
    option = { # radio button to choose a code type
        "code": Component(c=(560, 380)),
        "cat" : Component(c=(640, 380)),
        "subcat": Component(c=(700, 380))
    }

    exec_button: Component = field(default_factory=lambda: Component(c=(530, 480)))
    quit_button: Component = field(default_factory=lambda: Component(c=(710, 480)))

    progress_region: Region = field(default_factory=lambda: Region(
        rect=(274, 407,  308, 422)))
    match_region: Region = field(default_factory=lambda: Region(
        rect=(419, 406,  447, 420),  # entire region
        regions=[(418,406, 425,420), # hundredth region
                 (424,406, 431,420),  # tenth region
                 (430,406, 437,420)]   # oneth region
        ))

    def as_dict(self) -> Dict[str, Component]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__.keys()}

@dataclass
class ErrDialogPopMap(WindowMap):
    pass
@dataclass
class ReadWindowMap(WindowMap): 
    pass
@dataclass
class WriteWindowMap(WindowMap): 
    pass

@dataclass
class MainWindowMap(WindowMap):
    """Components on the MAIN window (Window border coords)."""
    exe_path: str = r"C:\Program Files (x86)\medical\medical.exe"
    name_prefix: str = "medical.exe"  # of app name
    backend: str = "win32"
    start_timeout: float = 15.0

    # Login
    user_id_textbox: TextBox = field(default_factory=lambda: TextBox(
        c=(82, 129), #lt=(48, 121), size=(73, 19), rb=(48+73, 121+19), # inner_size=(69, 15), 
        text="admin", cclass="ThunderRT6TextBox"
    ))
    password_textbox: TextBox = field(default_factory=lambda: TextBox(
        c=(82, 157), # lt=(48, 148), size=(73, 19), rb=(48+73, 148+19), # inner_size=(69, 15), 
        text="IDEA1234", cclass="ThunderRT6TextBox"
    ))
    login_button: Button = field(default_factory=lambda: Button(
        c=(150, 145), # lt=(130, 118), size=(46, 54), rb=(130+46, 118+54), 
        text="로그인", cclass="ThunderRT6CommandButton",
        popup = ErrDialogPopMap(
            title=r"^medical", cclass="#32770", ready_timeout=3.0
            # text=r".*(확인|OK).*", 
        )
    ))

    # Actions entry
    analysis_button: Button = field(default_factory=lambda: Button(
        c=(150, 55), # lt=(131, 31), size=(47, 58), rb=(131+47, 31+58), 
        text="분석", cclass="ThunderRT6CommandButton", 
        popup = AnalysisWindowMap(
            title=r"^분석$", cclass="ThunderRT6FormDC", ready_timeout=3.0
        )
    ))
    start_button: Button = field(default_factory=lambda: Button(
        c=(740, 60), # lt=(719, 31), size=(52, 58), rb=(719+52, 31+58), 
        text="전사", cclass="ThunderRT6CommandButton"
    ))
    pause_button: Button = field(default_factory=lambda: Button(
        c=(800, 60), # lt=(773, 31), size=(49, 58), rb=(773+49, 31+58), 
        text="정지", cclass="ThunderRT6CommandButton"
    ))
    exit_button: Button = field(default_factory=lambda: Button(
        c=(990, 60), # lt=(968, 23), size=(49, 58), rb=(968+49, 23+58), 
        text="종료", cclass="ThunderRT6CommandButton"
    ))
    
    # File 
    write_button: Button = field(default_factory=lambda: Button(
        c=(690, 590), # lt=(670, 565), size=(43, 55), rb=(670+43, 565+55), 
        text="저장", cclass="ThunderRT6CommandButton", 
        popup = ReadWindowMap(
            title=r"^처방일기$", cclass="#32770",
            ready_timeout=3.0
        )
    ))
    read_button: Button = field(default_factory=lambda: Button(
        c=(735, 590), # lt=(714, 565), size=(43, 55), rb=(714+43, 565+55), 
        text="읽기", cclass="ThunderRT6CommandButton", 
        popup = ReadWindowMap(
            title=r"^처방일기$", cclass="ThunderRT6FormDC", 
            ready_timeout=3.0
        )
    ))

    # Wave selection
    square_wave_option: OptionButton = field(default_factory=lambda: OptionButton(
        c=(600, 605), # lt=(560, 597), size=(99, 19), rb=(560+99, 597+19), 
        text="square_wave", cclass="ThunderRT6OptionButton"
    ))
    mixed_wave_option: OptionButton = field(default_factory=lambda: OptionButton(
        c=(815, 570), # lt=(774, 559), size=(91, 21), rb=(774+91, 559+21), 
        text="복합파동", cclass="ThunderRT6CheckBox"
    ))

    # Time/volume
    time_length_textbox: TextBox = field(default_factory=lambda: TextBox(
        c=(860, 605), # lt=(840, 597), size=(45, 21), rb=(840+45, 597+21), 
        text="실행시간", cclass="ThunderRT6TextBox"
    ))
    time_length_apply_button: Button = field(default_factory=lambda: Button(
        c=(960, 605), # lt=(916, 593), size=(97, 31), rb=(916+97, 593+31), 
        text="선택행시간조정", cclass="ThunderRT6CommandButton"
    ))
    remaining_time_textbox: TextBox = field(default_factory=lambda: TextBox(
        c=(660, 645), # lt=(630, 636), size=(67, 20), rb=(630+67, 636+20), 
        text="남은시간", cclass="ThunderRT6TextBox"
    ))
    volume_control_bar: Button = field(default_factory=lambda: Button(
        c=(940, 645), # lt=(880, 633), size=(135, 23), rb=(880+135, 633+23), # inner_size=(0, 0), 
        text="Volume", cclass="Slider20WndClass"
    ))

    def call(self, comp: Component, *args: Any, **kwargs: Any) -> Any: 
        """
        Policy for callback input params
        - win as the 1st param, always
        - Component에 저장된 기본 인자(cb_args/cb_kwargs)를 먼저 적용
        - 호출 시 추가로 받은 args/kwargs가 뒤에 추가
        Return value:
        - return value of callback function
        """
        if not comp.callback:
            return None
        merged_args = (comp, *comp.cb_args, *args)
        merged_kwargs = {**comp.cb_kwargs, **kwargs}
        return comp.callback(*merged_args, **merged_kwargs)
    
    # Optional lookup for dynamic access
    def as_dict(self) -> Dict[str, Component]:
        return {
            "user_id_textbox": self.user_id_textbox,
            "password_textbox": self.password_textbox,
            "login_button": self.login_button,
            
            "analysis_button": self.analysis_button,
            "start_button": self.start_button,
            "pause_button": self.pause_button,
            "exit_button": self.exit_button,
            
            "write_button": self.write_button,
            "read_button": self.read_button,
            
            "square_wave_option": self.square_wave_option,
            "mixed_wave_option": self.mixed_wave_option,
            "time_length_textbox": self.time_length_textbox,
            "time_length_apply_button": self.time_length_apply_button,
            "remaining_time_textbox": self.remaining_time_textbox,
            "volume_control_button": self.volume_control_button,
            
            "program_tree": self.program_tree,
            "program_list": self.program_list,
            "prescription_list": self.prescription_list,
        }



# ------------------------
# Top-level UI map
# ------------------------
@dataclass
class __UIMap(metaclass=SingletonMeta):
    """Top-level container of all windows (SCREEN coords)."""
    main: MainWindowMap = field(default_factory=lambda: MainWindowMap(
        title=r"^量子波動轉寫系統", cclass="ThunderRT6FormDC", 
        ready_timeout=15.0
    ))

    def as_dict(self) -> Dict[str, WindowMap]:
        return {
            "main" : self.main,
            # "login_dialog" : self.main.login_button.popup,
            "analysis" : self.main.analysis_button.popup, # AnalysisWindowMap
            "read" : self.main.read_button.popup,         # ReadWindowMap
            "write": self.main.write_button.popup         # WriteWindowMap
        }
    
    def __getitem__(self, key): # to access like ["analysis"]
        return self.as_dict()[key]

    # Optional quick access
    def all_components(self) -> Dict[str, Component]:
        d: Dict[str, Component] = {}
        d.update({f"main.{k}": v for k, v in self.main.as_dict().items()})
        d.update({f"analysis.{k}": v for k, v in self.analysis.as_dict().items()})
        # d.update({f"read.{k}": v for k, v in self.read.as_dict().items()})
        # d.update({f"write.{k}": v for k, v in self.write.as_dict().items()})
        return d

UIMap = __UIMap()