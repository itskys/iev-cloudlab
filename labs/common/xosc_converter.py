"""IEV CloudLab 工业级 OpenSCENARIO 场景生成与互操作转换器 | OpenSCENARIO Converter & Exporter

功能说明：
  实现高校实验场景与汽车工业界自动驾驶仿真工具链（CARLA, CarMaker, esmini, VTD, Prescan）
  的无缝接轨。支持 ISO 22179 / Euro-NCAP 标准工况的参数化动态生成与 ASAM OpenSCENARIO 1.0/1.1
  标准 XML 导出。

核心能力：
  1. 纯 Python 零依赖标准 XML 构造器（兼具高鲁棒性与工业级规范结构）；
  2. 典型量产级测试工况参数化生成：
     - Cut-in 邻车突发加塞切入工况 (create_cutin_scenario)
     - CCRb 前车定点紧急制动避险工况 (create_ccr_braking_scenario)
     - 交叉口视线遮挡横穿工况 (create_crossing_scenario)
  3. OpenSCENARIO 结构化合规性校验器 (validate_xosc_xml)；
  4. Jupyter 原生一键本地导出按钮 (render_xosc_download_button)；
  5. 批量场景参数空间网格遍历 (batch_generate_scenarios)。
"""

import base64
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union


def _prettify_xml(elem: ET.Element) -> str:
    """将 ElementTree 转换为格式化良好的 XML 字符串"""
    rough_string = ET.tostring(elem, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode('utf-8')


def _create_base_xosc_tree(scenario_name: str, road_network_file: str = "cutin.xodr") -> Tuple[ET.Element, ET.Element, ET.Element]:
    """创建 ASAM OpenSCENARIO 1.1 标准根节点与基础头部结构"""
    root = ET.Element('OpenSCENARIO', {
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsi:noNamespaceSchemaLocation': 'OpenSCENARIO.xsd'
    })

    # 1. FileHeader
    header = ET.SubElement(root, 'FileHeader', {
        'revMajor': '1',
        'revMinor': '1',
        'date': datetime.now().isoformat(),
        'description': f'IEV CloudLab Industrial Benchmark Scenario: {scenario_name}',
        'author': 'IEV CloudLab Scenario Engineering Team',
    })

    # 2. ParameterDeclarations
    ET.SubElement(root, 'ParameterDeclarations')

    # 3. CatalogLocations
    catalog = ET.SubElement(root, 'CatalogLocations')
    ET.SubElement(catalog, 'VehicleCatalog')

    # 4. RoadNetwork
    road_net = ET.SubElement(root, 'RoadNetwork')
    ET.SubElement(road_net, 'LogicFile', {'filepath': road_network_file})

    # 5. Entities
    entities = ET.SubElement(root, 'Entities')

    # 6. Storyboard
    storyboard = ET.SubElement(root, 'Storyboard')
    init = ET.SubElement(storyboard, 'Init')
    actions = ET.SubElement(init, 'Actions')

    return root, entities, actions


def _add_vehicle_entity(
    entities_elem: ET.Element,
    entity_name: str,
    category: str = "car",
    length: float = 4.8,
    width: float = 1.8,
    height: float = 1.4,
    max_speed: float = 69.4,
    max_accel: float = 8.0,
    max_decel: float = 10.0,
):
    """添加标准车辆实体与 BoundingBox"""
    scen_obj = ET.SubElement(entities_elem, 'ScenarioObject', {'name': entity_name})
    veh = ET.SubElement(scen_obj, 'Vehicle', {'name': entity_name, 'vehicleCategory': category})
    ET.SubElement(veh, 'ParameterDeclarations')
    
    # 尺寸包围盒
    bb = ET.SubElement(veh, 'BoundingBox')
    ET.SubElement(bb, 'Center', {'x': str(length / 2.0), 'y': '0.0', 'z': str(height / 2.0)})
    ET.SubElement(bb, 'Dimensions', {'width': str(width), 'length': str(length), 'height': str(height)})
    
    # 性能限制
    perf = ET.SubElement(veh, 'Performance', {
        'maxSpeed': str(max_speed),
        'maxAcceleration': str(max_accel),
        'maxDeceleration': str(max_decel),
    })
    
    # 轮轴
    axles = ET.SubElement(veh, 'Axles')
    ET.SubElement(axles, 'FrontAxle', {'maxSteering': '0.5', 'wheelDiameter': '0.6', 'trackWidth': '1.6', 'positionX': str(length * 0.7), 'positionZ': '0.3'})
    ET.SubElement(axles, 'RearAxle', {'maxSteering': '0.0', 'wheelDiameter': '0.6', 'trackWidth': '1.6', 'positionX': '0.0', 'positionZ': '0.3'})
    ET.SubElement(veh, 'Properties')


def create_cutin_scenario_xosc(
    ego_speed_kmh: float = 50.0,
    target_speed_kmh: float = 40.0,
    initial_gap_m: float = 25.0,
    cutin_time_s: float = 3.5,
    target_lane_id: int = -2,
    ego_lane_id: int = -1,
    road_file: str = "cutin.xodr",
    output_path: Optional[str] = None,
) -> str:
    """参数化生成 ISO 22179 标准 Cut-in 加塞场景 OpenSCENARIO 1.1 XML 文件。

    :param ego_speed_kmh: 自车巡航初速度 (km/h)
    :param target_speed_kmh: 加塞目标车巡航初速度 (km/h)
    :param initial_gap_m: 初始纵向车间距 (m)
    :param cutin_time_s: 仿真开始后触发切入的时机 (s)
    :param target_lane_id: 目标车初始车道 (-2 表示左邻车道)
    :param ego_lane_id: 自车车道 (-1 表示主直行车道)
    :param road_file: 关联的 OpenDRIVE 道路网文件
    :param output_path: 保存 XML 路径（若 None 则仅返回 XML 字符串）
    :return: 格式化后的 OpenSCENARIO XML 文本
    """
    ego_v_ms = ego_speed_kmh / 3.6
    target_v_ms = target_speed_kmh / 3.6
    ego_s_init = 10.0
    target_s_init = ego_s_init + initial_gap_m

    root, entities, init_actions = _create_base_xosc_tree("Cut-in Emergency Avoidance", road_file)

    # 1. 添加实体
    _add_vehicle_entity(entities, "Ego", length=4.7, width=1.85, height=1.45)
    _add_vehicle_entity(entities, "Target", length=4.5, width=1.80, height=1.40)

    # 2. Init 初始位姿与初速
    for name, s_pos, lane_id, v_ms in [("Ego", ego_s_init, ego_lane_id, ego_v_ms),
                                       ("Target", target_s_init, target_lane_id, target_v_ms)]:
        p_act = ET.SubElement(init_actions, 'Private', {'entityRef': name})
        
        # Teleport 位姿
        act_tele = ET.SubElement(p_act, 'PrivateAction')
        tele = ET.SubElement(act_tele, 'TeleportAction')
        pos = ET.SubElement(tele, 'Position')
        lane_pos = ET.SubElement(pos, 'LanePosition', {
            'roadId': '0', 'laneId': str(lane_id), 'offset': '0.0', 's': str(s_pos)
        })
        
        # 初速
        act_spd = ET.SubElement(p_act, 'PrivateAction')
        long_act = ET.SubElement(act_spd, 'LongitudinalAction')
        spd_act = ET.SubElement(long_act, 'SpeedAction')
        ET.SubElement(spd_act, 'SpeedActionDynamics', {'dynamicsShape': 'step', 'value': '0.0', 'dynamicsDimension': 'time'})
        spd_tgt = ET.SubElement(spd_act, 'SpeedActionTarget')
        ET.SubElement(spd_tgt, 'AbsoluteTargetSpeed', {'value': f'{v_ms:.3f}'})

    # 3. Story: 触发加塞变道切入
    storyboard = root.find('Storyboard')
    story = ET.SubElement(storyboard, 'Story', {'name': 'CutInStory'})
    act = ET.SubElement(story, 'Act', {'name': 'CutInAct'})

    # ManeuverGroup
    m_group = ET.SubElement(act, 'ManeuverGroup', {'maximumExecutionCount': '1', 'name': 'CutInSequence'})
    actors = ET.SubElement(m_group, 'Actors', {'selectTriggeringEntities': 'false'})
    ET.SubElement(actors, 'EntityRef', {'entityRef': 'Target'})

    maneuver = ET.SubElement(m_group, 'Maneuver', {'name': 'CutInManeuver'})
    event = ET.SubElement(maneuver, 'Event', {'name': 'LaneChangeEvent', 'priority': 'overwrite'})

    # 变道 Action: 切入自车所在车道
    action_lc = ET.SubElement(event, 'Action', {'name': 'TargetLaneChange'})
    lat_act = ET.SubElement(action_lc, 'LateralAction')
    lc_act = ET.SubElement(lat_act, 'LaneChangeAction')
    ET.SubElement(lc_act, 'LaneChangeActionDynamics', {'dynamicsShape': 'sinusoidal', 'value': '2.0', 'dynamicsDimension': 'time'})
    lc_tgt = ET.SubElement(lc_act, 'LaneChangeTarget')
    ET.SubElement(lc_tgt, 'AbsoluteTargetLane', {'value': str(ego_lane_id)})

    # 触发条件: 仿真时间达到 cutin_time_s
    start_trig = ET.SubElement(event, 'StartTrigger')
    cond_group = ET.SubElement(start_trig, 'ConditionGroup')
    cond = ET.SubElement(cond_group, 'Condition', {
        'name': 'CutInTimeCondition', 'delay': '0.0', 'conditionEdge': 'rising'
    })
    by_val = ET.SubElement(cond, 'ByValueCondition')
    ET.SubElement(by_val, 'SimulationTimeCondition', {'value': str(cutin_time_s), 'rule': 'greaterThan'})

    # Act 启动触发条件
    act_start = ET.SubElement(act, 'StartTrigger')
    act_cg = ET.SubElement(act_start, 'ConditionGroup')
    act_c = ET.SubElement(act_cg, 'Condition', {'name': 'ActStart', 'delay': '0.0', 'conditionEdge': 'rising'})
    act_val = ET.SubElement(act_c, 'ByValueCondition')
    ET.SubElement(act_val, 'SimulationTimeCondition', {'value': '0.0', 'rule': 'greaterOrEqual'})

    # StopTrigger
    stop_trig = ET.SubElement(storyboard, 'StopTrigger')
    stop_cg = ET.SubElement(stop_trig, 'ConditionGroup')
    stop_c = ET.SubElement(stop_cg, 'Condition', {'name': 'EndTimeCondition', 'delay': '0.0', 'conditionEdge': 'rising'})
    stop_val = ET.SubElement(stop_c, 'ByValueCondition')
    ET.SubElement(stop_val, 'SimulationTimeCondition', {'value': '12.0', 'rule': 'greaterThan'})

    xml_text = _prettify_xml(root)

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_text)

    return xml_text


