"""由 aeb_brake.xosc 派生 aeb_cruise.xosc：把 brake_trigger 的触发时间由 3s 改为
999999s（永不触发），其余（路网/摆位/初速/故事结构）完全一致——esmini 要求
StoryBoard 至少含一个 Story，整段摘除故事会被拒收。供 A3 误触发测试使用：
该测试要求全程无危险事件，AEB 应保持沉默。用 python3 gen_cruise.py 在本目录运行。"""
import re
src = open('aeb_brake.xosc', encoding='utf-8').read()
pat = re.compile(r'(<Condition name="brake_trigger".*?<SimulationTimeCondition value=")3(")', re.S)
out, n = pat.subn(r'\g<1>999999\g<2>', src)
assert n == 1, n
out = out.replace('description="aeb_brake"', 'description="aeb_cruise (brake trigger disabled; for false-trigger test)"')
open('aeb_cruise.xosc', 'w', encoding='utf-8').write(out)
print("wrote aeb_cruise.xosc")
