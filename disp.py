import curses
import sys, os

def intro_scr(stdscr):
    scr_h, scr_w = stdscr.getmaxyx()
    disp_arr = ["" for x in range(scr_h - 1)]

    if scr_h >= 1:
        disp_arr[1] = "#" * (scr_w - 1)
        disp_arr[scr_h - 2] = "#" * (scr_w - 1)

    return disp_arr

def cmd_handler(usr_in, stdscr):
    scr_h, scr_w = stdscr.getmaxyx()
    is_exit = False
    if usr_in[0:1] == "\\" or usr_in[0:1] == "/":  # if the user is enterring a command
        if usr_in[1:] == "quit" or usr_in[1:] == "exit":
            is_exit = True
        usr_in = ""
        cursor = [2, scr_h-1]
        stdscr.clear()

    return is_exit

def input_handler(stdscr, cursor, usr_in_char, usr_in):
    scr_h, scr_w = stdscr.getmaxyx()
    if usr_in_char >= 32 and usr_in_char <= 126 and len(usr_in) < scr_w-3:  # if user typed in a displayable character
        stdscr.clear()
        usr_in = usr_in + chr(usr_in_char)
        cursor[0] = min(cursor[0]+1,scr_w-1)
    elif usr_in_char == 8 or usr_in_char == 127:  # if user typed in backspace
        stdscr.clear()
        usr_in = usr_in[:-1]
        cursor[0] = max(cursor[0]-1,2)

    return cursor, usr_in


def push_disp(stdscr, disp_arr, usr_in):
    scr_h, scr_w = stdscr.getmaxyx()
    for indx, txt in enumerate(disp_arr):
        stdscr.addstr(indx, 0, txt)

    stdscr.addstr(scr_h-1, 0, ">")  # user input indicator
    stdscr.addstr(scr_h-1, 2, usr_in)  # print the partially typed user input to the screen

   

def disp(stdscr):
    scr_h, scr_w = stdscr.getmaxyx()  # obtain the screen dimensions
    disp_arr = intro_scr(stdscr)  # build the intro screen

    cursor = [2, scr_h-1]  # initial position of the cursor
    usr_in = ""  # initial user input

    stdscr.clear()  # clear the display
    stdscr.refresh()  # display the current values of the display
    curses.halfdelay(5)

    is_exit = False
    while not is_exit:
        
        push_disp(stdscr, disp_arr, usr_in)

        usr_in_char = stdscr.getch(cursor[1], cursor[0])

        if usr_in_char == 10:  # if the user pressed enter
            is_exit = cmd_handler(usr_in, stdscr)

        else:
            cursor, usr_in = input_handler(stdscr, cursor, usr_in_char, usr_in)
            
def main():
    curses.wrapper(disp)

if __name__ == "__main__":
    main()