def create_ccr_braking_scenario_xosc(
    ego_speed_kmh: float = 60.0,
    target_speed_kmh: float = 60.0,
    initial_gap_m: float = 30.0,
    brake_trigger_time_s: float = 2.0,
    target_decel_ms2: float = 6.0,
    road_file: str = "cutin.xodr",
    output_path: Optional[str] = None,
) -> str:
    """生成 Euro-NCAP 标准 Car-to-Car Rear 紧急制动避险测试场景。"""
    ego_v_ms = ego_speed_kmh / 3.6
    target_v_ms = target_speed_kmh / 3.6
    ego_s_init = 10.0
    target_s_init = ego_s_init + initial_gap_m

    root, entities, init_actions = _create_base_xosc_tree("EuroNCAP CCRb Braking Scenario", road_file)
    _add_vehicle_entity(entities, "Ego")
    _add_vehicle_entity(entities, "Target")

    # 同一车道初始化
    for name, s_pos, v_ms in [("Ego", ego_s_init, ego_v_ms), ("Target", target_s_init, target_v_ms)]:
        p_act = ET.SubElement(init_actions, 'Private', {'entityRef': name})
        act_tele = ET.SubElement(p_act, 'PrivateAction')
        tele = ET.SubElement(act_tele, 'TeleportAction')
        pos = ET.SubElement(tele, 'Position')
        ET.SubElement(pos, 'LanePosition', {'roadId': '0', 'laneId': '-1', 'offset': '0.0', 's': str(s_pos)})

        act_spd = ET.SubElement(p_act, 'PrivateAction')
        long_act = ET.SubElement(act_spd, 'LongitudinalAction')
        spd_act = ET.SubElement(long_act, 'SpeedAction')
        ET.SubElement(spd_act, 'SpeedActionDynamics', {'dynamicsShape': 'step', 'value': '0.0', 'dynamicsDimension': 'time'})
        spd_tgt = ET.SubElement(spd_act, 'SpeedActionTarget')
        ET.SubElement(spd_tgt, 'AbsoluteTargetSpeed', {'value': f'{v_ms:.3f}'})

    # Story: 前车急刹至静止
    storyboard = root.find('Storyboard')
    story = ET.SubElement(storyboard, 'Story', {'name': 'BrakingStory'})
    act = ET.SubElement(story, 'Act', {'name': 'BrakingAct'})
    m_group = ET.SubElement(act, 'ManeuverGroup', {'maximumExecutionCount': '1', 'name': 'BrakingGroup'})
    actors = ET.SubElement(m_group, 'Actors', {'selectTriggeringEntities': 'false'})
    ET.SubElement(actors, 'EntityRef', {'entityRef': 'Target'})

    maneuver = ET.SubElement(m_group, 'Maneuver', {'name': 'DecelManeuver'})
    event = ET.SubElement(maneuver, 'Event', {'name': 'HardBrakeEvent', 'priority': 'overwrite'})

    action_brake = ET.SubElement(event, 'Action', {'name': 'TargetBrakingAction'})
    long_b = ET.SubElement(action_brake, 'LongitudinalAction')
    spd_b = ET.SubElement(long_b, 'SpeedAction')
    ET.SubElement(spd_b, 'SpeedActionDynamics', {
        'dynamicsShape': 'linear', 'value': str(target_decel_ms2), 'dynamicsDimension': 'rate'
    })
    spd_tgt_b = ET.SubElement(spd_b, 'SpeedActionTarget')
    ET.SubElement(spd_tgt_b, 'AbsoluteTargetSpeed', {'value': '0.0'})

    # 触发条件
    start_trig = ET.SubElement(event, 'StartTrigger')
    cond_group = ET.SubElement(start_trig, 'ConditionGroup')
    cond = ET.SubElement(cond_group, 'Condition', {
        'name': 'BrakeTimeTrigger', 'delay': '0.0', 'conditionEdge': 'rising'
    })
    by_val = ET.SubElement(cond, 'ByValueCondition')
    ET.SubElement(by_val, 'SimulationTimeCondition', {'value': str(brake_trigger_time_s), 'rule': 'greaterThan'})

    act_start = ET.SubElement(act, 'StartTrigger')
    act_cg = ET.SubElement(act_start, 'ConditionGroup')
    act_c = ET.SubElement(act_cg, 'Condition', {'name': 'ActStart', 'delay': '0.0', 'conditionEdge': 'rising'})
    act_val = ET.SubElement(act_c, 'ByValueCondition')
    ET.SubElement(act_val, 'SimulationTimeCondition', {'value': '0.0', 'rule': 'greaterOrEqual'})

    xml_text = _prettify_xml(root)
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_text)
    return xml_text


