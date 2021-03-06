import keyword
import ast
from copy import deepcopy

import core_logic
import make_nodes
import operations
import validators

# TODO: Remove the current attr (Go back one)
# TODO: Have a blank line on top of for and while
# TODO: Actions that replaces the parent with the selected node
# (If the types match), or maybe yank, up, put does the job.
# TODO: A way to paste from stack overflow
# TODO: A way of inserting None
# TODO: Default values for function parameters
# TODO: Have a lambda use the selected expression as it's initial body
# TODO: A way of inserting \n

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
def insert(cursor_trail, tree, _):
    """Adds an element inside the node.
    It's useful to unempty an empty container (like a list)
    before populating it using "append" """

    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)
    if hasattr(selected_node, "bases"):
        # Add a new base class to the class 
        selected_node.bases.append(ast.Name(id="BaseClass", ctx=ast.Load()))

    # It doesn't make sense to insert into a body because they can't ever be empty
    # Except for the Module node
    elif isinstance(selected_node, ast.Module):
        selected_node.body.append(make_nodes.make_pass())

    elif isinstance(selected_node, ast.arguments):

        arg = make_nodes.make_arg()

        # Make the name unique
        arg.arg = core_logic.get_unique_name(arg.arg, selected_node)

        selected_node.args.append(arg)
        return [0]

    # Call has the args list as a list of expressions
    # That's different from function definitions, where it's a list of arguments
    # The grammar is really confusing when it comes to those "args"
    elif isinstance(selected_node, ast.Call):
        arg = make_nodes.make_expression()
        selected_node.args.append(arg)
        return [0]

    elif hasattr(selected_node, "elts"):
        ctx = core_logic.get_immediate_context(cursor_trail, tree)
        selected_node.elts.append(make_nodes.make_expression(ctx=ctx))

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
                value = value if value is not None else make_node.make_expression()
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

    # Assign -> Augmented Assign
    # Raise -> Add the cause (as in "raise foo from bar")
    # Assert -> Add the message
    # Import -> ImportFrom
    # alias -> add an asname (Which is kind of the whole point of the alias node)
    # comprehension -> add an if clause
    # yield -> add the thing to yield
    # Name -> starred
    # Index -> Slice

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
        new_names = [make_nodes.make_alias()] if new_names == [] else selected_node.names

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
    
    elif isinstance(selected_node, ast.comprehension):
        # Toggle the if clause
        if selected_node.ifs == []:
            selected_node.ifs = [make_nodes.make_expression()]
        else: 
            selected_node.ifs = []

    elif isinstance(selected_node, ast.Yield):
        # Toggle the thing to yield
        if selected_node.value is None:
            selected_node.value = make_nodes.make_expression()
        else: 
            selected_node.value = None

    elif isinstance(selected_node, ast.Name):
        # Make it into an ast.Starred

        if not core_logic.core_is_within_field(
                cursor_trail,
                tree,
                ast.Assign,
                "targets"
                ):

            print("Can't have a starred variable outside of an assignment")
            return

        # Does this check make the above one useless?
        parent = core_logic.get_node_at_cursor(cursor_trail[:-1], tree)
        if not (isinstance(parent, ast.Tuple) or isinstance(parent, ast.List)):
            print("A starred expression must be within a list or a tuple")
            return

        parent = core_logic.get_node_at_cursor(cursor_trail[:-1], tree)

        if isinstance(parent, ast.Assign) and len(parent.targets) <= 1:
            print("A starred expression can't be alone in an assignment")
            return

        # TODO: Make starred's work for function params
        starred = ast.Starred(
                value = selected_node,
                ctx = selected_node.ctx
                )

        core_logic.set_node_at_cursor(cursor_trail, tree, starred)

    elif (isinstance(selected_node, ast.Starred)
            and isinstance((name := selected_node.value), ast.Name)) :

        # Change the node to be the name
        core_logic.set_node_at_cursor(cursor_trail, tree, name)
    
    elif isinstance(selected_node, ast.Index):
        slice = ast.Slice(
                lower=selected_node.value,
                upper=make_nodes.make_expression(),
                step=None
                )

        core_logic.set_node_at_cursor(cursor_trail, tree, slice)

    elif isinstance(selected_node, ast.Slice):
        index = ast.Index(
                value=selected_node.lower,
                )

        core_logic.set_node_at_cursor(cursor_trail, tree, index)

    else:
        # TODO: Change all of the "this node" to the node's class
        print("Can't extend this node")

    return []


def yank(cursor_trail, tree, _):
    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)
    # TODO: Multi level undo
    tree.states_for_actions["yanked"] = deepcopy(selected_node)
    

def put(cursor_trail, tree, _):
    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)

    try:
        yanked = tree.states_for_actions["yanked"]
    except KeyError:
        print("No yanked node")
        return

    # Or they have the same type
    # or they are both statements
    # or they are both expressions
    # or it's an expression being pasted into a statement
    # (In this case we'll wrap it into an Expr)
    # otherwise, we can't paste here
    if not (
               (type(selected_node) == type(yanked))
            or (isinstance(selected_node, ast.stmt) and isinstance(yanked, ast.stmt))
            or (isinstance(selected_node, ast.stmt) and isinstance(yanked, ast.expr))
            or (isinstance(selected_node, ast.expr) and isinstance(yanked, ast.expr))
           ):

         print("Cannot paste here, the type is different")
         return

    if isinstance(selected_node, ast.stmt) and isinstance(yanked, ast.expr):
        # Fix the type by wrapping the expression into an Expr
        # Making both into ast.stmt
        yanked = ast.Expr(value=yanked)

    # TODO: Add the mirror logic for unwrapping an Expr into it's value

    core_logic.set_node_at_cursor(cursor_trail, tree, yanked)


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

    "yank": (yank, False),
    "put": (put, False)
}


# Add the node making functions from the make_nodes file
for key in make_nodes.nodes.keys():
    actions["make_" + key] = make_nodes.make_node(key)
