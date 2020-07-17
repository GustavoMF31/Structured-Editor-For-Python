import keyword
import ast
from copy import deepcopy

import core_logic
import make_nodes
import operations
import validators

# TODO: Call that calls a function !on! the selected expression
# TODO: Copy and paste
# TODO: Remove the current attr (Go back one)
# TODO: Have a blank line on top of for and while

def is_renameable(node):
    return (   hasattr(node, "id")
            or hasattr(node, "name")
            # Checking for 'asname', for aliases isn't needed
            # because they already have a name attribute
            or hasattr(node, "module")
            or hasattr(node, "attr")
            or hasattr(node, "arg")
            or isinstance(node, ast.Global) 
            or isinstance(node, ast.Nonlocal) 
            or has_string_value(node)
           )


def has_string_value(node):
    value = getattr(node, "value", False)
    if not value:
        return False

    return type(value) == str


def rename(new_name, node, maybe_index):

    if hasattr(node, "id"):
        node.id = new_name
    # Only rename by asname if it's not empty
    elif hasattr(node, "asname") and node.asname is not None:
        node.asname = new_name
    elif hasattr(node, "name"):
        node.name = new_name
    elif hasattr(node, "module"):
        node.module = new_name
    elif hasattr(node, "attr"):
        node.attr = new_name
    elif hasattr(node, "arg"):
        node.arg = new_name
    elif has_string_value(node):
        node.value = new_name
    # Must come after, otherwise imports, that have both names and a string value
    # will be renamed by index when they don't need to
    elif hasattr(node, "names"):
        node.names[maybe_index] = new_name
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

    # TODO: Enforce naming conventions
    # (like classes should start with a capital letter)
    if not is_renameable(node):
        print("Can't rename this type of node")
        return [] 

    new_name = get_user_input("Rename to: ") 

    if not is_identifier(new_name):
        print("Invalid name")
        return []

    # global and nonlocal keywords are annoying:
    # they have a list of identifiers instead of list of nodes,
    # so we can't select them with the cursor.
    # Instead, we ask for the index explicitly
    if type(node) == ast.Global or type(node) == ast.Nonlocal:
        try:
            index = int(get_user_input("Rename at index: "))
        except ValueError:
            print("Bad index")
            return [] 

        if index >= len(node.names):
            print("Bad index")
            return []

        rename(new_name, node, index)

    else:
        rename(new_name, node, None)

    # The [] means not to move the cursor
    return [] 


# TODO: Skip moving through Expr nodes for a better moving experience: No repeated 
# No repeated down presses without a visual change
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


# TODO: Also skip the Expr nodes
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


# TODO: Move to the inserted node (hopefully it's the first child)
# TODO: Insert inside body of the module
def insert(cursor_trail, tree, _):
    """Adds an element to the body of the node.
    It's useful to unempty an empty container (like a list)
    before populating it using "append" """

    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)
    if hasattr(selected_node, "bases"):
        # Add a new base class to the class 
        selected_node.bases.append(ast.Name(id="BaseClass", ctx=ast.Load()))

    elif isinstance(selected_node, ast.arguments):

        arg = make_nodes.make_default_arg()

        # Make the name unique
        arg.arg = core_logic.get_unique_name(arg.arg, selected_node)

        selected_node.args.append(arg)
        return [0]

    # Call has the args list as a list of expressions
    # That's different from function definitions, where it's a list of arguments
    # The grammar is really confusing when it comes to those "args"
    elif isinstance(selected_node, ast.Call):
        arg = make_nodes.make_default_expression()
        selected_node.args.append(arg)
        return [0]

    elif hasattr(selected_node, "elts"):
        ctx = core_logic.get_immediate_context(cursor_trail, tree)
        selected_node.elts.append(make_nodes.make_default_expression(ctx=ctx))

        return [-1]

    else:
        print("Can't insert inside this node")
        return []


