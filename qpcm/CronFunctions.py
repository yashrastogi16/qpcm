import MySQLdb
from datetime import date
def check_date_of_expiry():
	db = MySQLdb.connect("127.0.0.1","root","root","qpcm" )
	cursor = db.cursor()
	a = cursor.execute("SELECT * FROM qpcmms_guest")
	for i in cursor.fetchall():
		if i[14]==date.today():
			cursor.execute("UPDATE qpcmms_guest SET status='Inactive' WHERE id=%s",[(i[0])])
			db.commit()
check_date_of_expiry()		