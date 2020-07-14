import ast
import core_logic
import validators as v

# The python 3.8 abstract grammar can be found at:
# https://docs.python.org/3/library/ast.html#abstract-grammar

# TODO: Get rid of all this make_default_thing in favor of just make_thing

def make_node(node_name):

    def action(cursor_trail, tree,  get_user_input):
        validator, creator = nodes[node_name]
        selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)
        
        # Never touch the module
        if type(selected_node) == ast.Module:
            return 

        if not validator(cursor_trail, tree):
            print(f"Can't have {node_name} here")
            return
        
        arguments = []

        # Dependent actions need to know more to return the right thing
        if node_name in dependent_actions:
            arguments = arguments + [cursor_trail, tree]

        if node_name in user_input_actions:
           arguments = arguments + [get_user_input]
        
        node_to_insert = creator(*arguments)

        # Special case: An expression may be placed where a statement
        # is expected, as long as it's wrapped in an ast.Expr
        if isinstance(selected_node, ast.stmt) and isinstance(node_to_insert, ast.expr):
            node_to_insert_as_statement = ast.Expr(value=node_to_insert)

            core_logic.set_node_at_cursor(cursor_trail, tree, node_to_insert_as_statement)
        else:
            core_logic.set_node_at_cursor(cursor_trail, tree, node_to_insert)

    # (action, in_place, is_local)
    return (action, False)


def make_default_class():
    """ClassDef(identifier name,
             expr* bases,
             keyword* keywords,
             stmt* body,
             expr* decorator_list)"""

    return ast.ClassDef(
                name = "NewClass",
                bases = [],
                keywords = [],
                body = [make_default_statement()],
                decorator_list = [],
            )


def make_default_function():
    """FunctionDef(identifier name, arguments args,
                       stmt* body, expr* decorator_list, expr? returns,
                       string? type_comment)"""
    

    function_definition = ast.FunctionDef(
                name = "new_function",
                args = make_default_arguments(),
                body = [make_default_statement()],
                decorator_list = [],
                returns = None,
                type_comment = None
            )

    
    return function_definition


def make_default_import():
    """Import(alias* names)"""

    return ast.Import(names=[make_default_alias()])


# TODO: Not have the else branch by default
def make_default_for():
    """For(expr target, expr iter, stmt* body, stmt* orelse, string? type_comment)"""
    
    return ast.For(
            target = make_default_expression(ctx=ast.Store()),
            iter =  make_default_expression(),
            body = [make_default_statement()],
            # TODO: Add a way of creating the orelse
            orelse = [],
            type_comment = None
        )


def make_default_while():
    """While(expr test, stmt* body, stmt* orelse)"""

    return ast.While(
        test = make_default_expression(),
        body = [make_default_statement()],
        orelse = []
    )


def make_default_return():
    return ast.Return(value=make_default_expression())


def make_default_assign():
    """Assign(expr* targets, expr value, string? type_comment)j"""

    return ast.Assign(
            targets=[ast.Name(id="x", ctx=ast.Store())],
            value = make_default_expression(),
            type_comment = None
            )


def make_default_if():
    """If(expr test, stmt* body, stmt* orelse)"""

    return ast.If(
            test=make_default_expression(),
            body = [make_default_statement()],
            orelse = []
            )


def make_default_delete():
    """Delete(expr* targets)"""
    
    return ast.Delete(
                targets=[ast.Name(id="var", ctx=ast.Del())]
            )

def make_default_with():
    """With(withitem* items, stmt* body, string? type_comment)"""
    """withitem = (expr context_expr, expr? optional_vars)"""
    
    return ast.With(
            items = [
                ast.withitem(
                    context_expr=ast.Name(
                        id="context_manager",
                        ctx=ast.Load()
                    ),
                    optional_vars=ast.Name(
                        id="f",
                        ctx=ast.Store()
                    )

                )
            ],

            body = [make_default_statement()],
            type_comment = None,
        )


def make_default_raise():
    """Raise(expr? exc, expr? cause)"""

    return ast.Raise(
                exc=ast.Name(id="exception", ctx=ast.Load()),
                # Causes aren't that common so let's not include them
                # in the default raise
                cause=None # ast.Name(id="cause", ctx=ast.Load())
            )


def make_default_attribute(cursor_trail, tree):
    """Attribute(expr value, identifier attr, expr_context ctx)"""
    selected_expr = core_logic.get_node_at_cursor(cursor_trail, tree)

    # Get the context from the node that was already here
    ctx = getattr(selected_expr, "ctx", ast.Load())

    generated_attribute = ast.Attribute(
            value=selected_expr, 
            attr="attr",
            ctx=ctx
            )

    # Set it's new context
    # The funcion returns the class, so make an instance of it
    recursively_fix_context(get_context_for_child, selected_expr)

    return generated_attribute