# TODO: Multiple exceptions for the try block
def append(cursor_trail, tree, _):
    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)

    # Don't touch the module
    if isinstance(selected_node, ast.Module):
        return

    parent = core_logic.get_node_at_cursor(cursor_trail[:-1], tree)
    fieldname, index = core_logic.get_field_name_for_child(parent, selected_node)

    if index is not None:
        children = getattr(parent, fieldname)
        children.insert(index + 1, deepcopy(selected_node))

        # A dictionary should always have the same amount of keys and values
        # So let's be careful and keep them synced
        if type(parent) == ast.Dict:
            if fieldname == "keys":
                parent.values.insert(index + 1, deepcopy(parent.values[index]))
            if fieldname == "values":
                parent.keys.insert(index + 1, deepcopy(parent.keys[index]))

        # Comparisons are similar:
        # They should have the same number of comparators and comparands
        if type(parent) == ast.Compare:
            parent.ops.insert(index + 1, deepcopy(parent.ops[index]))

        # In the case we are within function arguments
        # two of them with the same name can break stuff.
        # So let's give the new one a different name 
        if type(selected_node) == ast.arg:
            children[index + 1].arg = core_logic.get_unique_name(selected_node.arg, parent)

        return

    # If we haven't returned yet, we can't append to it
    print("Can't append to this type of node")
       

# TODO: Recalculate the index after deleting
# to avoid the weird cursor jumps because of the wrapping around
def delete(cursor_trail, tree, _):

    # Don't touch the module
    if cursor_trail == []:
        return

    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)
    parent = core_logic.get_node_at_cursor(cursor_trail[:-1], tree)
    fieldname, index = core_logic.get_field_name_for_child(parent, selected_node)

    if index is not None:
        children_list = getattr(parent, fieldname)

        # A try block needs to have at least one of those not empty
        if fieldname == "handlers" or fieldname == "finalbody":
            if len(parent.handlers) + len(parent.finalbody)  == 1:
                print("A Try block needs handlers or a finally")
                return

        if isinstance(parent, ast.Dict):
            # If it's a dictionary, keep the key value pairs synced
            # by deleting the correspondig key/value
            if fieldname == "keys":
                parent.values.pop(index)

            if fieldname == "values":
                parent.keys.pop(index)

        if isinstance(parent, ast.BoolOp):
            if len(children_list) < 3:
                print("A boolean operation must have at least 2 operands")
                return

        # These kinds of nodes can't be empty
        elif  (  fieldname == "names"
            or fieldname == "body"
            or fieldname == "items"
            or fieldname == "targets"):

            if len(children_list) < 2:
                print("This can't be empty")
                return
        
        children_list.pop(index)

        # If there are no more children, move up
        if len(children_list) == 0:
            cursor_trail.pop()

    else:
        # setattr(parent, fieldname, None)
        pass


def insert_annotation(cursor_trail, tree, _):
    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)
    default_annotation = ast.Name(id="annotation", ctx=ast.Load())

    if hasattr(selected_node, "returns"):
        # Toggle the return annotation
        if selected_node.returns is None:
            selected_node.returns = default_annotation 
        else:
            selected_node.returns = None

    # The assignments must come befor the generic annotation case
    # Because otherwise the annotated assignment's annotation will be
    # erroneously set to None
    elif isinstance(selected_node, ast.Assign):
        # Make it into an annotated assign
        annotated_assign = ast.AnnAssign(
                target=selected_node.targets[0],
                annotation=default_annotation,
                value=selected_node.value,
                # TODO: What does simple mean?
                simple=1
                ) 

        core_logic.set_node_at_cursor(cursor_trail, tree, annotated_assign)

    elif isinstance(selected_node, ast.AnnAssign):
        # Make it into a regular assign
        value = selected_node.value

        assign = ast.Assign(
                targets=[selected_node.target],
                value = value if value is not None else make_node.make_default_expression()
                )

        core_logic.set_node_at_cursor(cursor_trail, tree, assign)

    elif hasattr(selected_node, "annotation"):
        # Toggle the annotation
        if selected_node.annotation is None:
            selected_node.annotation = default_annotation
        else:
            selected_node.annotation = None

    else:
        print("This node can't have type annotations")

    return []


def insert_int(cursor_trail, tree, get_input):
    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)

    if not validators.is_simple_expression(cursor_trail, tree):
        print("Can't have an int here")
        return

    try:
        n = int(get_input("int: "))
    except ValueError:
        print("Invalid int")
        return

    constant = ast.Constant(value=n, kind=None)
    core_logic.set_node_at_cursor(cursor_trail, tree, constant)


