from threading import Thread
import time

class Timer(Thread):
    '''
    A timer that runs in a separate thread. Has the ability to call a function at
    every specified interval, as well as call a final function one time once the 
    timer has reached its end.
    
    interval is considered to be in seconds
    when start() is called, the initial state is paused, so resume() must be called
    '''

    def __init__(self, interval, time_limit, func=None, func_args=[], final_func=None, final_args=[]):
        
        super().__init__(target=self._loop)
        self.interval = interval
        self.time_limit = time_limit
        self.func = func
        self.func_args = func_args
        self.final_func = final_func
        self.final_args = final_args
        self.cancel_loop = False
        self.reset_loop = False
        self.pause_timer = True
        self.curent_interval = 0


    def _loop(self):
        '''
        Runs the timer. Executes an optional instruction every interval. Executes
        an optional final instruction when the timer has run out.
        Checks for any state updates every 0.1 seconds.
        If the timer runs out, the loop will pause and wait to be reset or
        wait for the thread to be joined.
        '''
        while True:

            #Wait for an interval to pass
            i = 0
            cont = False
            while i < self.interval * 10:

                if self.cancel_loop: return
                
                #Reset timer
                if self.reset_loop:
                    self.reset_loop = False
                    self.curent_interval = 0
                    cont = True
                    break
                
                #Pause timer
                if self.pause_timer:              
                    while self.pause_timer:
                        if self.cancel_loop: return
                        time.sleep(0.01)
                    cont = True
                    break
                
                time.sleep(0.1)
                i += 1

            if cont: continue

            #Increment time, execute an instruction
            if not self.cancel_loop and self.func: self.func(*self.func_args)
            self.curent_interval += 1

            #Execute final instruction when time is up
            if self.curent_interval >= self.time_limit:
                self.pause_timer = True
                if self.final_func: self.final_func(*self.final_args)


    def cancel(self):
        '''
        Stop the timer loop and join thread. Should be called from the parent thread.
        '''
        self.cancel_loop = True
        self.join()


    def reset(self, new_args=None):
        '''
        Reset the timer's interval to 0. New parameters may be assigned 
        here for the function called every interval.
        timer is paused on reset, must call resume()
        '''
        self.reset_loop = True
        if new_args: self.func_args = new_args
        self.pause_timer = True


    def pause(self):
        self.pause_timer = True

    def resume(self):
        self.pause_timer = False
        
    def get_current_interval(self) -> int:
        return self.curent_interval

    def set_current_interval(self, value):
        self.curent_interval = int(value)
