#!/usr/bin/env python2.7
"""The purpose of this module is to implement precise time-delayed execution of
functions.

This module allow to execute functions delayed in time. The functions are able
to receive many positional and/or keyword arguments. A function can be executed
once delayed a given number of mili-seconds, or repeated every N mili-seconds. Similarly,
a function can be called once the next timestamp multiple of a given number of
mili-seconds, or repeated every timestamp multiple of a given number of mili-seconds. For
this purpose, you can use the functions `once_after()`, `repeat_every()`,
`once_o_clock()` and `repeat_o_clock()`.

The normal use of this module requires the execution of `start()` function before
any function scheduling, and `stop()` function once the program is ready to its
termination. If the program is intended to run forever, you can use
`loop_forever()` function which never returns.

**ATTENTION**: this module uses UTC timestamps, so don't expect it to be
correlated with your timezone. Add the required offset to timestamps depending
in your timezone if you really need it.

Example:

>>> import Scheduler
>>> def say(something, more): print(time.time(), something, more)
>>> Scheduler.start()
>>> a = Scheduler.repeat_every(5000, say, "Hello", "World")
>>> b = Scheduler.repeat_o_clock(60000, say, "One", "Minute")
>>> DO_STUFF()
>>> Scheduler.remove(a)
>>> DO_STUFF()
>>> Scheduler.stop()

Another Example:

>>> import Scheduler
>>> def say(something, more): print(time.time(), something, more)
>>> Scheduler.start()
>>> Scheduler.repeat_every(5000, say, "Hello", "World")
>>> Scheduler.repeat_o_clock(60000, say, "One", "Minute")
>>> Scheduler.repeat_o_clock_with_offset(60000, 5000, say, "One", "Minute")
>>> Scheduler.loop_forever()

All functions receive mili-second resolution as integer values.

"""
import sys
import time
import threading
import traceback
from uuid import uuid4

import Queue

#####################
## PRIVATE SECTION ##
#####################

# Set of removed jobs.
__removed = set()
# Queue of pending jobs. Every job is tuple (timestamp, (function, args, kwargs)).
__jobs  = Queue.PriorityQueue()
# Event to awake main thread when jobs are ready or sleep time has passed.
__awake = threading.Event()
# List of pending threads, in order to execute join when the terminate.
__running = []
# Thread for main function execution.
__main_thread = None
__main_thread_running = False

T1_MILISECOND  = 1
T1_CENTISECOND = 10
T1_DECISECOND  = 100
T1_SECOND      = 1000
T1_MINUTE      = 60000
T1_HOUR        = 3600000
T1_DAY         = 24 * T1_HOUR
T1_WEEK        = 7 * T1_DAY

__transformation_dict = {
    "s" : lambda x: x*T1_SECOND,
    "m" : lambda x: x*T1_MINUTE,
    "h" : lambda x: x*T1_HOUR,
    "d" : lambda x: x*T1_DAY,
    "w" : lambda x: x*T1_WEEK,
}

def __transform(ms):
    print ms
    if type(ms) == str or type(ms) == unicode:
        n = float(ms[:-1])
        t = ms[-1].lower()
        return int( round( __transformation_dict[t](n) ) )
    else:
        return ms

def __gettime(): return time.time()*1000

def __run_threaded(job_func, *args, **kwargs):
    """Executes the given function with args and kwargs in a thread."""
    job_thread = threading.Thread(target=job_func, args=args, kwargs=kwargs)
    try:
        job_thread.start()
    except:
        print "Unexpected error:", traceback.format_exc()
    return job_thread

def __check_running_threads(timeout=0.0):
    """Traverses __running list looking for joinable threads."""
    global __running
    r = []
    for th in __running:
        th.join(timeout)
        if th.isAlive(): r.append( th )
    __running = r

def __main_loop():
    """Traverses the priority queue __jobs executing jobs in order.
    
    When a job is ready (its timestamp has passed), it is executed. Otherwise,
    the main thread will wait until the expected timestamp or until __awake
    condition is notified.
    """
    while __main_thread_running:
        __check_running_threads()
        when,uuid,data = __jobs.get()
        if uuid in __removed:
            __removed.discard(uuid)
            continue
        amount = when - __gettime()
        if amount > 0:
            __jobs.put( (when,uuid,data) )
            amount = when - __gettime()
            if amount > 0:
                __awake.wait(amount/1000.0)
                __awake.clear()
        else:
            job,args,kwargs = data
            __running.append( __run_threaded(job, *args, **kwargs) )

def __once_after(mili_seconds, uuid, func, *args, **kwargs):
    """Executes the given job function after given mili-seconds amount."""
    if __main_thread_running:
        now  = __gettime()
        when = now + mili_seconds
        __jobs.put( (when, uuid, (func,args,kwargs)) )
        __awake.set()
    else:
        raise Exception("Unable to enqueue any job while Scheduler is stopped.")

