"""Generate A4 LTAP-OD intersection-yield scenario (pure XML, no scenariogeneration needed).

LTAP-OD = Left Turn Across Path - Opposite Direction.
Geometry (world coordinates, meters):
    Road 0: east-west  (0,0) -> (200,0),   hdg = 0
    Road 1: north-south (100,100) -> (100,-300), hdg = -pi/2  (length 400)

    Target (esmini scripted): road 1, lane -1 (x ~= 98.5), s = 45 -> (98.5, 55),
                              constant 16 m/s southbound.
    Ego (Python controlled):  road 1, lane +1 (x ~= 101.5), s = 130 -> (101.5, -30),
                              heading north. Student controller decides yield/turn.
    Conflict point: (98.5, 0.0) where Ego's left-turn path crosses Target's lane.

Outputs: intersection.xodr, intersection.xosc
"""

import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

XODR = """<?xml version="1.0" encoding="utf-8"?>
<OpenDRIVE>
    <header name="intersection" revMajor="1" revMinor="5" date="2026-10-19 00:00:00" north="0.0" south="0.0" east="0.0" west="0.0"/>
    <road rule="RHT" id="0" junction="-1" length="200">
        <link/>
        <planView>
            <geometry s="0" x="0" y="0" hdg="0" length="200">
                <line/>
            </geometry>
        </planView>
        <elevationProfile/>
        <lateralProfile/>
        <lanes>
            <laneSection s="0">
                <left>
                    <lane id="2" type="driving" level="false">
                        <link/>
                        <width a="3" b="0" c="0" d="0" sOffset="0"/>
                        <roadMark sOffset="0" type="broken" weight="standard" color="standard" height="0.02" width="0.2"/>
                    </lane>
                    <lane id="1" type="driving" level="false">
                        <link/>
                        <width a="3" b="0" c="0" d="0" sOffset="0"/>
                        <roadMark sOffset="0" type="broken" weight="standard" color="standard" height="0.02" width="0.2"/>
                    </lane>
                </left>
                <center>
                    <lane id="0" type="none" level="false">
                        <roadMark sOffset="0" type="broken" weight="standard" color="standard" height="0.02" width="0.2"/>
                    </lane>
                </center>
                <right>
                    <lane id="-1" type="driving" level="false">
                        <link/>
                        <width a="3" b="0" c="0" d="0" sOffset="0"/>
                        <roadMark sOffset="0" type="broken" weight="standard" color="standard" height="0.02" width="0.2"/>
                    </lane>
                    <lane id="-2" type="driving" level="false">
                        <link/>
                        <width a="3" b="0" c="0" d="0" sOffset="0"/>
                        <roadMark sOffset="0" type="broken" weight="standard" color="standard" height="0.02" width="0.2"/>
                    </lane>
                </right>
            </laneSection>
        </lanes>
    </road>
    <road rule="RHT" id="1" junction="-1" length="400">
        <link/>
        <planView>
            <geometry s="0" x="100" y="100" hdg="-1.57079632679" length="400">
                <line/>
            </geometry>
        </planView>
        <elevationProfile/>
        <lateralProfile/>
        <lanes>
            <laneSection s="0">
                <left>
                    <lane id="2" type="driving" level="false">
                        <link/>
                        <width a="3" b="0" c="0" d="0" sOffset="0"/>
                        <roadMark sOffset="0" type="broken" weight="standard" color="standard" height="0.02" width="0.2"/>
                    </lane>
                    <lane id="1" type="driving" level="false">
                        <link/>
                        <width a="3" b="0" c="0" d="0" sOffset="0"/>
                        <roadMark sOffset="0" type="broken" weight="standard" color="standard" height="0.02" width="0.2"/>
                    </lane>
                </left>
                <center>
                    <lane id="0" type="none" level="false">
                        <roadMark sOffset="0" type="broken" weight="standard" color="standard" height="0.02" width="0.2"/>
                    </lane>
                </center>
                <right>
                    <lane id="-1" type="driving" level="false">
                        <link/>
                        <width a="3" b="0" c="0" d="0" sOffset="0"/>
                        <roadMark sOffset="0" type="broken" weight="standard" color="standard" height="0.02" width="0.2"/>
                    </lane>
                    <lane id="-2" type="driving" level="false">
                        <link/>
                        <width a="3" b="0" c="0" d="0" sOffset="0"/>
                        <roadMark sOffset="0" type="broken" weight="standard" color="standard" height="0.02" width="0.2"/>
                    </lane>
                </right>
            </laneSection>
        </lanes>
    </road>
</OpenDRIVE>
"""

VEHICLE_XML = """        <ScenarioObject name="{name}">
            <Vehicle name="{name}Car" vehicleCategory="car">
                <ParameterDeclarations/>
                <BoundingBox>
                    <Center x="1.4" y="0.0" z="0.9"/>
                    <Dimensions width="2.0" length="4.8" height="1.8"/>
                </BoundingBox>
                <Performance maxSpeed="150.0" maxDeceleration="8.0" maxAcceleration="10.0"/>
                <Axles>
                    <FrontAxle maxSteering="2.5" wheelDiameter="2.5" trackWidth="1.8" positionX="1.4" positionZ="0.9"/>
                    <RearAxle maxSteering="0.0" wheelDiameter="0.0" trackWidth="1.8" positionX="1.4" positionZ="0.9"/>
                </Axles>
                <Properties/>
            </Vehicle>
        </ScenarioObject>
"""

