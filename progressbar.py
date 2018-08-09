# -*- coding: utf-8 -*-
import time #only for the example
"""
This class lets you create a text-based progress bar which updates
in place - i.e. it doesn't print to a newline.

early all of the code in the print method of this class (called 
setProgressBar) comes from a stackoverflow post
(https://stackoverflow.com/a/34325723/3746992) from user Greenstick 
(https://stackoverflow.com/users/2206251/greenstick).

I have put it in a class, because it mimics how I use these sorts of things
in other languages (R, Java etc.)
 

@author: James M. Curran
@contact: james.m.curran@gmail.com
"""
class ProgressBar:
    def __init__(self, iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
        """
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
        """ 
        self.iteration = iteration
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill = fill
    
    
    def setProgressBar(self, iteration):
        self.iteration = iteration
        
        percent = ("{0:." + str(self.decimals) + "f}").format(100 * (self.iteration / float(self.total)))
        filledLength = int(self.length * self.iteration // self.total)
        bar = self.fill * filledLength + '-' * (self.length - filledLength)
        print('\r{} |{}| {}%% {}'.format(self.prefix, bar, percent, self.suffix), end = '\r')
        # Print New Line on Complete
        if self.iteration == self.total: 
            print()
            

if __name__ == '__main__':
    ## This will run too quickly to see on most hardware, but you get the idea
    total = 2000
    pb = ProgressBar(0, total, length = 50)
    
    for i in range(0, total):
        pb.setProgressBar(i + 1)
        time.sleep(1)