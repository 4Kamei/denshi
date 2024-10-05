" hi def denshiLocal           ctermfg=209 guifg=#ff875f
" hi def denshiImported        ctermfg=214 guifg=#ffaf00 cterm=bold gui=bold
" hi def denshiParameter       ctermfg=75  guifg=#5fafff
" hi def denshiParameterUnused ctermfg=117 guifg=#87d7ff cterm=underline gui=underline
" hi def denshiFree            ctermfg=218 guifg=#ffafd7
" hi def denshiBuiltin         ctermfg=207 guifg=#ff5fff
" hi def denshiAttribute       ctermfg=49  guifg=#00ffaf
" hi def denshiSelf            ctermfg=249 guifg=#b2b2b2
" hi def denshiUnresolved      ctermfg=226 guifg=#ffff00 cterm=underline gui=underline
" hi def denshiSelected        ctermfg=231 guifg=#ffffff ctermbg=161 guibg=#d7005f

hi def denshiParameter      ctermfg=75  guifg=#5fafff cterm=underline gui=italic
hi def denshiKeyword        ctermfg=49  guifg=#00ffaf cterm=bold      gui=underline

hi def denshiErrorSign      ctermfg=231 guifg=#ffffff ctermbg=160 guibg=#d70000
hi def denshiErrorChar      ctermfg=231 guifg=#ffffff ctermbg=160 guibg=#d70000
sign define denshiError text=E> texthl=denshiErrorSign


" These options can't be initialized in the Python plugin since they must be
" known immediately.
let g:denshi#filetypes = get(g:, 'denshi#filetypes', ['python'])
let g:denshi#simplify_markup = get(g:, 'denshi#simplify_markup', v:true)
let g:denshi#no_default_builtin_highlight = get(g:, 'denshi#no_default_builtin_highlight', v:true)

function! s:simplify_markup()
    autocmd FileType python call s:simplify_markup_extra()

    " For python-syntax plugin
    let g:python_highlight_operators = 0
endfunction

function! s:simplify_markup_extra()
    hi link pythonConditional pythonStatement
    hi link pythonImport pythonStatement
    hi link pythonInclude pythonStatement
    hi link pythonRaiseFromStatement pythonStatement
    hi link pythonDecorator pythonStatement
    hi link pythonException pythonStatement
    hi link pythonConditional pythonStatement
    hi link pythonRepeat pythonStatement
endfunction

function! s:disable_builtin_highlights()
    autocmd FileType python call s:remove_builtin_extra()
    let g:python_no_builtin_highlight = 1
    hi link pythonBuiltin NONE
    let g:python_no_exception_highlight = 1
    hi link pythonExceptions NONE
    hi link pythonAttribute NONE
    hi link pythonDecoratorName NONE

    " For python-syntax plugin
    let g:python_highlight_class_vars = 0
    let g:python_highlight_builtins = 0
    let g:python_highlight_exceptions = 0
    hi link pythonDottedName NONE
endfunction

function! s:remove_builtin_extra()
    syn keyword pythonKeyword True False None
    hi link pythonKeyword pythonNumber
endfunction

function! s:filetype_changed()
    let l:ft = expand('<amatch>')
    if index(g:denshi#filetypes, l:ft) != -1
        if !get(b:, 'denshi_attached', v:false)
            Denshi enable
        endif
    else
        if get(b:, 'denshi_attached', v:false)
            Denshi disable
        endif
    endif
endfunction

function! denshi#buffer_attach()
    if get(b:, 'denshi_attached', v:false)
        return
    endif
    let b:denshi_attached = v:true
    augroup DenshiEvents
        autocmd! * <buffer>
        autocmd BufEnter <buffer> call DenshiBufEnter(+expand('<abuf>'), line('w0'), line('w$'))
        autocmd BufLeave <buffer> call DenshiBufLeave()
        autocmd VimResized <buffer> call DenshiVimResized(line('w0'), line('w$'))
        autocmd TextChanged <buffer> call DenshiTextChanged()
        autocmd TextChangedI <buffer> call DenshiTextChanged()
        autocmd CursorMoved <buffer> call DenshiCursorMoved(line('w0'), line('w$'))
        autocmd CursorMovedI <buffer> call DenshiCursorMoved(line('w0'), line('w$'))
    augroup END
    call DenshiBufEnter(bufnr('%'), line('w0'), line('w$'))
endfunction

function! denshi#buffer_detach()
    let b:denshi_attached = v:false
    augroup DenshiEvents
        autocmd! * <buffer>
    augroup END
endfunction

function! denshi#init()
    if g:denshi#no_default_builtin_highlight
        call s:disable_builtin_highlights()
    endif
    if g:denshi#simplify_markup
        call s:simplify_markup()
    endif

    autocmd FileType * call s:filetype_changed()
    autocmd BufWipeout * call DenshiBufWipeout(+expand('<abuf>'))
endfunction

call denshi#init()
