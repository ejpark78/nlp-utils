
# detail
```bash
time pbzip2 -p8 -c -d crawler-naver-kin-detail.json.bz2 \
    | jq -c '{"category": .category, "answer": .answer, "question": .detail_question}' \
    | perl -ple 's/"category":\[\]/"category":""/' \
    | bzip2 > crawler-naver-kin-detail.simple.json.bz2

# 실행 시간: 45:13.83, 사용자: 2805.40, 시스템: 35.88, CPU: 104%, 전체: 2713.83

```

# question_list / question_list_done
```json
{
  "d1Id": 8,
  "dirId": 8030401,
  "docId": 319157641,
  "document_id": "8-8030401-319157641",
  "fullDirNamePath": "Q&A > 생활 > 미용 > 다이어트, 체형관리 > 음식다이어트",
  "previewContents": "제가 근력운동 후 바나나1개 계란2개 건포도 5개정도 먹는데.. 운동 후 건포도를 먹으면 안되나요?",
}
```

```bash
time pbzip2 -p8 -c -d crawler-naver-kin-question_list.json.bz2 \
    | jq -c '{"d1Id": .d1Id, "dirId": .dirId, "docId": .docId, "fullDirNamePath": .fullDirNamePath, "question": .previewContents}' \
    | bzip2 > crawler-naver-kin-question_list.simple.json.bz2

time pbzip2 -p8 -c -d crawler-naver-kin-question_list_done.json.bz2 \
    | jq -c '{"d1Id": .d1Id, "dirId": .dirId, "docId": .docId, "fullDirNamePath": .fullDirNamePath, "question": .previewContents}' \
    | bzip2 > crawler-naver-kin-question_list_done.simple.json.bz2

```