def make_default_call(cursor_trail, tree):
    """Call(expr func, expr* args, keyword* keywords)"""

    expr = core_logic.get_node_at_cursor(cursor_trail, tree)
    expr = expr if isinstance(expr, ast.expr) else ast.Name(id="f", ctx=ast.Load())

    return ast.Call(
            func=expr,
            args=[],
            keywords=[],
            )


# TODO: Have the left side default to the selected expression
def make_default_bin_op(left=None, right=None):
    if left is None:
        left = ast.Name(id="x", ctx=ast.Load())

    if right is None:
        right = ast.Name(id="y", ctx=ast.Load())

    """BinOp(expr left, operator op, expr right)"""
    return ast.BinOp(
            left=left,
            op=ast.Add(),
            right=right
            )


def make_default_lambda():
    """Lambda(arguments args, expr body)"""

    return ast.Lambda(
            args=make_default_arguments(),
            body=make_default_expression()
            )


def make_default_if_expression():
    """IfExp(expr test, expr body, expr orelse)"""

    return ast.IfExp(
            test=make_default_expression(),
            body=make_default_expression(),
            orelse=make_default_expression()
            )


def make_default_named_expression(cursor_trail, tree):
    """NamedExpr(expr target, expr value)"""
    
    selected_expr = core_logic.get_node_at_cursor(cursor_trail, tree)
    selected_expr = selected_expr if isinstance(selected_expr, ast.expr) else make_default_expression()

    return ast.NamedExpr(
            target=ast.Name(id="x", ctx=ast.Store()),
            value=selected_expr
            )


def make_default_expression(ctx=None):
    if ctx is None:
        ctx = ast.Load()

    return ast.Name(id="None", ctx=ctx)


def make_default_statement():
    return ast.Pass()


def make_default_arg():
    """arg = (identifier arg, expr? annotation, string? type_comment)"""
    return ast.arg(arg="x", annotation=None, type_comment=None)


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


def make_async(cursor_trail, tree):

    definition = core_logic.get_node_at_cursor(cursor_trail, tree)

    if type(definition) == ast.FunctionDef:
        return ast.AsyncFunctionDef(
                name = definition.name,
                args = definition.args,
                body = definition.body,
                decorator_list = definition.decorator_list,
                returns =  definition.returns,
                type_comment = definition.type_comment
            )

    if type(definition) == ast.AsyncFunctionDef:
        return ast.FunctionDef(
                name = definition.name,
                args = definition.args,
                body = definition.body,
                decorator_list = definition.decorator_list,
                returns =  definition.returns,
                type_comment = definition.type_comment
            )

    if type(definition) == ast.With:
        return ast.AsyncWith(
                items = definition.items,
                body = definition.body,
                type_comment = definition.type_comment
            )

    if type(definition) == ast.AsyncWith:
        return ast.With(
                items = definition.items,
                body = definition.body,
                type_comment = definition.type_comment
            )


def make_defaul_try():
    """Try(stmt* body, excepthandler* handlers, stmt* orelse, stmt* finalbody)"""
    
    return ast.Try(
            body=[ast.Pass()],
            handlers=[make_default_exception_handler()],
            # The else and the finally are not that common
            # let's not include them by default
            orelse=[],
            # orelse=[ast.Pass()],
            finalbody=[],
            # finalbody=[ast.Pass()],
            )


def make_default_exception_handler():
    """excepthandler = ExceptHandler(expr? type, identifier? name, stmt* body)"""

    # The ast module has it capitalized for some reason
    return ast.ExceptHandler(
            type = ast.Name("Exception", ctx=ast.Load()),
            name="e",
            body=[ast.Pass()],
            )


def make_default_assert():
    """Assert(expr test, expr? msg)"""

    return ast.Assert(test=ast.Name(id="test", ctx=ast.Load()), msg=None)

    
def make_default_global():
    """Global(identifier* names)"""

    return ast.Global(names=["global_var"])


def make_default_pass():
    return ast.Pass()



def make_default_break():
    return ast.Break()



def make_default_continue():
    return ast.Continue()


def make_default_tuple(cursor_trail, tree):
    """Tuple(expr* elts, expr_context ctx)"""

    selected_expr = core_logic.get_node_at_cursor(cursor_trail, tree)
    parent = core_logic.get_node_at_cursor(cursor_trail[:-1], tree)

    # Steal the ctx from the node that was already here
    # Default to Load
    ctx = getattr(selected_expr, "ctx", ast.Load())

    created_tuple = ast.Tuple(elts=[selected_expr], ctx=ctx) 

    recursively_fix_context(created_tuple, selected_expr)

    return created_tuple


def make_default_list(cursor_trail, tree):
    """List(expr* elts, expr_context ctx)"""
    selected_expr = core_logic.get_node_at_cursor(cursor_trail, tree)
    parent = core_logic.get_node_at_cursor(cursor_trail[:-1], tree)

    # Steal the ctx from the node that was already here
    # Default to Load
    ctx = getattr(selected_expr, "ctx", ast.Load())

    created_list = ast.List(elts=[selected_expr], ctx=ctx) 
    # Fix the contexts
    recursively_fix_context(created_list, selected_expr)

    return created_list


