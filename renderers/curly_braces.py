import astor
import ast
from .standard import cursor_highlighter_of


def render_view(tree, node):

    generator_class = curly_braces_python_of(tree)
    return astor.to_source(
            tree,
            #pretty_source= lambda x: "".join(x),
            source_generator_class=curly_braces_python_of(node)
            )


def curly_braces_python_of(node):

    from astor.code_gen import set_precedence 

    class CurlyBracesPython(cursor_highlighter_of(node)):
        def visit_For(self, node, is_async=False):
            set_precedence(node, node.target)
            prefix = 'async ' if is_async else ''
            self.statement(node, '%sfor ' % prefix,
                           node.target, ' in ', node.iter, '{')
            self.body_or_else(node) 
            self.newline()
            self.write("}")

        def visit_ClassDef(self, node):
                have_args = []

                def paren_or_comma():
                    if have_args:
                        self.write(', ')
                    else:
                        have_args.append(True)
                        self.write('(')

                self.decorators(node, 2)
                self.statement(node, 'class %s' % node.name)
                for base in node.bases:
                    self.write(paren_or_comma, base)
                # keywords not available in early version
                for keyword in self.get_keywords(node):
                    self.write(paren_or_comma, keyword.arg or '',
                               '=' if keyword.arg else '**', keyword.value)
                self.conditional_write(paren_or_comma, '*', self.get_starargs(node))
                self.conditional_write(paren_or_comma, '**', self.get_kwargs(node))
                self.write(have_args and '){' or '{')
                self.body(node.body)
                self.newline()
                self.write("}")
                if not self.indentation:
                    self.newline(extra=2)

        def visit_FunctionDef(self, node, is_async=False):
            prefix = 'async ' if is_async else ''
            self.decorators(node, 1 if self.indentation else 2)
            self.statement(node, '%sdef %s' % (prefix, node.name), '(')
            self.visit_arguments(node.args)
            self.write(')')
            self.conditional_write(' -> ', self.get_returns(node))
            self.write('{')
            self.body(node.body)
            self.newline()
            self.write("}")
            if not self.indentation:
                self.newline(extra=2)

        def visit_If(self, node):
            set_precedence(node, node.test)
            self.statement(node, 'if ', node.test, ':')
            self.body(node.body)
            while True:
                else_ = node.orelse
                if len(else_) == 1 and isinstance(else_[0], ast.If):
                    node = else_[0]
                    set_precedence(node, node.test)
                    self.write(self.newline, 'elif ', node.test, '{')
                    self.body(node.body)
                else:
                    self.else_body(else_)
                    break
        

        def visit_While(self, node):
            set_precedence(node, node.test)
            self.statement(node, 'while ', node.test, '{')
            self.body_or_else(node)
            self.newline()
            self.write("}")

        def visit_With(self, node, is_async=False):
            prefix = 'async ' if is_async else ''
            self.statement(node, '%swith ' % prefix)
            if hasattr(node, "context_expr"):  # Python < 3.3
                self.visit_withitem(node)
            else:                              # Python >= 3.3
                self.comma_list(node.items)
            self.write('{')
            self.body(node.body)
            self.newline()
            self.write("}")

        def visit_ExceptHandler(self, node):
            self.statement(node, 'except')
            if self.conditional_write(' ', node.type):
                self.conditional_write(' as ', node.name)
            self.write('{')
            self.body(node.body)
            self.newline()
            self.write("}")

    return CurlyBracesPython
