import ast
from functools import reduce


def list_children(ast_node):

    # Those are reported as nodes by ast.iter_child_nodes(parent)
    # But cause trouble down the road
    # (AttributeErrors when navigating to them)
    # TODO: Move the banned nodes to a different file
    troublemaker_nodes = [
            ast.Load,
            ast.Store,
            ast.Del,
            ast.AugLoad,
            ast.AugStore,
            ast.Param,
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.Is,
            ast.IsNot,
            ast.In,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.MatMult,
            ast.Div,
            ast.Mod,
            ast.Pow,
            ast.LShift,
            ast.RShift,
            ast.BitOr,
            ast.BitXor,
            ast.BitAnd,
            ast.FloorDiv,
            ast.And,
            ast.Or,
            ]

    # So filter them out
    return list(filter(
                lambda x : type(x) not in troublemaker_nodes,
                ast.iter_child_nodes(ast_node)
            ))


def get_nth_children_wrapping_around(node, n):
    children = list_children(node)
    length = len(children)
    return children[n % length]


def get_node_at_cursor(cursor_trail, full_ast):
    return reduce(
            get_nth_children_wrapping_around,
            cursor_trail,
            full_ast
            )


def get_field_name_for_child(parent, child): 
    
    fields = list(ast.iter_fields(parent))

    for (field_name, field_content) in fields:
        if type(field_content) == list:
            for index, node in enumerate(field_content):
                if node == child:
                    return (field_name, index)
        
        if field_content == child:
            return (field_name, None)


def is_valid_ast(tree):
    """Make sure an ast is valid by trying to compile it"""
     
    try:
        ast.fix_missing_locations(tree)
        compiled = compile(tree, "<test-ast>", "exec")
    except (SyntaxError, ValueError, TypeError) as e:
        return (False, e)
    
    return (True, None)


def core_act(action, is_local, cursor_trail, ast, get_vim_input):
    """Performs the pure part of executing an action
    (at least kind of pure)"""

    selected_node = get_node_at_cursor(cursor_trail, ast)

    if is_local:
        # In this case the action will modify the node
        cursor_movement = action(selected_node, get_vim_input)
    else:
        # In this case the action modifies the ast and the cursor_trail
        # For functions with access to the full cursor trail
        # There is no point using the cursor_movement variable
        action(cursor_trail, ast, get_vim_input)
        cursor_movement = []

    # Move the cursor according to the action
    cursor_trail = cursor_trail + cursor_movement
    
    return (cursor_trail, ast)


def set_node_at_cursor(cursor_trail, ast, node):
    # Cannot set the module itself
    if cursor_trail == []:
        return

    last_child_index = cursor_trail[-1]
    parent = get_node_at_cursor(cursor_trail[:-1], ast)
    child = get_nth_children_wrapping_around(parent, last_child_index)

    # Will fail to pattern match if it returns None
    # Maybe fail better somehow
    field_name, index = get_field_name_for_child(
            parent,
            child)

    if index is not None:
        # In this case it was within a list
        list = getattr(parent, field_name)
        list[index] = node
    else:
        setattr(parent, field_name, node)


def core_is_within(cursor_trail, tree, ast_node_type): 
    # A Module isn't within anything
    if cursor_trail == []:
        return False

    parent = get_node_at_cursor(cursor_trail[:-1], tree)

    # We are within the ast_node_type if our parent is of the type
    # or our parent itself is within the ast_node_type
    # TODO: Consider using isinstance instead of comparing the type
    return (type(parent) == ast_node_type
            or core_is_within(cursor_trail[:-1], tree, ast_node_type)
            )

def core_is_within_field(cursor_trail, tree, ast_node_type, fieldname): 
    """ Checks if the selected node is within a specific field of a
    parent of the specified type
    """

    # A Module isn't within anything
    if cursor_trail == []:
        return False

    parent = get_node_at_cursor(cursor_trail[:-1], tree)
    child = get_node_at_cursor(cursor_trail, tree)

    # We are within the ast_node_type if our parent is of the type
    # and the fieldname is the specified one
    # or our parent itself is within the ast_node_type with the right field

    return (
            (isinstance(parent, ast_node_type) and get_field_name_for_child(parent, child)[0] == fieldname) 
            or core_is_within_field(cursor_trail[:-1], tree, ast_node_type, fieldname)
            )


def core_is_not_in_context(cursor_trail, tree, ctx):
    return type(get_immediate_context(cursor_trail, tree)) != ctx


def core_is_in_context(cursor_trail, tree, ctx):
    return type(get_immediate_context(cursor_trail, tree)) == ctx


def get_immediate_context(cursor_trail, tree):
    """Returns the context of the closer parent that has one"""

    # A Module is definetly not in a context
    if cursor_trail == []:
        return None

    selected_node = get_node_at_cursor(cursor_trail, tree)
    if getattr(selected_node, "ctx", False):
        return selected_node.ctx 
    else:
        return get_immediate_context(cursor_trail[:-1], tree)


def get_unique_name(initial_name, arguments) -> str:
    """Add underscores until the name is unique"""

    # TODO: Do something about other types of arguments (like posonlyargs and etc...)
    already_taken_names = list(map(lambda x: x.arg, arguments.args))

    name = initial_name 
    while name in already_taken_names:
        # Append underscores until the name is valid again
        name = name + "_"

    return name


def is_being_assigned_to(cursor_trail, tree):
    """Finds out if the selected expression is
    in the left side of an assignment"""

    # The module is not being assigned to
    if cursor_trail == []:
        return False
    
    selected_node = get_node_at_cursor(cursor_trail, tree)
    parent = get_node_at_cursor(cursor_trail[:-1], tree)

    if isinstance(parent, ast.Assign):
        # If the parent is the assignment, let's check if we are in it's left side
        fieldname, index = get_field_name_for_child(parent, selected_node)
        return fieldname == "targets"

    else:
        return is_being_assigned_to(cursor_trail[:-1], tree)
