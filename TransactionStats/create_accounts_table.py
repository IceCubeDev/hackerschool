import psycopg2

if __name__ == "__main__":
	db = None
	cursor = None
	try:
		db = psycopg2.connect("dbname='transaction_test' user='postgres' host='localhost' password='123456'")
	except Exception as e:
		print("I am unable to connect to the database: %s" % e.args[1])
	else:
		cursor = db.cursor()
	
	cursor.execute("CREATE TABLE accounts (acctnum INT PRIMARY KEY, balance NUMERIC(8) NOT NULL DEFAULT 0.0);")
	for i in range(1, 1001):
		try:
			cursor.execute("INSERT INTO accounts(acctnum, balance) VALUES(%d, 0.0);" %(i))
		except Exception as e:
			print("Error inserting %d : %s" % (i, e.args[1]))
	
	db.commit()
	cursor.close()
	db.close()
