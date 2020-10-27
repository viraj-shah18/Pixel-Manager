#!usr/bin/python3
import curses,time,os
import getpass,sys,signal
import shutil
from distutils.dir_util import copy_tree
from datetime import datetime
from depend import *
from create import *


os.stat(".")

print(time.ctime((os.stat(".").st_ctime)))
def show_stat(stdscr,file,dira):
    h,w = stdscr.getmaxyx()
    wn = 3*w//10-1
    curses.init_pair(11,curses.COLOR_WHITE,25)
    st = os.stat(file)
    if dira:
        dira = "Folder"
    else:
        dira = "File"
    for i in range(1,h-2):
        stdscr.addstr(i,w-wn," "*wn,curses.color_pair(11))
    stdscr.addstr(1,w-wn+wn//2-1,"Stats",curses.color_pair(11))    
    stdscr.addstr(2,w-wn+1,"Created  : "+str(time.ctime(st.st_ctime)),curses.color_pair(11))
    stdscr.addstr(3,w-wn+1,"Modified : "+str(time.ctime(st.st_atime)),curses.color_pair(11))
    stdscr.addstr(4,w-wn+1,"Accessed : "+str(time.ctime(st.st_mtime)),curses.color_pair(11))
    stdscr.addstr(5,w-wn+1,"Size (KB): "+str(st.st_size) ,curses.color_pair(11))
    stdscr.addstr(5,w-wn+1,"Size (KB): "+str(st.st_size) ,curses.color_pair(11))
    stdscr.addstr(6,w-wn+1,"Type     : "+dira ,curses.color_pair(11))
"""
atime ctime mtime size mode type 
"""