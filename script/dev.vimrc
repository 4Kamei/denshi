"A minimal vimrc for development

syntax on
set nocompatible
colorscheme zellner

set noswapfile
set hidden
set tabstop=8
set shiftwidth=4
set softtabstop=4
set smarttab
set expandtab
set number

let &runtimepath .= ',' . getcwd()
let $NVIM_RPLUGIN_MANIFEST = './script/rplugin.vim'

let mapleader = ','

noremap <silent> <S-j> 4j
noremap <silent> <S-k> 4k
noremap <silent> q :q<CR>
noremap <silent> Q :qa!<CR>
noremap <silent><C-tab> :bnext<CR>
noremap <silent><C-S-tab> :bprev<CR>


function! SynStack()
    if !exists('*synstack')
        return
    endif
    echo map(synstack(line('.'), col('.')), "synIDattr(v:val, 'name')")
endfunc
nnoremap <leader>v :call SynStack()<CR>


let $DENSHI_LOG_FILE = '/tmp/denshi.log'
let $DENSHI_LOG_LEVEL = 'DEBUG'

let g:denshi#error_sign_delay = 0.5

nmap <silent> <leader>rr :Denshi rename<CR>
nmap <silent> <Tab> :Denshi goto name next<CR>
nmap <silent> <S-Tab> :Denshi goto name prev<CR>

nmap <silent> <C-n> :Denshi goto class next<CR>
nmap <silent> <C-p> :Denshi goto class prev<CR>

nmap <silent> <C-a> :Denshi goto function next<CR>
nmap <silent> <C-x> :Denshi goto function prev<CR>

nmap <silent> <leader>ee :Denshi error<CR>
nmap <silent> <leader>ge :Denshi goto error<CR>
