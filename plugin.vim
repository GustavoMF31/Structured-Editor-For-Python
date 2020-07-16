if !has('python3')
  echo 'Error: Requires vim compiled with +python3'
  finish
endif

" The path of the main python file
let g:path = fnamemodify(resolve(expand('<sfile>:p')), ':h') . '/main.py'
" echo g:path

execute 'py3file ' . g:path


command! -buffer -nargs=0 CursorDown exec 'py3 act("cursor_down")'
command! -buffer -nargs=0 CursorUp exec 'py3 act("cursor_up")'
command! -buffer -nargs=0 CursorLeft exec 'py3 act("cursor_left")'
command! -buffer -nargs=0 CursorRight exec 'py3 act("cursor_right")'
command! -buffer -nargs=0 Save exec 'py3 save()'

" Actions
command! -buffer -nargs=0 Rename exec 'py3 act("rename")'
command! -buffer -nargs=0 MakeFunction exec 'py3 act("make_function")'
command! -buffer -nargs=0 MakeClass exec 'py3 act("make_class")'
command! -buffer -nargs=0 Append exec 'py3 act("append")'
command! -buffer -nargs=0 Insert exec 'py3 act("insert")'
command! -buffer -nargs=0 Delete exec 'py3 act("delete")'
command! -buffer -nargs=0 TypeAnnotation exec 'py3 act("type_annotation")'
command! -buffer -nargs=0 Add exec 'py3 act("add")'
command! -buffer -nargs=0 Subtract exec 'py3 act("subtract")'
command! -buffer -nargs=0 Multiply exec 'py3 act("multiply")'
command! -buffer -nargs=0 Divide exec 'py3 act("divide")'
command! -buffer -nargs=0 Mod exec 'py3 act("mod")'
command! -buffer -nargs=0 Pow exec 'py3 act("pow")'
command! -buffer -nargs=0 InsertInt exec 'py3 act("insert_int")'
command! -buffer -nargs=0 Equals exec 'py3 act("equals")'
command! -buffer -nargs=0 GreaterThan exec 'py3 act("greater_than")'
command! -buffer -nargs=0 GreaterThanEquals exec 'py3 act("greater_than_equals")'
command! -buffer -nargs=0 LessThan exec 'py3 act("less_than")'
command! -buffer -nargs=0 LessThanEquals exec 'py3 act("less_than_equals")'
command! -buffer -nargs=0 Is exec 'py3 act("is")'
command! -buffer -nargs=0 In exec 'py3 act("in")'
command! -buffer -nargs=0 And exec 'py3 act("and")'
command! -buffer -nargs=0 Or exec 'py3 act("or")'
command! -buffer -nargs=0 Extend exec 'py3 act("extend")'
command! -buffer -nargs=0 MakeInvert exec 'py3 act("make_invert")'
command! -buffer -nargs=0 MakeNot exec 'py3 act("make_not")'
command! -buffer -nargs=0 MakeUAdd exec 'py3 act("make_uadd")'
command! -buffer -nargs=0 MakeUSub exec 'py3 act("make_usub")'
command! -buffer -nargs=0 Import exec 'py3 act("make_import")'
command! -buffer -nargs=0 MakeFor exec 'py3 act("make_for")'
command! -buffer -nargs=0 MakeWhile exec 'py3 act("make_while")'
command! -buffer -nargs=0 MakeAsync exec 'py3 act("make_async")'
command! -buffer -nargs=0 MakeReturn exec 'py3 act("make_return")'
command! -buffer -nargs=0 MakeAssign exec 'py3 act("make_assign")'
command! -buffer -nargs=0 MakeIf exec 'py3 act("make_if")'
command! -buffer -nargs=0 MakeDelete exec 'py3 act("make_delete")'
command! -buffer -nargs=0 MakeWith exec 'py3 act("make_with")'
command! -buffer -nargs=0 MakeRaise exec 'py3 act("make_raise")'
command! -buffer -nargs=0 MakeCall exec 'py3 act("make_call")'
command! -buffer -nargs=0 MakeTry exec 'py3 act("make_try")'
command! -buffer -nargs=0 MakeAssert exec 'py3 act("make_assert")'
command! -buffer -nargs=0 MakeGlobal exec 'py3 act("make_global")'
command! -buffer -nargs=0 MakePass exec 'py3 act("make_pass")'
command! -buffer -nargs=0 MakeBreak exec 'py3 act("make_break")'
command! -buffer -nargs=0 MakeContinue exec 'py3 act("make_continue")'
command! -buffer -nargs=0 MakeList exec 'py3 act("make_list")'
command! -buffer -nargs=0 MakeAttribute exec 'py3 act("make_attribute")'
command! -buffer -nargs=0 MakeBinOp exec 'py3 act("make_bin_op")'
command! -buffer -nargs=0 MakeString exec 'py3 act("make_string")'
command! -buffer -nargs=0 MakeLambda exec 'py3 act("make_lambda")'
command! -buffer -nargs=0 MakeIfExp exec 'py3 act("make_if_exp")'
command! -buffer -nargs=0 MakeNamedExpression exec 'py3 act("make_named_expression")'
command! -buffer -nargs=0 MakeTuple exec 'py3 act("make_tuple")'
command! -buffer -nargs=0 MakeName exec 'py3 act("make_name")'

