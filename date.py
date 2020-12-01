import datetime

today = datetime.date.today()
if today.weekday() == 0:
    print(today)
else:
    saturday = today + datetime.timedelta( (5-today.weekday()) % 7 )
    print(saturday)