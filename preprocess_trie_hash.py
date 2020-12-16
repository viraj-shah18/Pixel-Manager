from collections import defaultdict
paths = set()
# Trie Node
class Node:
    def __init__(self):
        self.children = defaultdict(bool)
        self.is_end = False
        self.path = []
    
# Trie 
class Trie:
    # Init trie
    def __init__(self):
        self.head = Node()

    # Insert into trie
    def insert(self,pattern,path):
        temp = self.head
        for i in range(len(pattern)):
            ind = ord(pattern[i])
            # print(ind)
            if temp.children[ind] == False:
                temp.children[ind] = Node()
            temp = temp.children[ind]
        temp.is_end = True
        temp.path+=[path]

    # search in trie
    def search(self,pattern):
        temp = self.head
        for i in range(len(pattern)):
            ind = ord(pattern[i])
            if temp is False or temp.children[ind] is False:
                return False
            temp = temp.children[ind]
        return temp.is_end,temp.path
    
    # find all prefixes
    def prefix_all(self,head,pattern,results):
        temp = head
        for ind,i in temp.children.items():
            if i:
                if i.is_end:
                    results.append((pattern+chr(ind),i.path))
                results = self.prefix_all(i,pattern+chr(ind),results)
        return results
        
    def prefix_search(self,pattern):
        results = []
        temp = self.head
        for i in range(len(pattern)):
            ind = ord(pattern[i])
            if temp.children[ind] == False:
                return results
            temp=temp.children[ind]
        if(temp.is_end):
            key = pattern
            results.append((key,temp.path))
        results = self.prefix_all(temp,pattern,results)
        return results
    
    # preprocess trie
    def preprocess(self,path):
        global paths
        global file
        try:
            if path not in paths:
                paths.add(path)
                file.write(path+"\n")
                for i in os.listdir(path):
                    k = 0
                    for j in range(len(path)):
                        if path[j]=="/":
                            k = j

                    if path[k+1:]==i:
                        continue
                    self.insert(i,path)
                    if os.path.isdir(path+"/"+i):
                        old = path
                        path+="/"+i
                        self.preprocess(path)
                        path = old
        except:
            pass

# make a list of paths which are in the trie
file = open('mypaths.txt',"w")

# below is a preloader implemented
import os,time
import curses
def prog(stdscr,h,w,kk):
    while not kk.values()[0]:
        curses.init_pair(100,1,10)
        curses.init_pair(200,2,25)
        for i in range(10):
            stdscr.addstr(0,0," "*w,curses.color_pair(1))
        stdscr.refresh()
        for i in range(0,w-1):
            if i<=5:
                stdscr.addstr(0,i," "*(i+1),curses.color_pair(200))
            elif i>=(w-5):
                stdscr.addstr(0,i," "*(w-i),curses.color_pair(200))
            else:
                stdscr.addstr(0,i," "*6,curses.color_pair(200))
            stdscr.refresh()
            if kk.values()[0]:
                break
            time.sleep(0.03)
            if i<=5:
                stdscr.addstr(0,i," "*(i+1),curses.color_pair(100))
            elif i>=(w-5):
                stdscr.addstr(0,i," "*(w-i),curses.color_pair(100))
            else:
                stdscr.addstr(0,i," "*6,curses.color_pair(100))
            stdscr.refresh()
    