nnoremap <buffer> s :Save<Enter>
nnoremap <buffer> h :CursorLeft<Enter>
nnoremap <buffer> j :CursorDown<Enter>
nnoremap <buffer> k :CursorUp<Enter>
nnoremap <buffer> l :CursorRight<Enter>
nnoremap <buffer> t :TypeAnnotation<Enter>
nnoremap <buffer> e :Extend<Enter>
nnoremap <buffer> + :Add<Enter>
nnoremap <buffer> - :Subtract<Enter>
nnoremap <buffer> * :Multiply<Enter>
nnoremap <buffer> % :Mod<Enter>
nnoremap <buffer> / :Divide<Enter>
nnoremap <buffer> ^ :Pow<Enter>
nnoremap <buffer> = :Equals<Enter>
nnoremap <buffer> > :GreaterThan<Enter>
nnoremap <buffer> >= :GreaterThanEquals<Enter>
nnoremap <buffer> < :LessThan<Enter>
nnoremap <buffer> <= :LessThanEquals<Enter>
nnoremap <buffer> & :And<Enter>
nnoremap <buffer> <Bar> :Or<Enter>
nnoremap <buffer> ! :Not<Enter>
nnoremap <buffer> ~ :MakeInvert<Enter>
" TODO: Move the ++ and -- behavior to the + and - keys
nnoremap <buffer> ++ :MakeUAdd<Enter>
nnoremap <buffer> -- :MakeUSub<Enter>
" b stands for "be", (so it IS something)
nnoremap <buffer> cb :Is<Enter>
nnoremap <buffer> cn :In<Enter>

" TODO: Is this Actions comment in the right place?
" Actions
nnoremap <buffer> i :Insert<Enter>
nnoremap <buffer> r :Rename<Enter>
nnoremap <buffer> a :Append<Enter>
nnoremap <buffer> A :MakeAsync<Enter>
nnoremap <buffer> x :Delete<Enter>
nnoremap <buffer> ci :InsertInt<Enter>

" Node making actions
" v for statements
nnoremap <buffer> vf :MakeFunction<Enter>
nnoremap <buffer> vc :MakeClass<Enter>
nnoremap <buffer> vi :Import<Enter>
" couldn't think of anything for if (sad emoji), so 'h' it is
nnoremap <buffer> vh :MakeIf<Enter>
" vl means change loop (because vf is already taken by change function)
nnoremap <buffer> vl :MakeFor<Enter>
nnoremap <buffer> vw :MakeWhile<Enter>
nnoremap <buffer> vr :MakeReturn<Enter>
nnoremap <buffer> va :MakeAssign<Enter>
nnoremap <buffer> vd :MakeDelete<Enter>
nnoremap <buffer> vg :MakeWith<Enter>
" ve for change execption
nnoremap <buffer> ve :MakeRaise<Enter>
nnoremap <buffer> vt :MakeTry<Enter>
nnoremap <buffer> vq :MakeAssert<Enter>
" vs for change scope
nnoremap <buffer> vs :MakeGlobal<Enter>
nnoremap <buffer> vv :MakePass<Enter>
nnoremap <buffer> vb :MakeBreak<Enter>
nnoremap <buffer> vk :MakeContinue<Enter>
" c for expressions
nnoremap <buffer> cl :MakeList<Enter>
nnoremap <buffer> cc :MakeCall<Enter>
nnoremap <buffer> c. :MakeAttribute<Enter>
nnoremap <buffer> co :MakeBinOp<Enter>
nnoremap <buffer> cs :MakeString<Enter>
" f stands for function
nnoremap <buffer> cf :MakeLambda<Enter>
nnoremap <buffer> ch :MakeIfExp<Enter>
nnoremap <buffer> ca :MakeNamedExpression<Enter>
nnoremap <buffer> ct :MakeTuple<Enter>
" v stands for variable
nnoremap <buffer> cv :MakeName<Enter>
