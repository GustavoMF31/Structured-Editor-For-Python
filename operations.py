import ast

import core_logic
import make_nodes


# TODO: Handle nested comparisons using the lists 
def to_operation(new_operation):
    def change_operation(cursor_trail, tree, _):
        selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)

        # Compare -> BinOp
        if isinstance(selected_node, ast.Compare):
            selected_node = make_nodes.make_bin_op(
                    left=selected_node.left,
                    right=selected_node.comparators[0],
                    )

            core_logic.set_node_at_cursor(cursor_trail, tree, selected_node)

        # BoolOp -> BinOp
        elif isinstance(selected_node, ast.BoolOp):
            selected_node = make_nodes.make_bin_op(
                    left=selected_node.values[0],
                    right=selected_node.values[1],
                    )

            core_logic.set_node_at_cursor(cursor_trail, tree, selected_node)

        # Has to already be a BinOp otherwise
        elif not isinstance(selected_node, ast.BinOp):
            print("Can't change operation of this node")
            return 

        # Set the operation to an instance of the supplied class
        selected_node.op = new_operation()

    # (function, is_local?)
    return (change_operation, False)


def to_comparison(new_comparison):
    def change_comparison(cursor_trail, tree, _):
        selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)

        # BinOp -> Compare
        if isinstance(selected_node, ast.BinOp):
            selected_node = ast.Compare(
                    left=selected_node.left,
                    # The comparator will be set below
                    comparators=[selected_node.right]
                    )

            core_logic.set_node_at_cursor(cursor_trail, tree, selected_node)

        # BoolOp -> Compare
        elif isinstance(selected_node, ast.BoolOp):
            selected_node = ast.Compare(
                    left=selected_node.values[0],
                    # The comparator will be set below
                    comparators=[selected_node.values[1]]
                    )

            core_logic.set_node_at_cursor(cursor_trail, tree, selected_node)


        # Has to already be a Compare otherwise
        elif not isinstance(selected_node, ast.Compare):
            print("Can't change the comparison of this node")
            return

        # Set the operation to an instance of the supplied class
        selected_node.ops = [new_comparison()]

    return (change_comparison, False)


def to_bool_op(new_bool_op):
    def change_bool_op(cursor_trail, tree, _):
        selected_node = core_logic.get_node_at_cursor(cursor_trail, tree)

        # BinOp -> BoolOp
        if isinstance(selected_node, ast.BinOp):
            selected_node = ast.BoolOp(
                    # The operation will be set below
                    values = [selected_node.left, selected_node.right]
                    )

            core_logic.set_node_at_cursor(cursor_trail, tree, selected_node)

        # Compare -> BoolOp
        elif isinstance(selected_node, ast.Compare):
            selected_node = ast.BoolOp(
                    # The operation will be set below
                    values = [selected_node.left, selected_node.comparators[0]]
                    )

            core_logic.set_node_at_cursor(cursor_trail, tree, selected_node)
        
        # Has to already be a BoolOp otherwise
        elif not isinstance(selected_node, ast.BoolOp):
            print("Can't change the boolean operation of this node")
            return


        # Set the operation to an instance of the supplied class
        selected_node.op = new_bool_op()

    # The false means it's not a local action
    return (change_bool_op, False)

