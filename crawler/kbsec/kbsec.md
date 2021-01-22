
##  

```bash
PYTHONPATH=. python3 module/kbsec/kbsec.py --report-list
PYTHONPATH=. python3 module/kbsec/kbsec.py --reports
```

## export 

```bash
cp data/kbsec/kbsec.db data/kbsec/kbsec.bak.db

PYTHONPATH=. python3 module/kbsec/kbsec.py --export \
    --filename data/kbsec/kbsec.bak.db

rename 's/.bak././' data/kbsec/kbsec.bak.report*
```

## pdf

```bash
cat doc-id.list | xargs -I{} echo "wget --no-netrc -c http://rdata.kbsec.com/pdf_data/{}.pdf ; sleep 2" | bash -
```

## memo

```text
{
    'reportTag': '[KB: ETF/솔루션]',
    'thumnail': None,
    'tp': None,
    'vod': None,
    'analystNm': '공원배',
    'pCategoryid': '12',
    'docSubDetail': None,
    'stock': None,
    'docTitle': 'KB Delta 1',
    'name': None,
    'thumbnailImg': None,
    'indName': None,
    'vodUrl': None,
    'recommChg': None,
    'vodDate': None,
    'urlLinkH': 'https://bit.ly/2zE5VGX\n',
    'recomm': 'Not Rated',
    'publicDate': '2020-05-28',
    'publicTime': '07:38:32',
    'categoryid': '74',
    'docTitleSub': '대표지수 (KOSPI200, KOSDAQ150 등) 정기변경 확정',
    'documentid': '20200528002248760K',
    'docDetail2': None,
    'foldertemplate': '자산배분/매크로>자산배분 > 자산배분>ETF',
    'stkCd': '284740',
    'docDetail': '- 대표지수 정기변경 확정: KOSPI200 11종목, KOSDAQ150 14종목, KRX300 23종목\n- 2020년 6월 정기변경 주목할 포인트는? 과거와 다른 변화에 주목할 것\n- KOSPI200: 쿠쿠홈시스, 태영건설, 롯데관광개발 등 Days to Cover 높은 종목에 주목\n- KOSDAQ150 정기변경, 변화의 시작: 금융 섹터 종목의 경우 최초로 편입',
    'urlLink': 'https://bit.ly/2TJeeI6\n'
}

https://rc.kbsec.com/detailView.able?documentid=20200528002248760K

<input type="hidden" id="enc" value="aHR0cDovL3JkYXRhLmtic2VjLmNvbS9wZGZfZGF0YS8yMDIwMTEyMDA2NDkyNzI3MEsucGRm"/>

https://rc.kbsec.com/js/researchWeb/detailView/detailView.js?v=1606204712096


			var sUrl = 'https://rcv.kbsec.com/streamdocs/pdfview?id=B520190322125512762443&url=';
			var gbn = $("#gbn").val();
			var originalPdfUrl = atob(g_url);
			sUrl = sUrl + g_url;
			if(gbn) {
				sUrl = originalPdfUrl;
			}



https://rcv.kbsec.com/streamdocs/pdfview?url=aHR0cDovL3JkYXRhLmtic2VjLmNvbS9wZGZfZGF0YS8yMDIwMTEyNDE0MzIzNjIwN0sucGRm

$('#sdview').attr('src', 'https://rcv.kbsec.com/streamdocs/view/sd;streamdocsId=' + '72059200234928754' + ';fitMode=;viewMode=' + ';createdDictionary=' + true);


https://rcv.kbsec.com/streamdocs/v4/documents/72059199862928756/info

https://rcv.kbsec.com/streamdocs/v4/documents/72059200234928754/texts/0




				for(var i=0; i<arguments.length :="" arg="arguments[i];" callback:function="" categoryid="" chartcallback="" e.preventdefault="" g_url="" gbn='$("#gbn").val();' i="" if="" originalpdfurl="atob(g_url);" param="" reportid="" reportnm="" scategoryid="" surl="https://pdfview.kbsec.com/streamdocs/pdfview?id=B520190322125512762443&amp;url=" url="" var="" window.open="">pdf");	
			window.open(sUrl, "KB리서치&gt;pdf");	

https://pdfview.kbsec.com/streamdocs/pdfview?id=B520190322125512762443&url=aHR0cDovL3JkYXRhLmtic2VjLmNvbS9wZGZfZGF0YS8yMDIwMTEyNDA5NTQzMzExMEsucGRm




https://rcv.kbsec.com/streamdocs/get-word

https://rcv.kbsec.com/streamdocs/get-word-meaning

https://rcv.kbsec.com/streamdocs/pdfview?url=aHR0cDovL3JkYXRhLmtic2VjLmNvbS9wZGZfZGF0YS8yMDIwMTEyMDA2NDkyNzI3MEsucGRm


```
