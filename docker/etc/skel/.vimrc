
"set autoindent      " 자동으로 들여쓰기를 한다.
"set cindent         " C 프로그래밍을 할때 자동으로 들여쓰기를 한다.
"set smartindent     " 좀더 똑똑한 들여쓰기를 위한 옵션이다.
"set textwidth=79    " 만약 79번째 글자를 넘어가면 \
"set wrap            " 자동으로 <CR>를 삽입하여 다음 줄로 넘어간다.
"set shiftwidth=4    " 자동 들여쓰기를 할때 3칸 들여쓰도록 한다.
"set fencs=ucs-bom,utf-8,euc-kr.latin1 "한글 파일은 euc-kr로 읽어들이며,유니코드는 유니코드로 읽어들이도록 설정
"set fileencoding=euc-kr         " 실제로 파일을 저장할때 사용되는 인코딩은 euc-kr
"set expandtab         " 탭을 입력하면 공백문자로 변환하는 기능을 설정

set nowrapscan      " 검색할 때 문서의 끝에서 다시 처음으로 돌아가지 않는다.
set nobackup        " 백업 파일을 만들지 않는다.
set visualbell      " 키를 잘못눌렀을 때 삑 소리를 내는 대신 번쩍이게 한다.
set ruler           " 화면 우측 하단에 현재 커서의 위치(줄,칸)를 보여준다.
set tabstop=4       " Tab을 눌렀을 때 8칸 대신 3칸 이동하도록 한다.
set number          " 행번호를 사용한다.
set background=dark " 하이라이팅 옵션
set hlsearch        " 검색어를 구문강조해주는 기능
set ignorecase      " 검색할 때 대소문자 무시하도록 하는 것.
set title " 타이틀바에 현재 편집중인 파일을 표시

syntax on

"if has("syntax")
"   syntax on           " Default to no syntax highlightning
"   endif

autocmd FileType c,cpp,java,scala let b:comment_leader = '//'
autocmd FileType sh,ruby,python   let b:comment_leader = '#'
autocmd FileType conf,fstab       let b:comment_leader = '#'
autocmd FileType tex              let b:comment_leader = '%'
autocmd FileType mail             let b:comment_leader = '>'
autocmd FileType vim              let b:comment_leader = '"'
autocmd FileType nasm             let b:comment_leader = ';'

function! CommentLine()
   execute ':silent! s/^\(.*\)/' . b:comment_leader . ' \1/g'
endfunction

function! UncommentLine()
   execute ':silent! s/^' . b:comment_leader . ' //g'
endfunction

map <F5> :call CommentLine()<CR>
map <S-F5> :call UncommentLine()<CR>
