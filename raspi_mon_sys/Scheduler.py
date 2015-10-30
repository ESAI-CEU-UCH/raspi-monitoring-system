"""The purpose of this module is to implement precise time-delayed execution of
functions.

This module allow to execute functions delayed in time. The functions are able
to receive many positional and/or keyword arguments. A function can be executed
once delayed a given number of seconds, or repeated every N seconds. Similarly,
a function can be called once the next timestamp multiple of a given number of
seconds, or repeated every timestamp multiple of a given number of seconds. For
this purpose, you can use the functions once_after(), repeat_every(),
once_o_clock() and repeat_o_clock().

The normal use of this module requires the execution of start() function before
any function scheduling, and stop() function once the program is ready to its
termination. If the program is intended to run forever, you can use
loop_forever() function which never returns.

Example:

import Scheduler
def say(something, more):
    print(time.time(), something, more)
Scheduler.start()
a = Scheduler.repeat_every(5, say, "Hello", "World")
b = Scheduler.repeat_o_clock(60, say, "One", "Minute")
DO_STUFF()
Scheduler.remove(a)
DO_STUFF()
Scheduler.stop()


Another Example:

import Scheduler
def say(something, more):
    print(time.time(), something, more)
Scheduler.start()
Scheduler.repeat_every(5, say, "Hello", "World")
Scheduler.repeat_o_clock(60, say, "One", "Minute")
Scheduler.loop_forever()

"""
import sys
import time
import threading
from uuid import uuid4

import Queue

#####################
## PRIVATE SECTION ##
#####################

# Set of removed jobs.
__removed = set()
# Queue of pending jobs. Every job is tuple (timestamp, (function, args, kwargs)).
__jobs  = Queue.PriorityQueue()
# Condition to awake main thread when jobs are ready or sleep time has passed.
__awake = threading.Condition()
# List of pending threads, in order to execute join when the terminate.
__running = []
# Thread for main function execution.
__main_thread = None
__main_thread_running = False

def __sleep(amount):
    """Sleeps an amount time and awakes main thread after it."""
    time.sleep(amount)
    __awake.acquire()
    __awake.notify()
    __awake.release()

def __run_threaded(job_func, *args, **kwargs):
    """Executes the given function with args and kwargs in a thread."""
    job_thread = threading.Thread(target=job_func, args=args, kwargs=kwargs)
    try:
        job_thread.start()
    except:
        print "Unexpected error:", sys.exc_info()[0]
    return job_thread

def __check_running_threads():
    """Traverses __running list looking for joinable threads."""
    global __running
    r = []
    for th in __running:
        th.join(0.0)
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
        amount = when - time.time()
        if amount > 0:
            __jobs.put( (when,uuid,data) )
            amount = when - time.time()
            if amount > 0:
                __awake.acquire()
                __running.append( __run_threaded(__sleep, amount) )
                __awake.wait()
                __awake.release()
        else:
            job,args,kwargs = data
            __running.append( __run_threaded(job, *args, **kwargs) )

def __once_after(seconds, uuid, func, *args, **kwargs):
    """Executes the given job function after given seconds amount."""
    if __main_thread_running:
        now  = time.time()
        when = now + seconds
        __jobs.put( (when, uuid, (func,args,kwargs)) )
        __awake.acquire()
        __awake.notify()
        __awake.release()
    else:
        raise Exception("Unable to enqueue any job while Scheduler is stopped.")

def __repeated_job(seconds, expected_when, uuid, func, *args, **kwargs):
    """Repeats execution of a function every seconds.
    
    This function uses expected_when in order to improve precision of next
    repetition.
    """
    func(*args, **kwargs)
    now = time.time()
    diff = now - expected_when
    amount = seconds - diff
    if amount < 0:
        amount = amount % seconds
        expected_when = now + amount
    else:
        expected_when += seconds
    __once_after(amount, uuid, __repeated_job, seconds, expected_when, uuid,
                 func, *args, **kwargs)

def __repeated_o_clock(seconds, uuid, func, *args, **kwargs):
    """Repeats execution of job function at next time multiple of the given seconds."""
    func(*args, **kwargs)
    now  = time.time()
    when = now + (seconds - (now % seconds))
    __once_after(when - now, uuid, __repeated_o_clock, seconds, uuid,
                 func, *args, **kwargs)

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

def once_after(seconds, func, *args, **kwargs):
    """Executes the given job function after given seconds amount and returns a UUID."""
    uuid = uuid4()
    __once_after(seconds, uuid, func, *args, **kwargs)
    return uuid

def repeat_every(seconds, func, *args, **kwargs):
    """Repeats execution of given job function after every seconds and returns a UUID."""
    uuid = uuid4()
    __once_after(seconds, uuid, __repeated_job, seconds, time.time() + seconds, uuid,
                 func, *args, **kwargs)
    return uuid

def once_when(timestamp, func, *args, **kwargs):
    """Executes job function at the given timestamp and returns a UUID."""
    uuid = uuid4()
    seconds = timestamp - time.time()
    if seconds > 0: __once_after(seconds, uuid, func, *args, **kwargs)
    else: raise Exception("Unable to schedule functions in the past")
    return uuid

def once_o_clock(seconds, func, *args, **kwargs):
    """Executes job function at next time multiple of the given seconds and returns a UUID."""
    uuid = uuid4()
    now  = time.time()
    when = now + (seconds - (now % seconds))
    __once_after(when - now, uuid, func, *args, **kwargs)
    return uuid

def repeat_o_clock(seconds, func, *args, **kwargs):
    """Repeated execution of job function at every next time multiple of the given seconds and returns a UUID."""
    uuid = uuid4()
    now  = time.time()
    when = now + (seconds - (now % seconds))
    __once_after(when - now, uuid, __repeated_o_clock, seconds, uuid,
                 func, *args, **kwargs)
    return uuid

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
        __awake.acquire()
        __awake.notify()
        __awake.release()
        __main_thread.join()
        __main_thread = None

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
