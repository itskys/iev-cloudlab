"""生成 cut-in 测试场景：Target 在 Ego 前方相邻车道，5s 后切入 Ego 车道。

输出: cutin.xodr + cutin.xosc（OpenSCENARIO 1.1，可被 esmini v3.10.0 播放）
依赖: pip install "numpy==1.26.4" "scipy==1.13.1" scenariogeneration==0.9.3
  （注意：scenariogeneration 0.9.3 与 numpy 2.x 不兼容，必须 pin numpy 1.x；
   scipy 则需选兼容 numpy 1.x 的 1.13.1——已实测验证）
用法: python3 gen_cutin.py   # 在 cutin.xodr/cutin.xosc 所在目录运行 esmini
"""
from scenariogeneration import xosc as OSC
from scenariogeneration.xodr import OpenDrive
from scenariogeneration.xodr.generators import create_straight_road

# ---------- 1. 路网：600m 双车道直道（200m 时自车在路尽头追尾停住的前车，交互无法完成） ----------
road = create_straight_road(road_id=0, length=600, n_lanes=2, lane_offset=3)
odr = OpenDrive("cutin_road")
odr.add_road(road)
odr.adjust_roads_and_lanes()
odr.write_xml("cutin.xodr")
print("wrote cutin.xodr")

# ---------- 2. 车辆 ----------
bb = OSC.BoundingBox(2.0, 4.8, 1.8, 1.4, 0.0, 0.9)
fa = OSC.Axle(2.5, 2.5, 1.8, 1.4, 0.9)
ba = OSC.Axle(0.0, 0.0, 1.8, 1.4, 0.9)
ego_veh = OSC.Vehicle("EgoCar", OSC.VehicleCategory.car, bb, fa, ba, 150, 10, 8)
tgt_veh = OSC.Vehicle("TargetCar", OSC.VehicleCategory.car, bb, fa, ba, 150, 10, 8)

entities = OSC.Entities()
entities.add_scenario_object("Ego", ego_veh)
entities.add_scenario_object("Target", tgt_veh)

# ---------- 3. Init：摆位 + 初速 ----------
TD = OSC.TransitionDynamics(OSC.DynamicsShapes.step, OSC.DynamicsDimension.rate, 1)
init = OSC.Init()
init.add_init_action("Ego", OSC.TeleportAction(OSC.LanePosition(10, 0, -1, 0)))
init.add_init_action("Ego", OSC.AbsoluteSpeedAction(15, TD))
init.add_init_action("Target", OSC.TeleportAction(OSC.LanePosition(45, 0, -2, 0)))
init.add_init_action("Target", OSC.AbsoluteSpeedAction(12, TD))

# ---------- 4. Story：t=5s 时 Target 切入 Ego 车道 ----------
start_trigger = OSC.ValueTrigger(
    "act_start", 0, OSC.ConditionEdge.rising,
    OSC.SimulationTimeCondition(0, OSC.Rule.greaterThan),
    triggeringpoint="start",
)
cutin_trigger = OSC.ValueTrigger(
    "cutin", 0, OSC.ConditionEdge.rising,
    OSC.SimulationTimeCondition(5, OSC.Rule.greaterThan),
    triggeringpoint="start",
)
event = OSC.Event("cutin_event", OSC.Priority.overwrite)
event.add_trigger(cutin_trigger)
event.add_action("lanechange", OSC.AbsoluteLaneChangeAction(-1, TD))

man = OSC.Maneuver("cutin_maneuver")
man.add_event(event)
mangr = OSC.ManeuverGroup("cutin_group")
mangr.add_actor("Target")
mangr.add_maneuver(man)
act = OSC.Act("cutin_act", start_trigger)
act.add_maneuver_group(mangr)
story = OSC.Story("cutin_story")
story.add_act(act)

# ---------- 5. StoryBoard：30s 停止 ----------
stop_trigger = OSC.ValueTrigger(
    "sim_stop", 0, OSC.ConditionEdge.rising,
    OSC.SimulationTimeCondition(30, OSC.Rule.greaterThan),
    triggeringpoint="stop",
)
sb = OSC.StoryBoard(init, stoptrigger=stop_trigger)
sb.add_story(story)

# ---------- 6. 组装（OpenSCENARIO 1.1；1.2 已弃用 VehicleCategory.car） ----------
roadnet = OSC.RoadNetwork("cutin.xodr")
sce = OSC.Scenario(
    "cutin_03", "IEV CloudLab",
    OSC.ParameterDeclarations(),
    entities=entities, storyboard=sb,
    roadnetwork=roadnet, catalog=OSC.Catalog(),
    osc_minor_version=1,
)
sce.write_xml("cutin.xosc")
print("wrote cutin.xosc")
