import astor
import ast


def render_view(ast, current_node):
    """Shows the ast with the current_node selected. This renderer
    can be altered according to the user's preferences about how
    the code should look like (Like indentation, casing, etc),
    because those are not properties of the code, just of the render.
    Doesn' need to return valid python code, just readable code."""

    # TODO: Add a way of letting the user specify the renderer
    generator_class = cursor_highlighter_of(current_node)
    return astor.to_source(
            ast,
            source_generator_class=generator_class
            )


def render_standard(ast):
    """Render the ast in the most standard python. Should not be 
    altered by the user."""
    return astor.to_source(ast)


def cursor_highlighter_of(ast_node):

    # TODO: Find out why docstrings, when selected, become single quoted
    # TODO: The f strings look weird
    class CursorHighlighter(astor.SourceGenerator):
        
        cursor_start = "<<<"
        cursor_end = ">>>"

        def __init__(self, indent_with, add_line_information=False,
                     pretty_string=astor.code_gen.pretty_string,
                     # constants
                     len=len, isinstance=isinstance, callable=callable):

            super().__init__(indent_with,
                    add_line_information,
                    pretty_string,
                    len,
                    isinstance,
                    callable)

            # Flag to track the appending of the selected node
            # Important to place the start of the cursor in the correct position
            self.is_selected_node = False

            method_to_overwrite = 'visit_' + ast_node.__class__.__name__
            self.old_method = getattr(self, method_to_overwrite)

            setattr(self, method_to_overwrite, self.visit_the_specific_node)
            
            # Overwrite the write method
            old_write = self.write
            visit = self.visit
            result = self.result
            append = self.result.append

            def new_write(*params):
                append_after_the_lines = False

                for item in params:
                    if isinstance(item, ast.AST):
                        visit(item)
                    elif callable(item):
                        item()
                    else:

                        if self.is_selected_node:
                            append_after_the_lines = True
                            # Never forget to unset the flag
                            self.is_selected_node = False

                        if self.new_lines:
                            append('\n' * self.new_lines)

                            self.colinfo = len(result), 0
                            append(self.indent_with * self.indentation)
                            self.new_lines = 0

                            if append_after_the_lines:
                                append_after_the_lines = False
                                append(self.cursor_start) 
                        elif append_after_the_lines:
                            # If there are no lines, just append regularly
                            append(self.cursor_start)

                        if item:
                            append(item)

            self.write = new_write

        def visit_the_specific_node(self, node):
            # The node is already of the correct type
            # Check if it's the one we want

            if node == ast_node:
                # Set the flag that's read later when appending the selected node to the result buffer
                # (Is used to insert the starting cursor after newlines)
                self.is_selected_node = True

                # Render the node
                self.old_method(node)

                # Add the end of the cursor
                self.result.append(self.cursor_end)
            else:
                self.old_method(node)


    return CursorHighlighter

def is_all_newlines(string):
    is_newline = lambda x : x == "\n"
    return all(is_newline(x) for x in string) 

