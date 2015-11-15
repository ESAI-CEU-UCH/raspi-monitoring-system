import raspi_mon_sys.Scheduler as sched
import time

def say(something, more):
    print(time.time(), something, more)

sched.start()

sched.once_after(100, say, "it's", "me")
sched.once_when(int(time.time()*1000 + 200), say, "it's", "me")
a = sched.repeat_every(5000, say, "Hello", "World")
b = sched.repeat_o_clock(60000, say, "One", "Minute")
b = sched.repeat_o_clock_with_offset(60000, 5, say, "One", "Minute plus five")

time.sleep(31)

sched.remove(a)
print("Removed ", time.time())

c = sched.repeat_o_clock_with_offset(500, 5, say, "something", "funny")
time.sleep(31)
print("Stopping", time.time())

sched.stop()
print("Stopped ", time.time())
