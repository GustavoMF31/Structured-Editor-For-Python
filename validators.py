import ast

import core_logic


def is_instance_of(ast_node_type):
    def validate(cursor_trail, tree):
        selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)

        # make sure the node is allowed to be placed here
        return isinstance(selected_node, ast_node_type)

    return validate


# TODO: Move the validators into their own module
def is_not_instance_of(ast_node_type):
    def validate(cursor_trail, tree):
        selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)

        return not isinstance(selected_node, ast_node_type)

    return validate


def is_within(ast_node_type):
    def validate(cursor_trail, tree):

        return core_logic.core_is_within(cursor_trail, tree, ast_node_type)

    return validate


def is_within_field(ast_node_type, fieldname):
    def validate(cursor_trail, tree):

        return core_logic.core_is_within_field(cursor_trail, tree, ast_node_type, fieldname)

    return validate


def is_not_in_context(context):
    def validate(cursor_trail, tree):
        return core_logic.core_is_not_in_context(cursor_trail, tree, context)

    return validate


def is_in_context(context):
    def validate(cursor_trail, tree):
        return core_logic.core_is_in_context(cursor_trail, tree, context)

    return validate


def validate_both(first_validator, second_validator):
    """Make sure both validators pass"""

    def validate(cursor_trail, tree):
        return (first_validator(cursor_trail, tree)
                and second_validator(cursor_trail, tree))

    return validate


def validate_one_of(*validators):
    """Make sure at lest one of the validators passess"""

    def validate(cursor_trail, tree):
        for validator in validators:
            if validator(cursor_trail, tree):
                return True
            
        return False

    return validate


def validate_all_of(*list_of_validators):
    def validate(cursor_trail, tree):
        for validator in list_of_validators:
            if not validator(cursor_trail, tree):
                return False

        return True

    return validate


def validate_not(validator):
    """Negates the validator"""
    def negated(*args, **kwargs):
        return not validator(*args, **kwargs)

    return negated


def is_in_loop():
    # TODO: Maybe the async variants work too?
    return validate_one_of(
            is_within_field(ast.For, "body"),
            is_within_field(ast.While, "body")
            )

# Validates that it's a simple expression
# and that it's in a simple context (no assigning to it)
is_simple_expression = validate_all_of(
                            validate_one_of(
                                is_instance_of(ast.expr),
                                # Simple expressions are allowed as statements
                                # They will be wrapped in a Expr node
                                is_instance_of(ast.stmt)
                            ),
                            is_not_in_context(ast.Store),
                            is_not_in_context(ast.Param),
                            is_not_in_context(ast.Del),
                          )

# TODO: Replace all of the validate_both with validate_all
# For assignable expressions, any context goes
# and they can't be assign
is_assignable_expression = validate_one_of(
    is_instance_of(ast.expr),
    is_instance_of(ast.stmt),
)


# Those assignable expressions can't appear as targets of an annotated
# assignment
is_non_annotatable_assignable_expression = validate_all_of(
    is_assignable_expression,
    validate_not(
        is_within_field(ast.AnnAssign, "target"),
    ),
)


simple_expression_within_function = validate_all_of(
    is_simple_expression,
    validate_one_of(
        is_within(ast.FunctionDef),
        is_within(ast.AsyncFunctionDef)
    ),
 )
