# calendar_widget.py

import tkinter as tk
from tkcalendar import Calendar
from datetime import date, timedelta

class CalendarFrame(tk.Frame):
    """
    tk.Frame 안에 tkcalendar.Calendar를 넣고,
    날짜 두 번 클릭 시 시작일/종료일을 내부에 저장해 두었다가,
    get_selected_range() 메서드로 (start, end) 튜플을 반환해 줍니다.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # 선택된 날짜를 저장할 리스트 (최대 2개)
        self.date_selection = []

        # Calendar 위젯 생성
        self.cal = Calendar(
            self,
            selectmode='day',
            font=('Arial', 12),
            background='white',
            foreground='black',
            bordercolor='gray',
            headersbackground='#6096B4',
            headersforeground='white',
            selectbackground='#27374D',
            selectforeground='white',
            normalbackground='white',
            normalforeground='black',
            weekendbackground='#BDDCD6',
            weekendforeground='black',
            othermonthforeground='gray50',
            othermonthbackground='white',
            othermonthwebackground='#EEE9DA',
            date_pattern="yyyy-mm-dd"
        )
        self.cal.pack(pady=10, expand=True, fill="both")

        # 달력에서 날짜가 선택될 때마다 on_date_select() 호출
        self.cal.bind("<<CalendarSelected>>", self.on_date_select)

        # 오늘 날짜 강조
        self.cal.calevent_create(date.today(), '오늘', 'today')
        self.cal.tag_config('today', background='red', foreground='white')

        # “선택한 날짜 범위 출력” 버튼 (결과를 바로 아래 라벨에 표시)
        #self.range_button = tk.Button(self, text="선택한 날짜 범위 출력", command=self.show_range)
        #self.range_button.pack(pady=5)

        # 선택 결과를 보여 줄 라벨
        #self.result_label = tk.Label(self, text="", font=('Arial', 12))
        #self.result_label.pack(pady=5)

    def on_date_select(self, event):
        """
        달력에서 날짜를 클릭할 때마다 호출됩니다.
        date_selection에 최대 2개의 날짜를 저장해 두었다가,
        두 개가 모이면 highlight_range로 범위를 표시합니다.
        """
        selected = self.cal.selection_get()
        if len(self.date_selection) == 2:
            self.date_selection.clear()
        self.date_selection.append(selected)

        if len(self.date_selection) == 2:
            start, end = sorted(self.date_selection)
            self.highlight_range(start, end)

    def highlight_range(self, start_date, end_date):
        """
        시작일~종료일 범위에 배경색/태그를 설정합니다.
        """
        # 기존 모든 태그 제거
        self.cal.calevent_remove('all')

        # 오늘 날짜 강조
        self.cal.calevent_create(date.today(), '오늘', 'today')
        self.cal.tag_config('today', background='red', foreground='white')

        # 범위 날짜들을 연속적으로 강조
        delta = end_date - start_date
        for i in range(delta.days + 1):
            d = start_date + timedelta(days=i)
            self.cal.calevent_create(d, '범위', 'range')
        self.cal.tag_config('range', background='#B9D7EA', foreground='black')

        # 시작일/종료일 태그
        self.cal.calevent_create(start_date, '시작일', 'start')
        self.cal.calevent_create(end_date, '종료일', 'end')
        self.cal.tag_config('start', background='#274472', foreground='white')
        self.cal.tag_config('end', background='#274472', foreground='white')

    def show_range(self):
        """
        “선택한 날짜 범위 출력” 버튼이 눌렸을 때 호출됩니다.
        두 날짜가 모두 선택되어 있으면 라벨에 출력해 주고, 아니면 경고 메시지 출력.
        """
        if len(self.date_selection) == 2:
            start, end = sorted(self.date_selection)
            self.result_label.config(text=f"📅 시작일: {start} / 종료일: {end}")
        else:
            self.result_label.config(text="⚠️ 날짜를 두 개 선택해주세요.")

    def get_selected_range(self):
        """
        외부(예: GUI 체크 코드)에서 호출할 수 있도록
        (start_date, end_date) 튜플을 리턴해 줍니다.
        """
        if len(self.date_selection) == 2:
            return tuple(sorted(self.date_selection))
        return None, None