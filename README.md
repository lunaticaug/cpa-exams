# Contents

1. getfiles (python) - web crawler
2. fileprocess (python, GPT o3, Claude) - file converter (hwp, pdf to markdown)
3. json schema

_Note._


# workflow

## 1. getfiles 

<aside>

 **(1) fetching post urls.**

 > 페이지에서 게시글 목록이 있는 구조물 위치를 지정하여 코드 작성 요청
 //*[`@id="container"`]/div[2]

</aside>


<aside>

**(2) fetching file_urls and basic info by post lists**

 > https://{url}/fileDown.do?menuNo=&atchFileId={`postid_by_process1`}&fileSn={`file_number_1to10`}&bbsId={Number}
 >
 > 파일번호 1~10을 호출해보고 등록되지 않은 번호에 마킹
 </aside>


<aside>

**(3) get files by file_urls by process2**
</aside>

## 2. fileprocess

<aside>



</aside>


## 3. json schema


---

원본 기출문제의 저작권은 금융감독원에게 있습니다.

All CPA exam questions are © FSS and may not be reproduced, distributed,
or publicly transmitted without prior written permission from FSS
(https://cpa.fss.or.kr).