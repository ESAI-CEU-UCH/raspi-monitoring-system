import raspi_mon_sys.Scheduler as sched
import time

def say(something, more):
    print(time.time(), something, more)

sched.start()

a = sched.repeat_every(5, say, "Hello", "World")
b = sched.repeat_o_clock(60, say, "One", "Minute")
b = sched.repeat_o_clock_with_offset(60, 5, say, "One", "Minute")

time.sleep(31)

sched.remove(a)
print("Removed ", time.time())

time.sleep(31)
print("Stopping", time.time())

sched.stop()
print("Stopped ", time.time())
