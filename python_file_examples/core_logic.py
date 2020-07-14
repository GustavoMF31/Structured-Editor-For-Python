import ast
from functools import reduce


def list_children(ast_node):

    # Those are reported as nodes by ast.iter_child_nodes(parent)
    # But cause trouble down the road
    # (AttributeErrors when navigating to them)
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
            ast.NotIn
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


# TODO: Make sure this works
def is_valid_ast(tree):
    """Make sure an ast is valid by trying to compile it"""
     
    try:
        ast.fix_missing_locations(tree)
        compiled = compile(tree, "<test-ast>", "exec")
    except (SyntaxError, ValueError, TypeError) as e:
        return (False, e)
    
    return (True, None)


def core_act(action, in_place, is_local, cursor_trail, ast, get_vim_input):
    """Performs the pure part of executing an action
    (at least kind of pure)"""

    selected_node = get_node_at_cursor(cursor_trail, ast)

    if in_place:
        if is_local:
            # In this case the action will modify the node
            cursor_movement = action(selected_node, get_vim_input)
        else:
            # In this case the action modifies the ast and the cursor_trail
            # For functions with access to the full cursor trail
            # There is no point using the cursor_movement variable
            action(cursor_trail, ast, get_vim_input)
            cursor_movement = []

    # Non in place actions are useful for functions that create nodes
    else:
        if is_local:
            # In this case the action returns a new node 
            # And we set it as the current one
            cursor_movement, new_node = action(selected_node, get_vim_input)
        else:
            # In this case the function returns the new everything
            # For functions with access to the full cursor trail
            # There is no point using the cursor_movement variable
            cursor_trail, ast = action(cursor_trail, ast, get_vim_input)
            cursor_movement = []

        # TODO: Make sure this doesn't break whe cursor_trail was
        # modified by some function
        set_node_at_cursor(cursor_trail, ast, new_node) 

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

