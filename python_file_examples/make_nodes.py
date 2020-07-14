import ast


def make_node(node_name):

    def action(selected_node, _):
        ast_node_type, creator = nodes[node_name]
        
        # Never touch the module
        if type(selected_node) == ast.Module:
            return ([], selected_node)

        # Make sure the node is allowed to be placed here
        if not isinstance(selected_node, ast_node_type):
            print(f"Can't have a {node_name} here")
            return ([], selected_node)

        return ([], creator())

    # (action, in_place, is_local)
    return (action, False, True)


def make_default_class():
    """ClassDef(identifier name,
             expr* bases,
             keyword* keywords,
             stmt* body,
             expr* decorator_list)"""

    class_definition = ast.ClassDef(
                name = "NewClass",
                bases = [],
                keywords = [],
                body = [ast.Pass()],
                decorator_list = [],
            )

    return class_definition
    

def make_default_function():
    """FunctionDef(identifier name, arguments args,
                       stmt* body, expr* decorator_list, expr? returns,
                       string? type_comment)"""
    

    function_definition = ast.FunctionDef(
                name = "new_function",
                args = make_default_arguments(),
                body = [ast.Pass()],
                decorator_list = [],
                returns = None,
                type_comment = None
            )

    
    return function_definition


def make_default_import():
    return ast.Import(names=[make_default_alias()])


def make_default_arguments():
    return ast.arguments(
            posonlyargs=[],
            args=[],
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[]
        )

def make_default_alias(default_name="module", default_asname=None):
    return ast.alias(name=default_name, asname=default_asname)

nodes = {
        # "name" : (type, creator)
        "class": (ast.stmt, make_default_class),
        "function": (ast.stmt, make_default_function),
        "import": (ast.stmt, make_default_import)
 }


