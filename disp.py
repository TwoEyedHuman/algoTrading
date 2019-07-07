import curses
import sys, os

def disp(stdscr):
    scr_h, scr_w  =stdscr.getmaxyx()

    is_exit = False
    disp_arr = ["" for x in range(scr_h-1)]
    disp_arr[4] = "HELLO"

    cursor = [2, scr_h-1]
    usr_in = ""

    stdscr.clear()
    stdscr.refresh()
    curses.halfdelay(5)

    while (~is_exit):
        
        for indx, txt in enumerate(disp_arr):
            stdscr.addstr(indx, 0, txt)

        stdscr.addstr(scr_h-1, 0, ">")  # user input indicator
        stdscr.addstr(scr_h-1, 2, usr_in)  # print the partially typed user input to the screen

        usr_in_char = stdscr.getch(cursor[1], cursor[0])

        if usr_in_char == 10:  # if the user pressed enter
            if usr_in[0:1] == "\\" or usr_in[0:1] == "/":
                if usr_in[1:] == "quit" or usr_in[1:] == "exit":
                    is_exit = 0
                usr_in = ""
                cursor = [2, scr_h-1]
                stdscr.clear()

        else:
            if usr_in_char >= 32 and usr_in_char <= 126 and len(usr_in) < scr_w-3:  # if user typed in a displayable character
                stdscr.clear()
                usr_in = usr_in + chr(usr_in_char)
                cursor[0] = min(cursor[0]+1,scr_w-1)
            elif usr_in_char == 8 or usr_in_char == 127:  # if user typed in backspace
                stdscr.clear()
                usr_in = usr_in[:-1]
                cursor[0] = max(cursor[0]-1,2)

            
def main():
    curses.wrapper(disp)

if __name__ == "__main__":
    main()
