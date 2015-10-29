import raspi_mon_sys.Scheduler as sched
import time

def say(something, more):
    print(time.time(), something, more)

sched.start()

sched.repeat_every(5, say, "Hello", "World")
sched.repeat_o_clock(60, say, "One", "Minute")

time.sleep(20)

sched.stop()