def __repeated_job(mili_seconds, expected_when, uuid, func, *args, **kwargs):
    """Repeats execution of a function every mili-seconds.
    
    This function uses expected_when in order to improve precision of next
    repetition.
    """
    try:
        func(*args, **kwargs)
    except:
        print "Unexpected error:", traceback.format_exc()
    now = __gettime()
    diff = now - expected_when
    amount = mili_seconds - diff
    if amount < 0:
        amount = amount % mili_seconds
        expected_when = now + amount
    else:
        expected_when += mili_seconds
    __once_after(amount, uuid, __repeated_job, mili_seconds, expected_when, uuid,
                 func, *args, **kwargs)

def __repeated_o_clock_with_offset(mili_seconds, offset, uuid, func, *args, **kwargs):
    """Repeats execution of job function at next time multiple of the given mili-seconds plus the given offset."""
    try:
        func(*args, **kwargs)
    except:
        print "Unexpected error:", traceback.format_exc()
    now  = __gettime()
    when = now + (mili_seconds - ((now-offset) % mili_seconds))
    __once_after(when - now, uuid, __repeated_o_clock_with_offset,
                 mili_seconds, offset, uuid, func, *args, **kwargs)

####################
## PUBLIC SECTION ##
####################

def remove(uuid):
    """Allow remove a job scheduled using any repeat_* or once_* functions.
    
    This function is not removing the job from the scheduler, it uses a set of
    removed uuids ignoring the execution of the job once it pops out of the
    priority queue.
    """
    __removed.add(uuid)

def once_after(mili_seconds, func, *args, **kwargs):
    """Executes the given job function after given mili-seconds amount and returns a UUID."""
    mili_seconds = __transform(mili_seconds)
    assert type(mili_seconds) is int, "Needs an integer as mili_seconds parameter"
    uuid = uuid4()
    __once_after(mili_seconds, uuid, func, *args, **kwargs)
    return uuid

def repeat_every(mili_seconds, func, *args, **kwargs):
    """Repeats execution of given job function after every mili-seconds and returns a UUID."""
    mili_seconds = __transform(mili_seconds)
    assert type(mili_seconds) is int, "Needs an integer as mili_seconds parameter"
    uuid = uuid4()
    __once_after(mili_seconds, uuid, __repeated_job, mili_seconds, __gettime() + mili_seconds, uuid,
                 func, *args, **kwargs)
    return uuid

def once_when(ms_timestamp, func, *args, **kwargs):
    """Executes job function at the given timestamp in mili-seconds and returns a UUID."""
    assert type(ms_timestamp) is int, "Needs an integer as ms_timestamp parameter"
    uuid = uuid4()
    mili_seconds = ms_timestamp - __gettime()
    if mili_seconds > 0: __once_after(mili_seconds, uuid, func, *args, **kwargs)
    else: raise Exception("Unable to schedule functions in the past")
    return uuid

def once_o_clock(mili_seconds, func, *args, **kwargs):
    """Executes job function at next time multiple of the given mili-seconds and returns a UUID."""
    mili_seconds = __transform(mili_seconds)
    assert type(mili_seconds) is int, "Needs an integer as mili_seconds parameter"
    uuid = uuid4()
    now  = __gettime()
    when = now + (mili_seconds - (now % mili_seconds))
    __once_after(when - now, uuid, func, *args, **kwargs)
    return uuid

def repeat_o_clock_with_offset(mili_seconds, offset, func, *args, **kwargs):
    """Repeated execution of job function at every next time multiple of the given mili-seconds plus the given offset and returns a UUID."""
    mili_seconds = __transform(mili_seconds)
    offset = __transform(offset)
    if offset >= mili_seconds: raise Exception("Offset should be less than mili_seconds")
    assert type(mili_seconds) is int, "Needs an integer as mili_seconds parameter"
    assert type(offset) is int, "Needs an integer as offset parameter"
    uuid = uuid4()
    now  = __gettime()
    when = now + (mili_seconds - ((now-offset) % mili_seconds))
    __once_after(when - now, uuid, __repeated_o_clock_with_offset,
                 mili_seconds, offset, uuid, func, *args, **kwargs)
    return uuid

def repeat_o_clock(mili_seconds, func, *args, **kwargs):
    """Repeated execution of job function at every next time multiple of the given mili-seconds and returns a UUID."""
    mili_seconds = __transform(mili_seconds)
    return repeat_o_clock_with_offset(mili_seconds, 0, func, *args, **kwargs)

def start():
    """Executes the scheduler."""
    global __main_thread_running
    if not __main_thread_running:
        global __main_thread
        __main_thread_running = True
        __main_thread = __run_threaded( __main_loop )

def stop():
    """Stops execution of the scheduler."""
    global __main_thread_running
    if __main_thread_running:
        global __main_thread
        __main_thread_running = False
        while not __jobs.empty(): __jobs.get()
        __awake.set()
        __check_running_threads(None)
        __main_thread.join()
        __main_thread = None

def is_running():
    return __main_thread_running

def loop_forever():
    """Executes infinite loop, so it never ends and never returns."""
    if not __main_thread_running:
        raise Exception("Unable to loop while Scheduler is stopped.")
    __main_thread.join()

if __name__ == "__main__":
    def say(something, more):
        print(time.time(), something, more)    
    start()
    repeat_every(5, say, "Hello", "World")
    repeat_o_clock(60, say, "One", "Minute")
    loop_forever()
