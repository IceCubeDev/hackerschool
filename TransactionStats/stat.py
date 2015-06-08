import threading
import time
import random
import psycopg2


class StatThread(threading.Thread):
	
	VERBOUSE = False
	
	def __init__(self, tid, isolation_level, num_rows, sleep=0, timeout=None):
		threading.Thread.__init__(self)
		
		self.thread_id = "Thread-" + str(tid)
		
		self.num_rows = num_rows
		self.complete = 0
		self.total = 0
		self.failed = 0
		
		self.running = False
		self.sleep = sleep / 1000
		self.timeout = timeout
		self.elapsed = 0
		
		self.database = None
		self.cursor = None
		self.isolation_level = isolation_level
		
		random.seed()
	
	def init_connection(self):
		try:
			self.database = psycopg2.connect("dbname='transaction_test' user='postgres' host='localhost' password='123456'")
			self.cursor = self.database.cursor()
			self.database.commit()
		except Exception as e:
			print("Error connecting: %s" % str(e))
			return False
			
		return True
	
	def run(self):
		self.running = self.init_connection()
	
		while self.running:
			if self.timeout is not None and self.elapsed >= self.timeout:
				self.running = False
				break
		
			rowid = random.randint(0, self.num_rows)
			
			# time.time() - returns seconds
			start_time = time.time()
			self.execute_transaction(rowid)
			elapsed_time = (time.time() - start_time) * 1000
			
			self.elapsed += elapsed_time
		
		try:
			self.cursor.close()
			self.database.close()
		except Exception as e:
			print("Error closing database connection: %s" % (str(e)))
	
	def execute_transaction(self, rowid):
		try:
			self.database.set_isolation_level(self.isolation_level)
		except Exception as e:
			if StatThread.VERBOUSE: print("Unable to set isolation level: %s" %(str(e)))
			return
			
		try:
			self.cursor.execute("""SELECT * FROM accounts WHERE acctnum = %d;""" % (rowid))
			# Start of transaction
			self.total += 1
			time.sleep(self.sleep)
	
			self.cursor.execute("""UPDATE accounts SET balance = balance + 1 WHERE acctnum = %d;""" % (rowid))
			time.sleep(self.sleep)
	
			self.cursor.execute("""SELECT * FROM accounts WHERE acctnum = %d;""" % (rowid))
			time.sleep(self.sleep)
	
			self.database.commit()
			
			self.complete += 1
		except Exception as e:
			self.database.rollback()
			if StatThread.VERBOUSE: print("FAILED: %s" % str(e))
			self.failed += 1


################################################################################
def run_test(num_threads, isolation_level, sleep, timeout):

	try:
		db = psycopg2.connect("dbname='transaction_test' user='postgres' host='localhost' password='123456'")
		c = db.cursor()
		c.execute("""UPDATE accounts SET balance = 0;""")
		db.commit()
		c.close()
		db.close()
	except Exception as e:
		print("Unable to reset accounts table: %s" % (str(e)))
		exit(-1)

	threads = []
	for i in range(0, num_threads):
		t = StatThread(i, isolation_level, num_threads, sleep, timeout)
		t.start()
		threads.append(t)
	
	# Calculate statistics
	total = 0
	failed = 0
	complete = 0
	
	for thread in threads:
		thread.join()
		total += thread.total
		failed += thread.failed
		complete += thread.complete
	
	try:
		db = psycopg2.connect("dbname='transaction_test' user='postgres' host='localhost' password='123456'")
		c = db.cursor()
		c.execute("""SELECT SUM(balance) FROM accounts""")
		for record in c:
			total_balance = int(record[0])
		c.close()
		db.close()
	except Exception as e:
		total_balance = "error"
	
	#print("|%-7s|%-9s|%-11s|%-10s|%-8s|%-9s|" % \
	print("%-9s%-11s%-12s%-11s%-9s%-11s" % \
		(str(total), str(num_threads), str(sleep), str(complete), str(failed), str(total_balance)))
	#print("+-------+---------+-----------+----------+--------+---------+")
			
if __name__ == "__main__":
	timeout = 60000
	sleep = 0
	num_threads = 2
	
	for i in range(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE, psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE + 1):
		if i is psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE:
			print("LEVEL: SERIALIZABLE")	
		elif i is psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ:
			print("LEVEL: REPEATABLE READ")
		elif i is psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED:
			print("LEVEL: READ_COMMITTED")
		
		print("+-------+---------+-----------+----------+--------+---------+")
		print("| Total | Threads | Sleep(ms) | Complete | Failed | Balance |")
		print("+-------+---------+-----------+----------+--------+---------+")
		
		run_test(num_threads, i, sleep, timeout)
		run_test(num_threads, i, sleep + 50, timeout)
		run_test(num_threads, i, sleep + 500, timeout)
		
		run_test(num_threads * 5, i, sleep, timeout)
		run_test(num_threads * 5, i, sleep + 50, timeout)
		run_test(num_threads * 5, i, sleep + 500, timeout)
		
		run_test(num_threads * 50, i, sleep, timeout)
		run_test(num_threads * 50, i, sleep + 50, timeout)
		run_test(num_threads * 50, i, sleep + 500, timeout)
		
		run_test(num_threads * 500, i, sleep, timeout)
		run_test(num_threads * 500, i, sleep + 50, timeout)
		run_test(num_threads * 500, i, sleep + 500, timeout)
	