XOSC = """<?xml version="1.0" encoding="utf-8"?>
<OpenSCENARIO xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="OpenScenario.xsd">
    <FileHeader description="ltap_od_yield" author="IEV CloudLab" revMajor="1" revMinor="1" date="2026-10-19T00:00:00"/>
    <ParameterDeclarations/>
    <CatalogLocations/>
    <RoadNetwork>
        <LogicFile filepath="intersection.xodr"/>
    </RoadNetwork>
    <Entities>
""" + VEHICLE_XML.format(name="Ego") + VEHICLE_XML.format(name="Target") + """    </Entities>
    <Storyboard>
        <Init>
            <Actions>
                <Private entityRef="Ego">
                    <PrivateAction>
                        <TeleportAction>
                            <Position>
                                <LanePosition roadId="1" laneId="1" s="130.0" offset="0.0"/>
                            </Position>
                        </TeleportAction>
                    </PrivateAction>
                    <PrivateAction>
                        <LongitudinalAction>
                            <SpeedAction>
                                <SpeedActionDynamics dynamicsShape="step" value="1.0" dynamicsDimension="rate"/>
                                <SpeedActionTarget>
                                    <AbsoluteTargetSpeed value="9.0"/>
                                </SpeedActionTarget>
                            </SpeedAction>
                        </LongitudinalAction>
                    </PrivateAction>
                </Private>
                <Private entityRef="Target">
                    <PrivateAction>
                        <TeleportAction>
                            <Position>
                                <LanePosition roadId="1" laneId="-1" s="45.0" offset="0.0"/>
                            </Position>
                        </TeleportAction>
                    </PrivateAction>
                    <PrivateAction>
                        <LongitudinalAction>
                            <SpeedAction>
                                <SpeedActionDynamics dynamicsShape="step" value="1.0" dynamicsDimension="rate"/>
                                <SpeedActionTarget>
                                    <AbsoluteTargetSpeed value="16.0"/>
                                </SpeedActionTarget>
                            </SpeedAction>
                        </LongitudinalAction>
                    </PrivateAction>
                </Private>
            </Actions>
        </Init>
        <Story name="cruise_story">
            <ParameterDeclarations/>
            <Act name="cruise_act">
                <ManeuverGroup name="cruise_group" maximumExecutionCount="1">
                    <Actors selectTriggeringEntities="false">
                        <EntityRef entityRef="Target"/>
                    </Actors>
                    <Maneuver name="cruise_maneuver">
                        <Event name="cruise_event" priority="overwrite" maximumExecutionCount="1">
                            <Action name="keep_speed">
                                <PrivateAction>
                                    <LongitudinalAction>
                                        <SpeedAction>
                                            <SpeedActionDynamics dynamicsShape="step" value="1.0" dynamicsDimension="rate"/>
                                            <SpeedActionTarget>
                                                <AbsoluteTargetSpeed value="16.0"/>
                                            </SpeedActionTarget>
                                        </SpeedAction>
                                    </LongitudinalAction>
                                </PrivateAction>
                            </Action>
                            <StartTrigger>
                                <ConditionGroup>
                                    <Condition name="cruise_trigger" delay="0" conditionEdge="rising">
                                        <ByValueCondition>
                                            <SimulationTimeCondition value="0" rule="greaterThan"/>
                                        </ByValueCondition>
                                    </Condition>
                                </ConditionGroup>
                            </StartTrigger>
                        </Event>
                    </Maneuver>
                </ManeuverGroup>
                <StartTrigger>
                    <ConditionGroup>
                        <Condition name="act_start" delay="0" conditionEdge="rising">
                            <ByValueCondition>
                                <SimulationTimeCondition value="0" rule="greaterThan"/>
                            </ByValueCondition>
                        </Condition>
                    </ConditionGroup>
                </StartTrigger>
                <StopTrigger/>
            </Act>
        </Story>
        <StopTrigger>
            <ConditionGroup>
                <Condition name="sim_stop" delay="0" conditionEdge="rising">
                    <ByValueCondition>
                        <SimulationTimeCondition value="30" rule="greaterThan"/>
                    </ByValueCondition>
                </Condition>
            </ConditionGroup>
        </StopTrigger>
    </Storyboard>
</OpenSCENARIO>
"""

if __name__ == '__main__':
    with open(os.path.join(OUT_DIR, 'intersection.xodr'), 'w') as f:
        f.write(XODR)
    with open(os.path.join(OUT_DIR, 'intersection.xosc'), 'w') as f:
        f.write(XOSC)
    print(f'Generated intersection.xodr and intersection.xosc in {OUT_DIR}')