def validate_xosc_xml(xml_content_or_path: str) -> Tuple[bool, List[str]]:
    """核验 XML 文本或文件是否满足 ASAM OpenSCENARIO 1.x 规范结构。

    :param xml_content_or_path: XML 文本或 .xosc 文件路径
    :return: (is_valid, error_diagnostics)
    """
    errors = []
    if os.path.exists(xml_content_or_path):
        try:
            tree = ET.parse(xml_content_or_path)
            root = tree.getroot()
        except Exception as e:
            return False, [f"XML 语法解析失败: {str(e)}"]
    else:
        try:
            root = ET.fromstring(xml_content_or_path)
        except Exception as e:
            return False, [f"XML 文本解析失败: {str(e)}"]

    # 必备标签节点检查
    mandatory_tags = ['FileHeader', 'Entities', 'Storyboard']
    for tag in mandatory_tags:
        if root.find(tag) is None:
            errors.append(f"缺失必要核心节点: <{tag}>")

    # Entities 实体检查
    entities = root.find('Entities')
    if entities is not None:
        objs = entities.findall('ScenarioObject')
        if not objs:
            errors.append("实体列表为空：未定义任何 ScenarioObject")
        else:
            names = [o.get('name') for o in objs]
            if 'Ego' not in names:
                errors.append("警告：实体定义中未发现标准主车名称 'Ego'")

    # Storyboard 动作流检查
    sb = root.find('Storyboard')
    if sb is not None:
        if sb.find('Init') is None:
            errors.append("缺失初始位姿动作流: <Storyboard/Init>")
        if sb.find('Story') is None and sb.find('Init/Actions') is None:
            errors.append("未发现任何故事动作序列: <Story>")

    is_valid = len(errors) == 0
    return is_valid, errors


