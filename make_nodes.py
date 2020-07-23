import ast
import core_logic
import validators as v

# The python 3.8 abstract grammar can be found at:
# https://docs.python.org/3/library/ast.html#abstract-grammar

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


def make_class():
    """ClassDef(identifier name,
             expr* bases,
             keyword* keywords,
             stmt* body,
             expr* decorator_list)"""

    return ast.ClassDef(
                name = "NewClass",
                bases = [],
                keywords = [],
                body = [make_statement()],
                decorator_list = [],
            )


def make_function():
    """FunctionDef(identifier name, arguments args,
                       stmt* body, expr* decorator_list, expr? returns,
                       string? type_comment)"""
    

    function_definition = ast.FunctionDef(
                name = "new_function",
                args = make_arguments(),
                body = [make_statement()],
                decorator_list = [],
                returns = None,
                type_comment = None
            )

    
    return function_definition


def make_import():
    """Import(alias* names)"""

    return ast.Import(names=[make_alias()])


# TODO: Not have the else branch by default
def make_for():
    """For(expr target, expr iter, stmt* body, stmt* orelse, string? type_comment)"""
    
    return ast.For(
            target = make_expression(ctx=ast.Store()),
            iter =  make_expression(),
            body = [make_statement()],
            # TODO: Add a way of creating the orelse
            orelse = [],
            type_comment = None
        )


def make_while():
    """While(expr test, stmt* body, stmt* orelse)"""

    return ast.While(
        test = make_expression(),
        body = [make_statement()],
        orelse = []
    )


def make_return():
    return ast.Return(value=make_expression())


def make_assign():
    """Assign(expr* targets, expr value, string? type_comment)j"""

    return ast.Assign(
            targets=[ast.Name(id="x", ctx=ast.Store())],
            value = make_expression(),
            type_comment = None
            )


def make_if():
    """If(expr test, stmt* body, stmt* orelse)"""

    return ast.If(
            test=make_expression(),
            body = [make_statement()],
            orelse = []
            )


def make_delete():
    """Delete(expr* targets)"""
    
    return ast.Delete(
                targets=[ast.Name(id="var", ctx=ast.Del())]
            )

def make_with():
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

            body = [make_statement()],
            type_comment = None,
        )


def make_raise():
    """Raise(expr? exc, expr? cause)"""

    return ast.Raise(
                exc=ast.Name(id="exception", ctx=ast.Load()),
                # Causes aren't that common so let's not include them
                # in the default raise
                cause=None # ast.Name(id="cause", ctx=ast.Load())
            )


def make_attribute(cursor_trail, tree):
    """Attribute(expr value, identifier attr, expr_context ctx)"""
    selected_expr = core_logic.get_node_at_cursor(cursor_trail, tree)

    # In the case the parent is an annotated assignment,
    # It must'nt have the "simple" tag
    # TODO: Other annotatable and assignable expressions might need this too
    parent = core_logic.get_node_at_cursor(cursor_trail[:-1], tree)
    if isinstance(parent, ast.AnnAssign):
        # TODO: Can we use False? (The grammar says int)
        parent.simple = 0

    # Get the context from the node that was already here
    ctx = getattr(selected_expr, "ctx", ast.Load())

    # Make sure it's of the expr type (an not a statement)
    selected_expr = selected_expr if isinstance(selected_expr, ast.expr) else None

    generated_attribute = ast.Attribute(
            value=selected_expr if selected_expr is not None else make_expression(), 
            attr="attr",
            ctx=ctx
            )

    # Set it's new context if the child was an expression
    if selected_expr is not None:
        recursively_fix_context(generated_attribute, selected_expr)

    return generated_attribute


def make_call(cursor_trail, tree):
    """Call(expr func, expr* args, keyword* keywords)"""

    expr = core_logic.get_node_at_cursor(cursor_trail, tree)
    expr = expr if isinstance(expr, ast.expr) else ast.Name(id="f", ctx=ast.Load())

    return ast.Call(
            func=expr,
            args=[make_expression()],
            keywords=[],
            )

def make_call_on(cursor_trail, tree):
    """Calls a function on the selected expression"""

    expr = core_logic.get_node_at_cursor(cursor_trail, tree)
    expr = expr if isinstance(expr, ast.expr) else make_expression()

    return ast.Call(
            func = ast.Name(id="f", ctx=ast.Load()),
            args = [expr],
            keywords=[]
            )
    

