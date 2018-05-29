"Ensure vim has been compiled in python mode and we are editing a python file.
if !has('python3') || expand("%:e")!="py"
    finish
endif

" Make the plugin directory globally accessible
let g:plugindir = expand('<sfile>:p:h')
let g:filename = expand('%:p')

" Initialise the gutter
function! s:defineHighlights()
    highlight testPassed  guifg=#009900 guibg=#009900 ctermfg=2 ctermbg=2
    highlight testFailed  guifg=#ff2222 guibg=#ff2222 ctermfg=1 ctermbg=1
endfunction

function! s:defineSigns()
    sign define testPassed texthl=testPassed text=+ 
    sign define testFailed texthl=testFailed text=+
endfunction

" Functions to place marks in the gutter
function! s:markSuccess(lineNumber)
    execute ":sign place 1 line=" . a:lineNumber . " name=testPassed file=" . expand("%:p")
endfunction

function! s:markFailure(lineNumber)
    execute ":sign place 1 line=" . a:lineNumber . " name=testFailed file=" . expand("%:p")
endfunction

function! s:markNone(lineNumber)
    execute ":sign unplace 1 line=" . a:lineNumber . "file=" . expand("%:p")
endfunction

call s:defineHighlights()
call s:defineSigns()

py3 << EOF
import sys
import vim
sys.path.append(vim.eval('g:plugindir'))
import runTests
tm=runTests.TestManager()
EOF

command! Runtests execute 'py3 tm.runTests()'

autocmd BufRead,BufNewFile *.py nnoremap <F4> <ESC>:w<CR>:Runtests<CR>
execute ':Runtests'




