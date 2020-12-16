import curses
import time, filecmp
import os, re, multiprocessing
import logging as log
from depend import empty_right
from depend import option
from depend import copy
import json

# scroll : when reaching bottom increase
# lines : exact location of typing
# cursor : cursor

class Editor:
    def __init__(self, stdscr, file_name=None):
        
        # if python, then define some regex patterns
        extension = file_name.split(".")[-1]
        f = open("syntax_highlight.json", "r")
        colors = json.load(f)
        f.close()
        all_language_supported = ["py", "cpp"]
        if extension in all_language_supported:
            self.language_support = True
            self.key_col = colors["COLOR_PINK"][extension]
            self.bluish = colors["COLOR_BLUE"][extension]
            self.strings = colors["COLOR_ORANGE"][extension]
            self.comments = colors["COLOR_GREEN"][extension]
            self.single_line_comment = colors["COLOR_GREEN"][extension]["single_line"]
            self.multi_line_comment = colors["COLOR_GREEN"][extension]["multi_line"]
            self.extra = ""
        else:
            self.language_support = False
            self.strings = ""
            self.bluish = ""
            self.single_line_comment = ""
            self.multi_line_comment = ""
            self.key_col = ""
            self.extra = ""

        # Change the layout of the screen to editor.        
        self.h,self.w = stdscr.getmaxyx()
        self.path = file_name
        self.stdscr = stdscr
        self.stdscr.addstr(0,0," "*self.w,curses.color_pair(5) + curses.A_BOLD)
        self.stdscr.addstr(0,self.w//2-len("\U0001F40D"+self.path)//2,self.path,curses.color_pair(5) + curses.A_BOLD)
        curses.init_pair(3,curses.COLOR_WHITE,16)
        curses.init_pair(2, curses.COLOR_WHITE, 24)
        curses.init_pair(40,curses.COLOR_RED,16)
        curses.init_pair(60,curses.COLOR_YELLOW,24)
        curses.init_pair(210,26,16)
        curses.init_pair(211,11,16)
        curses.init_pair(212,14,16)
        curses.init_pair(213,58,16)
        self.global_pattern = ""
        self.clear_screen()
        self.stdscr.refresh()
        self.file = open(file_name,"r")
        self.temp_file = file_name+str(time.time())+".tmp"
        self.start()
        return 

    def clear_screen(self):
        """
            Clear Screen
        """
        # log.info("YES")
        for i in range(1,self.h-1):
            self.stdscr.addstr(i,0," "*(self.w),curses.color_pair(3))
    
    def color_all(self,pattern_type, color_no, curr_row, multi_line=False):
        if multi_line:
            pattern = re.compile(pattern_type, re.MULTILINE)
        else:
            pattern = re.compile(pattern_type)
        matches = [(m.start(0), m.end(0)) for m in re.finditer(pattern,self.lines[self.scroll_row+curr_row-1][self.scroll_col:self.scroll_col+self.w-self.lenth_of_num-3])]
        for j in matches:
            for k in range(j[0],j[1]):
                self.stdscr.addstr(curr_row,self.left_bound+k,self.lines[self.scroll_row+curr_row-1][self.scroll_col+k],curses.color_pair(color_no))

    def color_find(self, curr_row, regex_mode):
        if regex_mode:
            pattern = re.compile(self.global_pattern[3:])
        else:
            pattern = re.compile(re.escape(self.global_pattern))
        matches = [(m.start(0), m.end(0)) for m in re.finditer(pattern,self.lines[self.scroll_row+curr_row-1][self.scroll_col:self.scroll_col+self.w-self.lenth_of_num-3])]
        for j in matches:
            for k in range(j[0],j[1]):
                self.stdscr.addstr(curr_row,self.left_bound+k,self.lines[self.scroll_row+curr_row-1][self.scroll_col+k],curses.color_pair(44))


    def print_screen(self,color,range_=None):
        """
            Print Screen with color of text as color and range_ as None if there is no visual mode ON.
        """
        curses.init_pair(44,curses.COLOR_WHITE,51)
        self.clear_screen()
        for i in range(1,self.h-1):
            if self.scroll_row<max(self.number_of_lines,self.h-2):
                if i>self.number_of_lines and self.number_of_lines<10:
                    break
                self.stdscr.addstr(i,0," "+str(self.scroll_row+i)+"."+" "*(self.lenth_of_num-len(str(self.scroll_row+i))),curses.color_pair(5))
                if range_ and range_[0] <= self.scroll_row+i < range_[1]:
                    self.stdscr.addstr(i,0," "+str(self.scroll_row+i)+"."+" "*(self.lenth_of_num-len(str(self.scroll_row+i))),curses.color_pair(60))
                if i<self.number_of_lines+1:
                    self.stdscr.addstr(i,self.lenth_of_num+3,self.lines[self.scroll_row+i-1][self.scroll_col:self.scroll_col+self.w-self.lenth_of_num-3],curses.color_pair(3))
                    if self.language_support:
                        self.color_all(self.key_col, 40, i)
                        self.color_all(self.bluish, 211, i)
                        self.color_all(self.strings, 210, i)
                        self.color_all(self.single_line_comment, 212, i)
                        self.color_all(self.multi_line_comment, 212, i, True)

                    if self.global_pattern:
                        self.color_find(i, self.global_pattern[:3]=="re/")                    
                    

    @staticmethod
    def tmp_saver(lines,temp_file,num_of_lines):
        """
            save files temporary
        """
        file = open(temp_file,"w")
        for i in range(num_of_lines):
            file.write(lines[i]+"\n")
        file.close()

    def move_cursor(self):
        """
            change cursor position
        """
        self.stdscr.move(self.cursor_row,self.cursor_col)
        self.stdscr.refresh()

    def print_position(self):
        """
            Print position at the bottom right corner.
        """
        self.stdscr.addstr(self.h-1,self.w-self.w//8," "*(self.w//8-1),curses.color_pair(5))
        self.stdscr.addstr(self.h-1,self.w-self.w//8,"{}, {}".format(self.lines_row+1,self.lines_col+1),curses.color_pair(5))

    def replace(self):
        """
            Replace all instances of a pattern
        """
        self.stdscr.addstr(0,0,"REPLACE :",curses.color_pair(60))
        self.stdscr.addstr(0,9," "*(self.w//5-8),curses.color_pair(13))
        replace_on = ""
        while 1:
            self.left_bound = len(str(self.number_of_lines))+3
            self.lenth_of_num = len(str(self.number_of_lines))
            self.print_screen(44)
            self.move_cursor()
            self.stdscr.refresh()
            k = 0
            self.global_patten = ""
            key = self.stdscr.getch()
            if key==curses.KEY_DOWN:
                self.key_down()
            elif key==curses.KEY_UP:
                self.key_up()
            elif key==curses.KEY_LEFT:
                self.key_left()
            elif key==curses.KEY_RIGHT:
                self.key_right()
            elif key==curses.KEY_ENTER or key==10 or key==13:
                for i in range(self.number_of_lines):
                    self.lines[i] = self.lines[i].replace(self.global_pattern,replace_on)
                self.stdscr.addstr(0,0," "*(self.w//5+1),curses.color_pair(5))
                return 

            if key == 8 or key == 127 or key == curses.KEY_BACKSPACE and k>=0:
                    if k<0:
                        continue
                    k-=1
                    replace_on = replace_on[:-1]
                    self.stdscr.move(0,len(replace_on)+10)
                    self.stdscr.addstr("\b \b",curses.color_pair(13))
            elif key!=263 and key!=258 and key!=259 and key!=261:
                k+=1
                replace_on+=chr(key)
                self.stdscr.attron(curses.color_pair(6))
                self.stdscr.move(0,len(replace_on)+8)
                self.stdscr.addch(key,curses.color_pair(13))

    def find(self):
        """
            Find all instances of a pattern
        """
        self.stdscr.addstr(0,4*self.w//5,"FIND :",curses.color_pair(60))
        self.stdscr.addstr(0,4*self.w//5+6," "*(self.w//5-5),curses.color_pair(13))
        while 1:
            self.left_bound = len(str(self.number_of_lines))+3
            self.lenth_of_num = len(str(self.number_of_lines))
            self.print_screen(44)
            self.move_cursor()
            self.stdscr.refresh()
            k = 0
            self.global_patten = ""
            key = self.stdscr.getch()
            if key==curses.KEY_DOWN:
                self.key_down()
            elif key==curses.KEY_UP:
                self.key_up()
            elif key==curses.KEY_LEFT:
                self.key_left()
            elif key==curses.KEY_RIGHT:
                self.key_right()
            elif key==27:
                self.global_pattern = ""
                self.stdscr.addstr(0,4*self.w//5," "*(self.w//5+1),curses.color_pair(5))
                return
            if key==18:
                if self.global_pattern:
                    self.replace()
                    continue
            if key == 8 or key == 127 or key == curses.KEY_BACKSPACE and k>=0:
                    if k<0:
                        continue
                    k-=1
                    self.global_pattern = self.global_pattern[:-1]
                    self.stdscr.move(0,4*self.w//5+len(self.global_pattern)+7)
                    self.stdscr.addstr("\b \b",curses.color_pair(13))
            elif key!=263 and key!=258 and key!=259 and key!=261:
                k+=1
                self.global_pattern+=chr(key)
                self.stdscr.attron(curses.color_pair(6))
                self.stdscr.move(0,4*self.w//5+len(self.global_pattern)+5)
                self.stdscr.addch(key,curses.color_pair(13))
        return

    def middle_(self, list_):
        all_spa = 0
        for item in list_:
            all_spa+=len(item)
        x = (self.w-all_spa-1)//2
        self.stdscr.addstr(self.h-1,0," "*(self.w-1),curses.color_pair(15))
        running_space = 0
        for i, item in enumerate(list_):
            if i%2:
                color_no = 15
            else:
                color_no = 13
            self.stdscr.addstr(self.h-1,x+running_space,item,curses.color_pair(color_no))
            running_space+=len(item)
    
    def options(self,mode):
        """
            different options for editor.
        """
        if mode=="c":
            cmd_list = [" esc ", "Command Mode", " ctrl+f ", "Find", " ctrl+r ", "Replace"]
        elif mode=="nc":
            cmd_list = [" q ", "Exit", " i ", "Insert", " s ", "Visual"]
        elif mode=="v":
            cmd_list = [" x ", "Cut", " c ", "Copy"]
        else:
            cmd_list = []
        self.middle_(cmd_list)
        # TODO: Add specific python like symbol in lowermost line 
        # if self.comments:
        #     self.stdscr.addstr(self.h-1,0," \U0001F40D Python",curses.color_pair(5))

    def cut_copy_paste(self):
        """
        Cut copy paste
        TODO: Clean the code
        """
        curses.init_pair(44,curses.COLOR_WHITE,51)
        store_row = self.lines_row
        store_col = self.lines_col
        self.stdscr.addstr(0,self.w-26," "*(25),curses.color_pair(5))
        self.stdscr.addstr(0,self.w-26,"Select Start Pos : {}, {}".format(store_row+1,store_col+1),curses.color_pair(5))
        self.selector_col = store_col
        self.selector_row = store_row
        self.buffer = []
        no_range = False
        while 1:
            self.left_bound = len(str(self.number_of_lines))+3
            self.lenth_of_num = len(str(self.number_of_lines))
            if not no_range:
                range_ = [store_row+1,self.lines_row+2]
            self.print_screen(44,range_)
            self.stdscr.addstr(self.h-1,self.w-26," "*(25),curses.color_pair(5))
            self.stdscr.addstr(self.h-1,self.w-26,"Select End Pos : {}, {}".format(self.lines_row+1,self.lines_col+1),curses.color_pair(5))
            self.move_cursor()
            self.stdscr.refresh()
            key = self.stdscr.getch()
            # exit, will not keep like this, just for now:
            # diff = self.lines_col-store_col
            if key==curses.KEY_DOWN:
                self.key_down()

            elif key==curses.KEY_UP:
                self.key_up()

            elif key==curses.KEY_LEFT:
                self.key_left()
            
            elif key==curses.KEY_RIGHT:
                self.key_right()
                
            elif key==27:
                self.buffer = []
                self.stdscr.addstr(0,self.w-30," "*(29),curses.color_pair(5))
                self.stdscr.addstr(self.h-1,self.w-26," "*(25),curses.color_pair(5))
                self.print_position()
                return

            elif key==ord("c"):
                no_range = True
                self.buffer = []
                # if self.lines_row<store_row:
                #     store_row,self.lines_row = self.lines_row,store_row
                # if store_col>self.lines_col:
                #     store_col,self.lines_col = self.lines_col,store_col
                    
                if self.lines_row!=store_row:
                    self.buffer.append(self.lines[store_row][store_col:])
                    for buff_lines in range(store_row+1,self.lines_row):
                        self.buffer.append(self.lines[buff_lines])
                    self.buffer.append(self.lines[self.lines_row][:self.lines_col])
                elif self.lines_col!=store_col:
                    self.buffer = [self.lines[store_row][store_col:]]
                # log.info(self.buffer)
                self.stdscr.addstr(0,self.w-30," "*(self.w//5-1),curses.color_pair(5))
                self.print_position()
                self.stdscr.addstr(0,self.w-30,"Press v to paste at a position",curses.color_pair(5))
            elif key==ord("x"):
                no_range = True
                self.buffer = []
                store_lines = self.number_of_lines
                if self.lines_row!=store_row:
                    self.buffer.append(self.lines[store_row][store_col:])
                    for buff_lines in range(store_row+1,self.lines_row):
                        self.buffer.append(self.lines[buff_lines])
                    self.buffer.append(self.lines[self.lines_row][:self.lines_col])
                elif self.lines_col!=store_col:
                    self.buffer = [self.lines[store_row][store_col:]]
                if self.lines_row!=store_row:
                    self.lines[store_row] = self.lines[store_row][:store_col]
                    for buff_lines in range(store_row+1,self.lines_row):
                        self.lines.pop(store_row+1)
                        self.number_of_lines-=1
                        self.lines_row-=1
                    self.lines[self.lines_row] = self.lines[self.lines_row][self.lines_col:]
                    self.cursor_col = min(self.w,self.left_bound + len(self.lines[self.lines_row]))
                elif self.lines_col!=store_col:
                    self.lines[store_row] = self.lines[store_row][:store_col]+self.lines[store_row][self.lines_col:]
                    self.cursor_col = min(self.w,self.left_bound + store_col)
                if self.scroll_row>0:
                    self.scroll_row = max(self.scroll_row-(store_lines-self.number_of_lines),0)
                # log.info(self.buffer)
                self.stdscr.addstr(0,self.w-30," "*(29),curses.color_pair(5))
                self.print_position
                self.stdscr.addstr(0,self.w-30,"Press v to paste at a position",curses.color_pair(5))
                self.lines_row = store_row
                self.lines_col = 0
                self.cursor_row = store_row-self.scroll_row+1
                self.cursor_col = self.left_bound
                if len(self.lines)==0:
                    self.lines = [""]

            elif key==ord("v") and self.buffer:
                if len(self.buffer)>1:
                    left = self.lines[self.lines_row][:self.lines_col]+self.buffer[0]
                    right = self.lines[self.lines_row][self.lines_col:]
                    self.lines[self.lines_row] = left
                    for buff_lines in range(1,len(self.buffer)):
                        self.number_of_lines+=1
                        self.lines = self.lines[:self.lines_row+buff_lines]+[self.buffer[buff_lines]]+self.lines[self.lines_row+buff_lines:]
                    if right:
                        self.lines = self.lines[:self.lines_row+buff_lines+1]+[right]+self.lines[self.lines_row+buff_lines+1:]
                else:
                     self.lines[self.lines_row] = self.lines[self.lines_row][:self.lines_col]+self.buffer[0]+self.lines[self.lines_row][self.lines_col:]


    def key_down(self):
        # Key Down
        if self.cursor_row<min(self.h-2,self.number_of_lines):
            self.cursor_row+=1
        elif self.number_of_lines-self.h+2>self.scroll_row:
            self.scroll_row+=1
        if self.lines_row<self.number_of_lines-1:
            self.lines_row+=1
        if self.cursor_col<len(self.lines[self.lines_row]) and not self.scrolled_right:
            return
        if self.lines_col>self.w or self.scrolled_right:
            self.cursor_col = self.left_bound
            self.lines_col = 0
            self.scroll_col = 0
            self.scrolled_right = False
        elif self.cursor_col>len(self.lines[self.lines_row])+self.left_bound:
            self.cursor_col = len(self.lines[self.lines_row])+self.left_bound
            self.lines_col = len(self.lines[self.lines_row])

    def key_up(self):
        # Key Up
        if self.cursor_row>1:
            self.cursor_row-=1
        elif self.scroll_row>0:
            self.scroll_row-=1
        if self.lines_row>0:
            self.lines_row-=1
        if self.cursor_col<len(self.lines[self.lines_row]) and not self.scrolled_right:
            return
        if self.lines_col>self.w or self.scrolled_right:
            self.cursor_col = self.left_bound
            self.lines_col = 0
            self.scroll_col = 0
            self.scrolled_right = False
        elif self.cursor_col>len(self.lines[self.lines_row])+self.left_bound:
            self.cursor_col = len(self.lines[self.lines_row])+self.left_bound
            self.lines_col = len(self.lines[self.lines_row])

    def key_right(self):
        # Key Right
        if self.cursor_col<self.w-1 and self.cursor_col<self.left_bound+len(self.lines[self.lines_row]):
            self.cursor_col+=1
        elif self.scroll_col<len(self.lines[self.lines_row])-self.w+self.left_bound+1:
            # log.info(str(len(self.lines[self.lines_row])-2)+" "+str(self.scroll_col))
            self.scrolled_right = True
            self.scroll_col+=1
        if self.lines_col<len(self.lines[self.lines_row]):
            self.lines_col+=1
            
    def key_left(self):
        # Key Left
        if self.cursor_col>self.left_bound:
            self.cursor_col-=1
        elif self.scroll_col>0:
            self.scroll_col-=1
        if self.lines_col>0:
            self.lines_col-=1

    def key_enter(self):
        # Key Enter
        if self.lines_row<self.number_of_lines:
            if self.lines_col==len(self.lines[self.lines_row]):
                left = self.lines[self.lines_row][:self.lines_col]    
                right = ""
            else:
                left = self.lines[self.lines_row][:self.lines_col]
                right = self.lines[self.lines_row][self.lines_col:]
            self.lines[self.lines_row] = left
            self.lines = self.lines[:self.lines_row+1]+[right]+self.lines[self.lines_row+1:]
            self.number_of_lines+=1
            if self.cursor_row<self.h-2:
                self.cursor_row+=1
            else:
                self.scroll_row+=1
            if self.lines_row<self.number_of_lines:
                self.lines_row+=1
            self.cursor_col = self.left_bound
            self.lines_col = 0
            self.scroll_col = 0
            if self.comments:
                p = 0
                line = self.lines[self.lines_row-1]
                lengt = len(self.lines[self.lines_row-1])
                while lengt>p+1:
                    if self.lines[self.lines_row-1][p]==" ":
                        p+=1
                    else:
                        break
                if self.lines_row>0 and len(self.lines[self.lines_row-1]) and self.lines[self.lines_row-1][-1]==":":
                    for k in range(p+4):
                        self.key_print(ord(" "))
                else:
                    for k in range(p):
                        self.key_print(ord(" "))
                        

    def key_back(self):
        # Key Backspace
        if self.lines_col==0:
            if self.lines_row!=0:
                store_len = len(self.lines[self.lines_row-1])
                self.lines[self.lines_row-1] = self.lines[self.lines_row-1]+self.lines[self.lines_row]
                self.lines.pop(self.lines_row)
                self.number_of_lines-=1
                self.lines_row-=1
                self.lines_col=store_len
                if self.cursor_col>0:
                    if store_len>self.w:
                        self.scroll_col=store_len-self.w+self.left_bound+1
                        self.cursor_col=self.w-1
                    else:
                        self.cursor_col=store_len+self.left_bound
                if self.scroll_row>0:
                    self.scroll_row-=1
                elif self.cursor_row>1:
                    self.cursor_row-=1

            return
        if self.lines_col>0 and self.lines_col<len(self.lines[self.lines_row])-1:
            self.lines[self.lines_row] = self.lines[self.lines_row][:self.lines_col-1]+self.lines[self.lines_row][self.lines_col:]
        elif self.lines_col>0:
            self.lines[self.lines_row] = self.lines[self.lines_row][:self.lines_col-1]
        if self.cursor_col>self.left_bound:
            self.cursor_col-=1
        elif self.scroll_col>0:
            self.scroll_col-=1
        if self.lines_col>0:
            self.lines_col-=1

    def key_print(self,key):
        # Print Key
        self.lines[self.lines_row] = self.lines[self.lines_row][:self.lines_col]+chr(key)+self.lines[self.lines_row][self.lines_col:]
        if self.cursor_col<self.w-1:
            self.cursor_col+=1
        else:
            self.scroll_col+=1
        self.lines_col+=1

    def start(self):
        # Start Main loop of editor
        self.lines = self.file.readlines()
        if len(self.lines)==0:
            self.lines = [""]
        self.number_of_lines = len(self.lines)
        for line in range(self.number_of_lines):
            self.lines[line] = self.lines[line].replace("\n","")
        # self.lines[-1] = self.lines[-1]+" "
        self.lenth_of_num = len(str(self.number_of_lines))
        self.scroll_row = 0
        self.scrolled_right = False
        self.scroll_col = 0
        self.cursor_row = 1
        self.lines_row = 0
        self.lines_col = 0
        self.cursor_col = len(str(self.number_of_lines))+3
        self.left_bound = len(str(self.number_of_lines))+3
        curses.curs_set(1)
        self.options("c")
        self.print_screen(3)
        self.move_cursor()
        self.stdscr.refresh()
        while 1:
            self.left_bound = len(str(self.number_of_lines))+3
            self.lenth_of_num = len(str(self.number_of_lines))
            self.print_screen(3)
            self.print_position()
            self.move_cursor()
            self.stdscr.refresh()
            key = self.stdscr.getch()
            # exit, will not keep like this, just for now:
            if key==27:
                self.options("nc")
                self.move_cursor()
                self.print_position()
                while 1:
                    key = self.stdscr.getch()
                    if key==ord("w"):
                        Editor.tmp_saver(self.lines,self.path,self.number_of_lines)

                    if key==ord("q"):
                        try:
                            if not filecmp.cmp(self.path,self.temp_file):
                                self.stdscr.addstr(0,2,"Press d to discard and exit")
                                key = self.stdscr.getch()
                                if key==ord("d"):
                                    pass
                                else:
                                    self.stdscr.addstr(0,2," "*27,curses.color_pair(5))
                                    continue
                        except:
                            pass
                        try:
                            os.remove(self.temp_file)
                        except:
                            pass
                        option(self.stdscr,self.h,self.w)
                        self.stdscr.refresh()
                        self.stdscr.addstr(self.h-1,0,copy,curses.color_pair(15))
                        curses.curs_set(0)
                        return
                    elif key==ord("s"):
                        self.options("v")
                        self.move_cursor()
                        self.print_position()
                        self.cut_copy_paste()
                        break
                    elif key==ord("i"):
                        break
                self.options("c")
                self.move_cursor()
                self.print_position()
                continue

            if key==6:
                self.find()
                continue

            if key==curses.KEY_DOWN:
                self.key_down()

            elif key==curses.KEY_UP:
                self.key_up()

            elif key==curses.KEY_LEFT:
                self.key_left()
            
            elif key==curses.KEY_RIGHT:
                self.key_right()

            elif key==curses.KEY_ENTER or key==10 or key==13:
                self.key_enter()

            elif key==curses.KEY_BACKSPACE:
                self.key_back()

            elif key==9:
                for oo in range(4):
                    self.key_print(ord(" "))
            elif key==ord('"') and self.comments:
                self.key_print(key)
                self.key_print(key)
                self.key_left()
            elif key==ord("(") and self.comments:
                self.key_print(key)
                self.key_print(ord(")"))
                self.key_left()
            elif key==ord("[") and self.comments:
                self.key_print(key)
                self.key_print(ord("]"))
                self.key_left()
            else:
                self.key_print(key)
            multiprocessing.Process(target=Editor.tmp_saver,args=(self.lines,self.temp_file,self.number_of_lines,)).start()
