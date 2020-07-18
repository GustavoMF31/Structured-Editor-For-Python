# Structured-Editor-For-Python
A Vim plugin for structured editing of python code

In a structured editor, the code is edited not by changing characters in a text file, but by semantic actions that modify the the Abstract Syntax Tree.
This leads to some very interesting possibilities for improvements in the programming experience, because the editor is completely aware of the structure of the code and can be much more helpful.
For the code to be seen, it is "rendered" to the selected buffer with regular python syntax. While this buffer is the only way the code is read, it is merely visual. After the plugin is loaded, the AST is the only source of truth and changing the characters does nothing.


The first obvious benefit is that it is impossible to create syntax errors. This comes directly from the fact that the AST represents the code much better than a regular text file.

Another insight is that, because the rendered code is never parsed, it doesn't need to follow the syntax! This can theoretically allow for crazy stuff, like curly braces python. As long as the programmer can choose the editing actions based on it, it works. (It would require writing a custom renderer though)

Currently this project is just a prototype and is pretty awfull to actually edit code with. I think there are a couple of valid expressions missing and the current set of actions is not really convenient.

# Commands
When loaded, this plugin completely "overrides" Vim's normal mode, replacing regular commands.

## Movement
The hjkl keys move the cursor, but based on the AST:

```
k goes up to the parent node
j goes down to the first child node
h goes to the previous sibling
l goes to the following sibling
```

## Editing actions
```
s saves the file (Because the file is saved by python, vim will still warn you about unsaved stuff)
i adds a child to the selected node (Like an element to an empty list)
r renames the selected node
a clones the selected node 
A makes the selected node async (Like async for and async with)
x deletes the selected node when possible (It won't work if you try to empty the body of a statement for example, because that would be a syntax error)
t adds a type annotation to the selected node
e "extends" the selected node (Usually adds an else statement)
+ - * % / ^ = >= < <= & | change the selected operation 
! makes a not
~ is the tilde operator (called invert)
-- makes the selected node negative (-x)
```

## Actions for creating nodes
Because the amount of constructs that python supports, the list of keybindings is unfortunately really big.
I actually haven't put a lot of thought into organizing them in a meaningfull way, so, opinions are welcomed.

Actions for statements start with v, and actions for expressions start with c 

```
vf makes a function
vc makes a class
vi makes an import
vh makes an input an if statement
vl makes a for
vw makes a while
vr makes a return
va makes an assignment
vd makes a del
vg makes a with statement
ve makes a raise
vt makes a try
vq makes an assert
vs makes a global
vv makes a pass
vb makes a break
vk makes a continue

cl makes a list
cc makes a function call
c. makes an attribute (Like var.x)
co makes an operation (like a + b)
cs inserts a string
cf makes a lambda 
ch makes an if expression
ca makes a names expression (a := b)
ct makes a tuple
cv makes a variable
cd makes a dictionary
cg makes a set
ci makes a dict, list, or set into the corresponding generator
cy makes a yield expression
```
