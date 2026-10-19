"""H1: 参数化批量生成 cut-in 场景（3x3 全因子实验设计）。

参数网格：
  - 初始纵向间距 d ∈ {20, 30, 40} m（Ego s=10，Target s=10+d）
  - 目标车速 v ∈ {10, 12, 14} m/s（Ego 固定 15 m/s）
共 9 种组合 → 9 个 xosc 文件 + 1 个共享 xodr。

输出: labs/scenarios/A_esmini/H1_batch/cutin_d{d:02d}_v{v:02d}.xosc
依赖: pip install "numpy==1.26.4" "scipy==1.13.1" scenariogeneration==0.9.3
用法: python3 gen_batch.py   # 在 H1_batch/ 目录运行
"""
import os
from scenariogeneration import xosc as OSC
from scenariogeneration.xodr import OpenDrive
from scenariogeneration.xodr.generators import create_straight_road

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DISTANCES = [20, 30, 40]   # m, Ego 与 Target 初始纵向间距
SPEEDS = [10, 12, 14]      # m/s, Target 初速（Ego 固定 15 m/s）
EGO_S = 10.0
EGO_V = 15.0
CUTIN_T = 5.0              # s, Target 变道触发时刻
SIM_T = 20.0               # s, 仿真时长


def build_road():
    road = create_straight_road(road_id=0, length=400, n_lanes=2, lane_offset=3)
    odr = OpenDrive("h1_batch_road")
    odr.add_road(road)
    odr.adjust_roads_and_lanes()
    path = os.path.join(OUT_DIR, "h1_batch.xodr")
    odr.write_xml(path)
    print(f"wrote {path}")
    return os.path.basename(path)


def build_scenario(dist, speed, xodr_name):
    bb = OSC.BoundingBox(2.0, 4.8, 1.8, 1.4, 0.0, 0.9)
    fa = OSC.Axle(2.5, 2.5, 1.8, 1.4, 0.9)
    ba = OSC.Axle(0.0, 0.0, 1.8, 1.4, 0.9)
    ego_veh = OSC.Vehicle("EgoCar", OSC.VehicleCategory.car, bb, fa, ba, 150, 10, 8)
    tgt_veh = OSC.Vehicle("TargetCar", OSC.VehicleCategory.car, bb, fa, ba, 150, 10, 8)

    entities = OSC.Entities()
    entities.add_scenario_object("Ego", ego_veh)
    entities.add_scenario_object("Target", tgt_veh)

    TD = OSC.TransitionDynamics(OSC.DynamicsShapes.step,
                                OSC.DynamicsDimension.rate, 1)
    init = OSC.Init()
    init.add_init_action("Ego", OSC.TeleportAction(OSC.LanePosition(EGO_S, 0, -1, 0)))
    init.add_init_action("Ego", OSC.AbsoluteSpeedAction(EGO_V, TD))
    init.add_init_action(
        "Target", OSC.TeleportAction(OSC.LanePosition(EGO_S + dist, 0, -2, 0)))
    init.add_init_action("Target", OSC.AbsoluteSpeedAction(speed, TD))

    start_trigger = OSC.ValueTrigger(
        "act_start", 0, OSC.ConditionEdge.rising,
        OSC.SimulationTimeCondition(0, OSC.Rule.greaterThan),
        triggeringpoint="start",
    )
    cutin_trigger = OSC.ValueTrigger(
        "cutin", 0, OSC.ConditionEdge.rising,
        OSC.SimulationTimeCondition(CUTIN_T, OSC.Rule.greaterThan),
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

    stop_trigger = OSC.ValueTrigger(
        "sim_stop", 0, OSC.ConditionEdge.rising,
        OSC.SimulationTimeCondition(SIM_T, OSC.Rule.greaterThan),
        triggeringpoint="stop",
    )
    sb = OSC.StoryBoard(init, stoptrigger=stop_trigger)
    sb.add_story(story)

    roadnet = OSC.RoadNetwork(xodr_name)
    sce = OSC.Scenario(
        f"h1_cutin_d{dist:02d}_v{speed:02d}", "IEV CloudLab",
        OSC.ParameterDeclarations(),
        entities=entities, storyboard=sb,
        roadnetwork=roadnet, catalog=OSC.Catalog(),
        osc_minor_version=1,
    )
    fname = f"cutin_d{dist:02d}_v{speed:02d}.xosc"
    path = os.path.join(OUT_DIR, fname)
    sce.write_xml(path)
    return fname


def main():
    xodr_name = build_road()
    files = []
    for d in DISTANCES:
        for v in SPEEDS:
            files.append(build_scenario(d, v, xodr_name))
    print(f"generated {len(files)} scenarios:")
    for f in files:
        print("  ", f)
    assert len(files) == len(DISTANCES) * len(SPEEDS) == 9


if __name__ == "__main__":
    main()
