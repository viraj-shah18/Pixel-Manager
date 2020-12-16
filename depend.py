# import dependencies
import curses,time,os
import getpass,sys,signal
import shutil
from distutils.dir_util import copy_tree
from datetime import datetime

# current directory
os.chdir(".")
menu = os.listdir()
menu.sort()

# Some global Strings
file = "It is a File"
copy = " Selected File: "
search = "Ctrl + S to search: "
options = " c : copy, m : move, k : create file, g : create folder, v : paste"


def copy_cut(stdscr,fold,folder,folder_to_be_copied,h,w,path):
    """
        This function copies a file or a folder to current folder and updates the screen with current directory contents
        stdscr : standard screen
        fold : is it folder or file
        folder : name of folder/file
        folder_to_be_copied : path of folder to be copied
        h,w : screen
        path : path of current directory
    """
    if not fold:
        shutil.copy(folder_to_be_copied, os.getcwd()+"/"+folder)
    else:
        copy_tree(folder_to_be_copied, os.getcwd()+"/"+folder)
    option(stdscr,h,w)
    stdscr.addstr(h-1,0,copy,curses.color_pair(15))
    menu = os.listdir()
    menu.sort()
    listings = []
    for i in menu:
        listings.append(os.path.isdir(i))
    cur_row = menu.index(folder)+1
    print_menu(stdscr,listings,cur_row,folder,menu)
    l = len(menu)
    stdscr.addstr(0,0," "*w,curses.color_pair(5))
    stdscr.addstr(0,w//2-len(path)//2,path,curses.color_pair(5))
    a = 0
    return menu,listings,l,cur_row,a

def empty_right(stdscr, full_screen_mode=False):
    """
        This function creates room in the middle panel
        stdscr : standard screen
    """
    p, w = stdscr.getmaxyx()
    stdscr.attron(curses.color_pair(3))
    for i in range(1, p - 2):
        if full_screen_mode:
            stdscr.addstr(i, 0, " " * w)
            stdscr.refresh()
        else:
            stdscr.addstr(i, w // 5+1, " " * (4 * w // 5 - 37))
            stdscr.refresh()

def print_folder(stdscr,row):
    """
        print the content of the folder on which the cursor is.
    """
    try:
        h = list(os.listdir(row))
        p,w = stdscr.getmaxyx()
        per10screen = w//5
        empty_right(stdscr)
        for i in range(p-3):
            stdscr.attron(curses.color_pair(3))
            if len(h[i])<per10screen:
                l = h[i]+" "*(per10screen-len(row))
            else:
                l = h[i][:per10screen]
            x = w//5+2
            y = i+1
            stdscr.addstr(y,x,l)
    except:
        pass



def print_menu(stdscr,listings,n,this,menu):
    """
        print the main menu/current directory content on left panel
        this : name of file/folder on which cursor is.
        menu : current directory
    """
    h,w = stdscr.getmaxyx()
    per10screen = w//5
    per = " "*(w//5+1)
    for i in range(1,h-2):
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(i,0,per)
    stdscr.attroff(curses.color_pair(2))
    curses.init_pair(4, curses.COLOR_WHITE, 34)
    curses.init_pair(5, 3,17)
    stdscr.attron(curses.color_pair(5))
    stdscr.addstr(0,0," "*w)
    if listings[0]:
        print_folder(stdscr,menu[0])
    else:
        empty_right(stdscr)
        stdscr.addstr(h//2,w//2-len(file)//2,file,curses.color_pair(3))
    stdscr.attron(curses.color_pair(4))
    stdscr.addstr(h-2,0," "*(w-1))
    stdscr.addstr(h-2,w//2-len(menu[0])//2,menu[0])
    for idx, row in enumerate(menu):
        if (idx==0 and n==0) or this==row:
            stdscr.attron(curses.color_pair(1))
            if len(row)<per10screen:
                i = row+" "*(per10screen-len(row))
            else:
                i = row[:per10screen]
            x = 1
            y = idx+1
            stdscr.addstr(y,x,i)
            stdscr.attroff(curses.color_pair(1))
        else:
            if idx>=h-3:
                break
            stdscr.attron(curses.color_pair(2))
            if len(row)<per10screen:
                i = row+" "*(per10screen-len(row))
            else:
                i = row[:per10screen]
            x = 1
            y = idx+1
            stdscr.addstr(y,x,i)
    stdscr.refresh()

def scrolldown(stdscr,cur_row,menu):
    """
        handle scrolling in left panel
    """
    h,w = stdscr.getmaxyx()
    per10screen = w//5
    stdscr.attron(curses.color_pair(2))
    for idx in range(cur_row-h+3,cur_row):
        if len(menu[idx])<per10screen:
            i = menu[idx]+" "*(per10screen-len(menu[idx]))
        else:
            i = menu[idx][:per10screen]
        if idx==cur_row-1:
            stdscr.attron(curses.color_pair(1))
            if len(menu[idx])<per10screen:
                i = menu[idx]+" "*(per10screen-len(menu[idx]))
            else:
                i = menu[idx][:per10screen]
            x = 1
            y = idx+1-cur_row+h-3
            stdscr.addstr(y,x,i)
            stdscr.attroff(curses.color_pair(1))
            stdscr.attron(curses.color_pair(4))
            stdscr.addstr(h-2,0," "*(w-1))
            stdscr.addstr(h-2,w//2-len(menu[cur_row-1])//2,menu[cur_row-1])
        else:
            x = 1
            y = idx+1-cur_row+h-3
            stdscr.addstr(y,x,i)
    stdscr.refresh()


# relative to bottom left, print options
def option(stdscr,h,w):
    if w<100:
        return
    x = w-76-2*w//5
    curses.init_pair(70,curses.COLOR_WHITE,23)
    stdscr.addstr(h-1,0," "*(w-1),curses.color_pair(15))
    stdscr.addstr(h-1,2*w//5," "*(3*w//5),curses.color_pair(15))
    stdscr.addstr(h-1,2*w//5+x," c ",curses.color_pair(70))
    stdscr.addstr(h-1,2*w//5+x+3,"Copy",curses.color_pair(5))
    stdscr.addstr(h-1,2*w//5+x+7," m ",curses.color_pair(70))
    stdscr.addstr(h-1,2*w//5+x+10,"Move",curses.color_pair(5))
    stdscr.addstr(h-1,2*w//5+x+14," k ",curses.color_pair(70))
    stdscr.addstr(h-1,2*w//5+x+17,"File",curses.color_pair(5))
    stdscr.addstr(h-1,2*w//5+x+21," g ",curses.color_pair(70))
    stdscr.addstr(h-1,2*w//5+x+24,"Folder",curses.color_pair(5))
    stdscr.addstr(h-1,2*w//5+x+30," d+r ",curses.color_pair(70))
    stdscr.addstr(h-1,2*w//5+x+35,"Delete",curses.color_pair(5))
    stdscr.addstr(h-1,2*w//5+x+41," ctrl+a ",curses.color_pair(70))
    stdscr.addstr(h-1,2*w//5+x+49,"Search",curses.color_pair(5))
    stdscr.addstr(h-1,2*w//5+x+55," shift+tab ",curses.color_pair(70))
    stdscr.addstr(h-1,2*w//5+x+66,"Terminal",curses.color_pair(5))