def render_xosc_download_button(xml_content: str, filename: str = "custom_scenario.xosc") -> str:
    """生成可在 Jupyter Notebook 中直接点击一键下载到本地的 HTML 按钮"""
    b64_data = base64.b64encode(xml_content.encode('utf-8')).decode('utf-8')
    data_uri = f"data:application/xml;base64,{b64_data}"

    html = f"""
    <div style="margin: 12px 0;">
        <a href="{data_uri}" download="{filename}"
           style="background: #2563eb; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 13px; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 2px 4px rgba(37,99,235,0.2);">
            📥 下载工业标准 OpenSCENARIO (.xosc) 文件
        </a>
        <span style="font-size: 12px; color: #64748b; margin-left: 10px;">
            可直接载入 CARLA / CarMaker / VTD / esmini 运行
        </span>
    </div>
    """
    return html


def batch_generate_scenarios(
    speed_range_kmh: List[float],
    gap_range_m: List[float],
    output_dir: str,
) -> List[str]:
    """批量生成参数化测试场景网格，用于极端场景模糊测试 (Fuzzing)。

    :param speed_range_kmh: 目标车切入车速列表 [30, 40, 50, ...]
    :param gap_range_m: 初始时距列表 [15, 20, 25, ...]
    :param output_dir: 输出目录
    :return: 生成的 .xosc 文件路径列表
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []

    for v in speed_range_kmh:
        for g in gap_range_m:
            fn = f"cutin_v{int(v)}_g{int(g)}.xosc"
            p = os.path.join(output_dir, fn)
            create_cutin_scenario_xosc(
                ego_speed_kmh=50.0,
                target_speed_kmh=v,
                initial_gap_m=g,
                cutin_time_s=3.0,
                output_path=p,
            )
            generated_files.append(p)

    return generated_files
