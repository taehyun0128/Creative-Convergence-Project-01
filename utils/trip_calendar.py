import tkinter as tk
from tkcalendar import Calendar
from datetime import date, timedelta

""""
start : 시작일일
end : 종료일일
"""

# 선택한 날짜들
date_selection = []

def highlight_range(start_date, end_date):
    # 모든 기존 태그 제거
    cal.calevent_remove('all')

    # 오늘 날짜 강조
    cal.calevent_create(date.today(), '오늘', 'today')
    cal.tag_config('today', background='red', foreground='white')

    # 날짜 범위 강조
    delta = end_date - start_date
    for i in range(delta.days + 1):
        d = start_date + timedelta(days=i)
        cal.calevent_create(d, '범위', 'range')
    cal.tag_config('range', background='#B9D7EA', foreground='black')

    # 시작일/종료일 강조
    cal.calevent_create(start_date, '시작일', 'start')
    cal.calevent_create(end_date, '종료일', 'end')
    cal.tag_config('start', background='#274472', foreground='white')
    cal.tag_config('end', background='#274472', foreground='white')

def on_date_select(event):
    selected = cal.selection_get()

    if len(date_selection) == 2:
        date_selection.clear()

    date_selection.append(selected)

    if len(date_selection) == 2:
        start, end = sorted(date_selection)
        highlight_range(start, end)

def show_range():
    if len(date_selection) == 2:
        start, end = sorted(date_selection)
        result_label.config(text=f"📅 시작일: {start} / 종료일: {end}")
        print(start, end)
    else:
        result_label.config(text="⚠️ 날짜를 두 개 선택해주세요.")

# GUI 구성
root = tk.Tk()
root.title("여행가자! 날짜선택")

# 캘린더
cal = Calendar(root, selectmode='day', font=('Arial', 12),
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
               date_pattern="yyyy-mm-dd")
cal.pack(pady=20)
cal.bind("<<CalendarSelected>>", on_date_select)

# 오늘 날짜 강조 초기 설정
cal.calevent_create(date.today(), '오늘', 'today')
cal.tag_config('today', background='red', foreground='white')

# 버튼
range_button = tk.Button(root, text="선택한 날짜 범위 출력", command=show_range)
range_button.pack(pady=5)

# 결과 라벨
result_label = tk.Label(root, text="", font=('Arial', 12))
result_label.pack(pady=5)

root.mainloop()
