import schedule
import time
import psycopg2
import config as cfg

def job():
    con = psycopg2.connect(database=cfg.sql["database"], user=cfg.sql["user"], password=cfg.sql["password"], host=cfg.sql["host"], port=cfg.sql["port"])
    cur = con.cursor()
    while True:
        try:
            cur.execute("select updatematchuptable()")
        except KeyboardInterrupt:
            raise
        except:
            continue
        break
    print("Ran Job")
    con.close()

#schedule.every(5).to(10).minutes.do(job)
schedule.every().hour.do(job)
while True:
    schedule.run_pending()
    time.sleep(1)