# TODO: Have the left side default to the selected expression
def make_bin_op(left=None, right=None):
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


def make_lambda():
    """Lambda(arguments args, expr body)"""

    return ast.Lambda(
            args=make_arguments(),
            body=make_expression()
            )


def make_if_expression():
    """IfExp(expr test, expr body, expr orelse)"""

    return ast.IfExp(
            test=make_expression(),
            body=make_expression(),
            orelse=make_expression()
            )


def make_named_expression(cursor_trail, tree):
    """NamedExpr(expr target, expr value)"""
    
    selected_expr = core_logic.get_node_at_cursor(cursor_trail, tree)
    selected_expr = selected_expr if isinstance(selected_expr, ast.expr) else make_expression()

    return ast.NamedExpr(
            target=ast.Name(id="x", ctx=ast.Store()),
            value=selected_expr
            )


def make_expression(ctx=None):
    if ctx is None:
        ctx = ast.Load()

    return ast.Name(id="n", ctx=ctx)


def make_statement():
    return ast.Pass()


def make_arg():
    """arg = (identifier arg, expr? annotation, string? type_comment)"""
    return ast.arg(arg="x", annotation=None, type_comment=None)


def make_arguments():
    return ast.arguments(
            posonlyargs=[],
            args=[],
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[]
        )


def make_alias(default_name="module", default_asname=None):
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

    if isinstance(definition, ast.comprehension):
        # Toggle the async
        definition.is_async = 0 if definition.is_async == 1 else 1
        return definition


def make_try():
    """Try(stmt* body, excepthandler* handlers, stmt* orelse, stmt* finalbody)"""
    
    return ast.Try(
            body=[ast.Pass()],
            handlers=[make_exception_handler()],
            # The else and the finally are not that common
            # let's not include them by default
            orelse=[],
            # orelse=[ast.Pass()],
            finalbody=[],
            # finalbody=[ast.Pass()],
            )


def make_exception_handler():
    """excepthandler = ExceptHandler(expr? type, identifier? name, stmt* body)"""

    # The ast module has it capitalized for some reason
    return ast.ExceptHandler(
            type = ast.Name("Exception", ctx=ast.Load()),
            name="e",
            body=[ast.Pass()],
            )


def make_assert():
    """Assert(expr test, expr? msg)"""

    return ast.Assert(test=ast.Name(id="test", ctx=ast.Load()), msg=None)

    
def make_global():
    """Global(identifier* names)"""

    return ast.Global(names=["global_var"])


def make_pass():
    return ast.Pass()


def make_break():
    return ast.Break()


def make_continue():
    return ast.Continue()


def make_tuple(cursor_trail, tree):
    """Tuple(expr* elts, expr_context ctx)"""

    selected_expr = core_logic.get_node_at_cursor(cursor_trail, tree)
    parent = core_logic.get_node_at_cursor(cursor_trail[:-1], tree)

    # Steal the ctx from the node that was already here
    # Default to Load
    ctx = getattr(selected_expr, "ctx", ast.Load())

    selected_expr = selected_expr if isinstance(selected_expr, ast.expr) else None
    elts = [] if selected_expr is None else [selected_expr]

    created_tuple = ast.Tuple(elts=elts, ctx=ctx) 

    if selected_expr is not None: 
        recursively_fix_context(created_tuple, selected_expr)

    return created_tuple


def make_list(cursor_trail, tree):
    """List(expr* elts, expr_context ctx)"""
    selected_expr = core_logic.get_node_at_cursor(cursor_trail, tree)

    # Steal the ctx from the node that was already here
    # Default to Load
    ctx = getattr(selected_expr, "ctx", ast.Load())

    selected_expr = selected_expr if isinstance(selected_expr, ast.expr) else None
    elts = [] if selected_expr is None else [selected_expr]
    created_list = ast.List(elts=elts, ctx=ctx) 

    # If we have children, fix their contexts
    if selected_expr is not None:
        recursively_fix_context(created_list, selected_expr)

    return created_list