def extend(cursor_trail, tree, _):
    """ Bulks up the selected node.
    Specifically how depends on the node"""

    # If -> add else
    # For (Async too) -> add else
    # While -> add else
    # Try -> add else. (TODO: Do something about the finnaly block too)

    # Function (Async too) -> add decorator
    # Class -> add decorator 

    # TODO: Assign -> Augmented Assign
    # Raise -> Adds the cause (as in "raise foo from bar")
    # Assert -> Add the message
    # Import -> ImportFrom
    # alias -> add an asname (Which is kind of the whole point of the alias node)

    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)

    # The if expression has an orelse field that is an expression, not a list of statements
    if hasattr(selected_node, "orelse") and not isinstance(selected_node, ast.IfExp): 
        
        # Toggle the else branch
        if selected_node.orelse == []:
            selected_node.orelse = [ast.Pass()]
        else:
            selected_node.orelse = []

    elif hasattr(selected_node, "decorator_list"):

        # Toggle the decorator_list
        if selected_node.decorator_list == []:
            selected_node.decorator_list = [ast.Name(id="decorator", ctx=ast.Load())]
        else:
            selected_node.decorator_list = []

    elif isinstance(selected_node, ast.Raise):

        # toggle the cause
        if selected_node.cause is None:
            selected_node.cause = ast.Name(id="cause", ctx=ast.Load())
        else:
            selected_node.cause = None

    elif isinstance(selected_node, ast.Assert):

        # toggle the message
        if selected_node.msg is None:
            selected_node.msg = ast.Constant(value="message", kind=None)
        else:
            selected_node.msg = None

    elif isinstance(selected_node, ast.Import):

        # TODO: Break up an import as a bunch of ImportFrom instead of losing info
        # by just creating a single one
        new_names = selected_node.names
        new_names = [make_nodes.make_default_alias()] if new_names == [] else selected_node.names

        new_import = ast.ImportFrom(
                module = selected_node.names[0].name,
                names = selected_node.names,
                # TODO: What does level mean? (Is it like going up in the folder hierarchy?)
                # Even though the grammar allows level to be None, that makes astor break
                # So, let's initialize it to 0 (Still don't quite know what that means)
                level = 0
                )

        core_logic.set_node_at_cursor(cursor_trail, tree, new_import)

    elif isinstance(selected_node, ast.ImportFrom):

        new_import = ast.Import(names=selected_node.names)
        core_logic.set_node_at_cursor(cursor_trail, tree, new_import)

    elif isinstance(selected_node, ast.alias):
        # Toggle the asname
        if selected_node.asname is None:
            selected_node.asname = "alias"
        else: 
            selected_node.asname = None

    else:
        # TODO: Change all of the "this node" to the node's class
        print("Can't extend this node")

    return []


# Local actions only interact with the current node and it's children
# While contextual (non local) actions can interact with the whole AST

# The actions should be roughly ordered by complexity
# Simpler ones, like moving the cursor, coming first
actions = {
    # "action"     : (function, is_local?)
    "cursor_down"  : (move_cursor_down, True),
    "cursor_up"    : (move_cursor_up, False),
    "cursor_right" : (move_cursor_right, False),
    "cursor_left"  : (move_cursor_left, False),
    "rename"       : (user_input_rename, True),
    "append"       : (append, False),
    "insert"       : (insert, False),
    "delete"       : (delete, False),
    "insert_int"          : (insert_int, False),
    "type_annotation"       : (insert_annotation, False),
    "extend"      : (extend, False),
    # Binary operations
    "add"        : operations.to_operation(ast.Add),
    "subtract"        : operations.to_operation(ast.Sub),
    "multiply"        : operations.to_operation(ast.Mult),
    "divide"        : operations.to_operation(ast.Div),
    "mod"        : operations.to_operation(ast.Mod),
    "pow"        : operations.to_operation(ast.Pow),
    # Comparisons
    "equals"        : operations.to_comparison(ast.Eq),
    "greater_than"        : operations.to_comparison(ast.Gt),
    "greater_than_equals"        : operations.to_comparison(ast.GtE),
    "less_than"        : operations.to_comparison(ast.Lt),
    "less_than_equals"        : operations.to_comparison(ast.LtE),
    "is"        : operations.to_comparison(ast.Is),
    "in"        : operations.to_comparison(ast.In),
    # Boolean operation
    "and"        : operations.to_bool_op(ast.And),
    "or"        : operations.to_bool_op(ast.Or),
}


# Add the node making functions from the make_nodes file
for key in make_nodes.nodes.keys():
    actions["make_" + key] = make_nodes.make_node(key)
