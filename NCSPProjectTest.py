#!./venv/bin/python3

from NCSPProject import NCSPProject

sp_ner = NCSPProject()
sp_ner.verbose = True

sentence = "뉴스1) 이광호 기자 LA다저스의 류현진 선수와 마틴 김이 1일 미국 캘리포니아주 로스앤젤레스 제시 오웬스 공원에서 열린 LA다저스 팬페스티벌에 참석해 대화하고 있다."
pos_tagged = "뉴스/NNG+1/SN+)/SS 이광호/NNP 기자/NNG LA/SL+다저스/NNP+의/JKG 류현진/NNP 선수/NNG+와/JKB 마틴/NNP 김/NNP+이/JKS 1/SN+일/NNB 미국/NNP 캘리포니아주/NNP 로스앤젤레스/NNP 제시/NNP 오웬스/NNP 공원/NNG+에서/JKB 열리/VV+ㄴ/ETM LA/SL+다저스/NNP 팬/NNG+페스티벌/NNG+에/JKB 참석/NNG+하/XSV+아/EM 대화/NNG+하/XSV+고/EM 있/VX+다/EM+./SF"

config="./sp_config.ini"
domain="baseball"

sp_ner.open(config, domain)

ner_result = sp_ner.translate(sentence, pos_tagged)
print(sentence)
print(pos_tagged)
print(ner_result.strip())

sp_ner.close()