def make_subscript(cursor_trail, tree):
    """Subscript(expr value, slice slice, expr_context ctx)"""

    selected_expr = core_logic.get_node_at_cursor(cursor_trail, tree)

    # Steal the ctx from the node that was already here
    # Default to Load
    ctx = getattr(selected_expr, "ctx", ast.Load())
    selected_expr = selected_expr if isinstance(selected_expr, ast.expr) else make_expression()

    subscript = ast.Subscript(value=selected_expr, slice=make_slice(), ctx=ctx)
    recursively_fix_context(subscript, selected_expr)

    return subscript


def make_slice():
    """slice = Slice(expr? lower, expr? upper, expr? step)
          | ExtSlice(slice* dims)
          | Index(expr value)
    """

    return ast.Index(value=ast.Constant(value=0))


def recursively_fix_context(parent, node):
    # Fix the node's ctx
    node.ctx = get_context_for_child(parent, node)()

    # Fix the node's children's ctx
    for child in core_logic.list_children(node):
        if hasattr(child, "ctx"):
            recursively_fix_context(node, child)


def make_name(cursor_trail, tree):
    """Name(identifier id, expr_context ctx).
    This function must be dependent because of the context
    """

    selected_expr = core_logic.get_node_at_cursor(cursor_trail, tree)
    ctx = getattr(selected_expr, "ctx", ast.Load())

    return ast.Name(id="x", ctx=ctx)


# TODO: Move this to core_logic
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


def make_string(get_user_input):
    string = get_user_input("str: ")
    return ast.Constant(value=string, kind=None)


def make_not(cursor_trail, tree):
    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)
    expr = selected_node if isinstance(selected_node, ast.expr) else make_expression()

    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        # Having not not x doesn't really make sense
        # So let's just remove the not in this case
        return expr.operand
 
    return ast.UnaryOp(op=ast.Not(), operand=expr)
        

def make_invert(cursor_trail, tree):
    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)
    expr = selected_node if isinstance(selected_node, ast.expr) else make_expression()

    return ast.UnaryOp(op=ast.Invert(), operand=expr)


def make_usub(cursor_trail, tree):
    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)
    expr = selected_node if isinstance(selected_node, ast.expr) else make_expression()

    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.USub):
        # Having - - x doesn't really make sense
        # So let's just remove the minus in this case
        return expr.operand
 
    return ast.UnaryOp(op=ast.USub(), operand=expr)


def make_dict(cursor_trail, tree):
    """Dict(expr* keys, expr* values)
    """
    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)
    expr = selected_node if isinstance(selected_node, ast.expr) else make_expression()

    return ast.Dict(keys=[ast.Name(id="key", ctx=ast.Load())], values=[expr])


def make_set(cursor_trail, tree):
    """Set(expr* elts)
    """

    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)
    expr = selected_node if isinstance(selected_node, ast.expr) else make_expression()

    return ast.Set(elts=[expr])


def make_generator(cursor_trail, tree):
    """ Makes a generator of the selected_expression 
    
    ListComp(expr elt, comprehension* generators)
    SetComp(expr elt, comprehension* generators)
    DictComp(expr key, expr value, comprehension* generators)
    GeneratorExp(expr elt, comprehension* generators)
    """

    selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)
    if isinstance(selected_node, ast.List):
        comprehension = ast.ListComp

        try:
            elt = selected_node.elts[0]
        except IndexError:
            elt = make_expression()

        elts = {"elt": elt} 

    elif isinstance(selected_node, ast.Set):
        comprehension = ast.SetComp

        try:
            elt = selected_node.elts[0]
        except IndexError:
            elt = make_expression()

        elts = {"elt": elt} 

    elif isinstance(selected_node, ast.Dict):
        comprehension = ast.DictComp

        try:
            key = selected_node.keys[0]
            value = selected_node.values[0]
        except IndexError:
            key = make_expression()
            value = make_expression()

        elts = {"key": key, 
                "value": value
                }
    else:
        comprehension = ast.GeneratorExp
        expr = selected_node if isinstance(selected_node, ast.expr) else make_expression()

        elts = {"elt": expr}


    return comprehension(**elts, generators=[make_comprehension()])


def make_comprehension():
    """comprehension = (expr target, expr iter, expr* ifs, int is_async)"""

    return ast.comprehension(
            target=make_expression(ctx=ast.Store()),
            iter=ast.Name(id="iterable", ctx=ast.Load()),
            ifs=[],
            is_async=0,
            )
    