def recursively_fix_context(parent, node):
    # Fix the node's ctx
    node.ctx = get_context_for_child(parent, node)()

    # Fix the node's children's ctx
    for child in core_logic.list_children(node):
        if hasattr(child, "ctx"):
            recursively_fix_context(node, child)


def make_default_name(cursor_trail, tree):
    """Name(identifier id, expr_context ctx).
    This function must be dependent because of the context
    """

    selected_expr = core_logic.get_node_at_cursor(cursor_trail, tree)
    ctx = getattr(selected_expr, "ctx", ast.Load())

    return ast.Name(id="x", ctx=ctx)


def get_context_for_child(parent, child):
    parent_ctx = getattr(parent, "ctx", None)
    if isinstance(parent_ctx, ast.Load):
        return ast.Load

    if parent_ctx is None:
        # TODO: Named Expressions too i think
        print("parent is none")
        if isinstance(parent, ast.Assign) and core_logic.get_field_name_for_child(parent, child) == "targets":
            return ast.Store
        else:
            return ast.Load

    if isinstance(parent, ast.Attribute): return ast.Load
    if isinstance(parent, ast.Subscript): return ast.Load
    if isinstance(parent, ast.List): return type(parent_ctx)
    if isinstance(parent, ast.Tuple): return type(parent_ctx)
    if isinstance(parent, ast.Starred): return type(parent_ctx)

    # Unknown context otherwise
    # (Just return None)


def make_default_string(get_user_input):
    string = get_user_input("str: ")
    return ast.Constant(value=string, kind=None)


# Those actions return different nodes depending on the context
dependent_actions = ["async", "list", "call", "attribute", "named_expression", "tuple", "name"]

# Those actions need user input
user_input_actions = ["string"]

nodes = {
    # "name" : (validator, creator)
    "class": (v.is_instance_of(ast.stmt), make_default_class),
    "function": (v.is_instance_of(ast.stmt), make_default_function),
    "import": (v.is_instance_of(ast.stmt), make_default_import),
    "if": (v.is_instance_of(ast.stmt), make_default_if),
    "for": (v.is_instance_of(ast.stmt), make_default_for),
    "while": (v.is_instance_of(ast.stmt), make_default_while),
    "return": (v.validate_both(
                v.is_instance_of(ast.stmt),
                v.validate_one_of(
                    v.is_within(ast.FunctionDef),
                    v.is_within(ast.AsyncFunctionDef)
                )
            ), make_default_return),
    "assign": (v.is_instance_of(ast.stmt), make_default_assign),
    "delete": (v.is_instance_of(ast.stmt), make_default_delete),
    "with": (v.is_instance_of(ast.stmt), make_default_with),
    "raise": (v.validate_both(
                v.is_instance_of(ast.stmt),
                v.validate_one_of(
                    v.is_within(ast.FunctionDef),
                    v.is_within(ast.AsyncFunctionDef)
                ),
            ), make_default_raise),
    "call": (v.validate_one_of(
                v.is_instance_of(ast.stmt),
                v.is_simple_expression,
        ), make_default_call),
    "async": (v.validate_one_of(
                v.is_instance_of(ast.FunctionDef),
                v.is_instance_of(ast.AsyncFunctionDef),
                v.is_instance_of(ast.AsyncWith),
                v.validate_both(
                    v.is_within(ast.AsyncFunctionDef),
                    v.is_instance_of(ast.With)
                )
             ), make_async),
    "try": (v.is_instance_of(ast.stmt), make_defaul_try),
    "assert": (v.is_instance_of(ast.stmt), make_default_assert),
    "global": (v.is_instance_of(ast.stmt), make_default_global),
    "pass": (v.is_instance_of(ast.stmt), make_default_pass),
    "break": (v.validate_both(
                v.is_instance_of(ast.stmt),
                v.is_in_loop(),
            ), make_default_break),
    "continue":(v.validate_both(
                v.is_instance_of(ast.stmt),
                v.is_in_loop(),
            ), make_default_continue),
    "list": (v.is_instance_of(ast.expr), make_default_list),
    "attribute": (v.is_instance_of(ast.expr), make_default_attribute),
    "bin_op": (v.is_simple_expression, make_default_bin_op),
    "string": (v.is_simple_expression, make_default_string),
    "lambda": (v.is_simple_expression, make_default_lambda),
    "if_exp": (v.is_simple_expression, make_default_if_expression),
    "named_expression": (v.is_simple_expression, make_default_named_expression),
    "tuple": (v.is_instance_of(ast.expr), make_default_tuple),
    "name": (v.is_instance_of(ast.expr), make_default_name),
 }

