import keyword
import ast
from copy import deepcopy

import core_logic
import make_nodes


def is_renameable(node):
    return (   getattr(node, "id", False)
            or getattr(node, "name", False)
            or getattr(node, "module", False)
            or getattr(node, "attr", False)
            or has_string_value(node)
           )


def has_string_value(node):
    value = getattr(node, "value", False)
    if not value:
        return False

    return type(value) == str


def rename(new_name, node):

    # If the attribute isn't there, default to False
    if getattr(node, "id", False):
        node.id = new_name
    elif getattr(node, "name", False):
        node.name = new_name
    elif getattr(node, "module", False):
        node.module = new_name
    elif getattr(node, "attr", False):
        node.attr = new_name
    elif has_string_value(node):
        node.value = new_name
    else:
        raise ValueError(
                f"{node.__class__.__name__} node isn't renameable"
                )

    return node


def is_identifier(ident: str) -> bool:
    """Determines if string is valid Python identifier."""

    if not ident.isidentifier():
        return False

    if keyword.iskeyword(ident):
        return False

    return True


def user_input_rename(node, get_user_input):

    # TODO: Rename string literals
    # TODO: Enforce naming conventions
    # (like classes should start with a capital letter)
    if not is_renameable(node):
        print("Can't rename this type of node")
        return [] 

    new_name = get_user_input("Rename to: ") 

    if not is_identifier(new_name):
        print("Invalid name")
        return [] 
    
    rename(new_name, node)

    # The [] means not to move the cursor
    return [] 

def move_cursor_down(node, _):
    children = core_logic.list_children(node)

    # Ensure the selected node has children
    if children == []:
        return []

    print(children[0].__class__.__name__)

    # Move the cursor down
    return [0]

def move_cursor_left(cursor_trail, ast, _):
    if cursor_trail == []:
        return
    
    # decrement in one the index of the last child
    # effectively moving back to the previous sibling
    cursor_trail.append(cursor_trail.pop() - 1)
    current_node = core_logic.get_node_at_cursor(cursor_trail, ast)
    print(current_node.__class__.__name__)

def move_cursor_up(cursor_trail, ast, _):
    if cursor_trail == []:
        return
    
    cursor_trail.pop()
    current_node = core_logic.get_node_at_cursor(cursor_trail, ast)
    print(current_node.__class__.__name__)


def move_cursor_right(cursor_trail, ast, _):
    if cursor_trail == []:
        return

    # Increment in one the index of the last child
    # Effectively moving to the next sibling
    cursor_trail.append(cursor_trail.pop() + 1)
    current_node = core_logic.get_node_at_cursor(cursor_trail, ast)
    print(current_node.__class__.__name__)


# TODO: Move these none guys to the make_node file
def make_none_expression():
    return ast.Name(id="None", ctx=ast.Load())


def make_none_statement():
    return ast.Expr(value=make_none_expression())


# The append function as it is right now essentially does two things:
# It clones the current thing in the current array like structure
# and appends a none when you have the whole array like structure selected
# I think it should just do the first one
def append(cursor_trail, tree, _):
    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)

    if getattr(selected_node, "elts", False):
        selected_node.elts.append(make_none_expression())
        return

    if getattr(selected_node, "body", False):
        # I think there is a case where body is not a list
        # TODO: Check the ASDL and fix this
        selected_node.body.append(make_none_statement())
        return

    parent = core_logic.get_node_at_cursor(cursor_trail[:-1], tree)
    fieldname, index = core_logic.get_field_name_for_child(parent, selected_node)

    # TODO: implemente the make_default_of function
    # that returns the simplest of an ast node
    # (most likely a bunch on nodes structurally nested)
    # for now, let's just make a copy of the currently selected node
    if index is not None:
        children = getattr(parent, fieldname)
        children.insert(index + 1, deepcopy(selected_node))
        return

    # If we haven't returned yet, we can't append to it
    print("Can't append to this type of node")
       

    
# Local actions only interact with the current node and it's children
# While contextual (non local) actions can interact with the whole AST


# In place actions modify their arguments
# While non in place actions return the new versions of them

# The actions should be roughly ordered by complexity
# Simpler ones, like moving the cursor, coming first
actions = {
        # "action_name" : (function, in_place?, is_local?)
        "cursor_down" : (move_cursor_down, True, True),
        "cursor_up" : (move_cursor_up, True, False),
        "cursor_right" : (move_cursor_right, True, False),
        "cursor_left" : (move_cursor_left, True, False),
        "rename" : (user_input_rename, True, True),
        "make_function" : make_nodes.make_node("function"),
        "make_class" : make_nodes.make_node("class"),
        "make_import": make_nodes.make_node("import"),
        "append" : (append, True, False),

        }