def make_await():
    """Await(expr value)"""

    # TODO: Use the selected expression if possible
    return ast.Await(value=make_expression())


def make_yield():
    """Yield(expr? value)"""

    return ast.Yield(value=make_expression())


def make_yield_from():
    """YieldFrom(expr value)"""

    return ast.YieldFrom(value=make_expression())


# Those actions return different nodes depending on the context
dependent_actions = ["async", "list", "call", "attribute", "named_expression",
                    "tuple", "name", "not", "usub", "invert", "dict", "set",
                    "generator", "subscript", "call_on"]

# Those actions need user input
user_input_actions = ["string"]
 
nodes = {
    # "name" : (validator, creator)
    "class": (v.is_instance_of(ast.stmt), make_class),
    "function": (v.is_instance_of(ast.stmt), make_function),
    "import": (v.is_instance_of(ast.stmt), make_import),
    "if": (v.is_instance_of(ast.stmt), make_if),
    "for": (v.is_instance_of(ast.stmt), make_for),
    "while": (v.is_instance_of(ast.stmt), make_while),
    "return": (v.validate_both(
                v.is_instance_of(ast.stmt),
                v.validate_one_of(
                    v.is_within(ast.FunctionDef),
                    v.is_within(ast.AsyncFunctionDef)
                )
            ), make_return),
    "assign": (v.is_instance_of(ast.stmt), make_assign),
    "delete": (v.is_instance_of(ast.stmt), make_delete),
    "with": (v.is_instance_of(ast.stmt), make_with),
    "raise": (v.validate_both(
                v.is_instance_of(ast.stmt),
                v.validate_one_of(
                    v.is_within(ast.FunctionDef),
                    v.is_within(ast.AsyncFunctionDef)
                ),
            ), make_raise),
    "call": (v.is_simple_expression, make_call),
    "call_on" : (v.is_simple_expression, make_call_on),
    "async": (v.validate_one_of(
                v.is_instance_of(ast.FunctionDef),
                v.is_instance_of(ast.AsyncFunctionDef),
                v.is_instance_of(ast.AsyncWith),
                v.is_instance_of(ast.comprehension),
                v.validate_both(
                    v.is_within(ast.AsyncFunctionDef),
                    v.is_instance_of(ast.With)
                )
             ), make_async),
    "try": (v.is_instance_of(ast.stmt), make_try),
    "assert": (v.is_instance_of(ast.stmt), make_assert),
    "global": (v.is_instance_of(ast.stmt), make_global),
    "pass": (v.is_instance_of(ast.stmt), make_pass),
    "break": (v.validate_both(
                v.is_instance_of(ast.stmt),
                v.is_in_loop(),
            ), make_break),
    "continue":(v.validate_both(
                v.is_instance_of(ast.stmt),
                v.is_in_loop(),
            ), make_continue),
    "list": (v.is_non_annotatable_assignable_expression, make_list),
    "attribute": (v.is_assignable_expression, make_attribute),
    "bin_op": (v.is_simple_expression, make_bin_op),
    "string": (v.is_simple_expression, make_string),
    "lambda": (v.is_simple_expression, make_lambda),
    "if_exp": (v.is_simple_expression, make_if_expression),
    "named_expression": (v.is_simple_expression, make_named_expression),
    "tuple": (v.is_non_annotatable_assignable_expression, make_tuple),
    "name": (v.is_assignable_expression, make_name),
    "not": (v.is_simple_expression, make_not),
    "invert": (v.is_simple_expression, make_invert),
    "usub": (v.is_simple_expression, make_usub),
    "dict": (v.is_simple_expression, make_dict),
    "set": (v.is_simple_expression, make_set),
    "generator": (v.is_simple_expression, make_generator),
    "await": (v.validate_all_of(
                v.is_simple_expression,
                v.is_within(ast.AsyncFunctionDef),
             ), make_await),
    "yield": (v.simple_expression_within_function, make_yield),
    "yield_from": (v.simple_expression_within_function, make_yield_from),
    # TODO: Abstract the common logic of all the assignable expressions
    "subscript": (v.is_assignable_expression, make_subscript),
 }

