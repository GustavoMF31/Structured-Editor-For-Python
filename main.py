import vim
import os
import sys
from copy import deepcopy

# TODO: Find a way to make comments work!
# Check that issue about comments on astor

# Get absolute path to the plugin
plugin_path = vim.eval("g:path")

# Get the absolute path to the current folder
current_folder = os.path.abspath(f'{plugin_path}/../')

# Add it to the system paths so we can import files on the same folder
sys.path.append(current_folder)

# Finally import it
from core_logic import *
import actions
import renderer


def render_view_to_buffer():
    selected_node = get_node_at_cursor(cursor_trail, ast)
    rendered_text = renderer.render_view(ast, selected_node, adjust_width(window.width))

    # Write the text to the buffer
    buffer[:] = rendered_text.split("\n")


def get_vim_input(message):
    vim.command("call inputsave()")
    vim.command("let user_input = input('" + message + "')")
    vim.command("call inputrestore()")
    return vim.eval("user_input")


def current_node():
    return get_node_at_cursor(cursor_trail, ast)


def save():

    with open(filename, "w", encoding="utf-8") as f:
        f.write(renderer.render_standard(ast))


def adjust_width(window_width):
    """Subtracts the width by 3 in case the numbers option is set,
    because the line numbers takes 3 columns from the screen's space"""
        
    if vim.eval("&number") or vim.eval("&relativenumber"):
        return window_width - 3

    return window_width


# Perform an action (A node modification)
def act(action_name):

    # Make reassigning these variables work
    global cursor_trail
    global ast

    action, is_local = actions.actions[action_name]
    
    cursor_trail, ast = core_act(
                action,
                is_local,
                cursor_trail,
                ast,
                get_vim_input
            )

    render_view_to_buffer()


# It's important to save the buffer because the currently selected buffer
# might stop being the python code one
# Useful info: https://vimhelp.org/if_pyth.txt.html#python-buffer
window = vim.current.window
buffer = vim.current.buffer
filename = buffer.name

# The original ast
ast = ast.parse("\n".join(buffer[:]))

# Set the initial action state dict
# Stores stuff like the copy and pasted node
ast.states_for_actions = {}

# Set the initial view
buffer[:] = renderer.render_view(ast, ast, adjust_width(window.width)).split("\n")

# Stores the path to the editing cursor
# An int n means the nth child of the current node
# n is used modulo the number of children, so negative number and huge
# numbers are allowed (They will wrap around)
cursor_trail = []

