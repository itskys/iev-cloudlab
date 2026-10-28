"""IEV CloudLab 共享库 v0.9.0"""
from .controller import BaseController, PIDController
from .esmini_env import EsminiEnv, KinematicBicycleModel
from .battery_adapter import BatteryFASTSimAdapter
from .fastsim_helper import load_bev_list, run_udds, compare_vehicles, plot_cycle
from .vehicle_library import (
    list_batteries, list_vehicles,
    load_battery, load_vehicle,
    save_result, load_result,
)
from .report_checker import (
    verify_report_consistency,
    check_student_directory,
    check_class_reports,
    format_verification_markdown,
    format_verification_html,
)
from .chain_validator import (
    validate_d3_to_c1_chain,
    load_chained_battery_model,
    render_chain_status_html,
    analyze_battery_energy_chain,
    plot_chain_correlation,
)
from .skills_profiler import (
    compute_student_skill_profile,
    render_student_radar_svg,
    compute_class_skills_matrix,
    render_class_weakness_html,
    SKILL_DIMENSIONS,
)
from .xosc_converter import (
    create_cutin_scenario_xosc,
    create_ccr_braking_scenario_xosc,
    validate_xosc_xml,
    render_xosc_download_button,
    batch_generate_scenarios,
)
from .report_evaluator import (
    evaluate_report_comprehensively,
    render_report_evaluation_card,
)
from .student_cockpit import (
    get_student_study_progress,
    render_student_cockpit_html,
    pre_submit_report_check,
    scan_personal_results,
)
from .snapshot_manager import (
    create_snapshot,
    list_snapshots,
    restore_snapshot,
    compute_code_diff,
    render_time_machine_html,
    show_time_machine,
)
from .plagiarism_detector import (
    check_code_similarity,
    scan_class_code_plagiarism,
    render_plagiarism_report_html,
)

__version__ = "0.9.0"
__all__ = [
    "BaseController", "PIDController",
    "EsminiEnv", "KinematicBicycleModel",
    "BatteryFASTSimAdapter",
    "load_bev_list", "run_udds", "compare_vehicles", "plot_cycle",
    "list_batteries", "list_vehicles",
    "load_battery", "load_vehicle",
    "save_result", "load_result",
    # 实验报告一致性核验 (T1.1)
    "verify_report_consistency", "check_student_directory", "check_class_reports",
    "format_verification_markdown", "format_verification_html",
    # 跨实验数据链路门禁 (T1.2)
    "validate_d3_to_c1_chain", "load_chained_battery_model", "render_chain_status_html",
    "analyze_battery_energy_chain", "plot_chain_correlation",
    # 7 大核心工程能力雷达与短板画像 (T1.3)
    "compute_student_skill_profile", "render_student_radar_svg",
    "compute_class_skills_matrix", "render_class_weakness_html",
    "SKILL_DIMENSIONS",
    # OpenSCENARIO 工业级导出与转换器 (T2.1)
    "create_cutin_scenario_xosc", "create_ccr_braking_scenario_xosc",
    "validate_xosc_xml", "render_xosc_download_button", "batch_generate_scenarios",
    # 实验报告综合质性评定 (T2.2)
    "evaluate_report_comprehensively", "render_report_evaluation_card",
    # 学生自主学习驾驶舱与预审自检 (T2.3)
    "get_student_study_progress", "render_student_cockpit_html",
    "pre_submit_report_check", "scan_personal_results",
    # 学生端代码时光机与自动快照 (P2.2)
    "create_snapshot", "list_snapshots", "restore_snapshot",
    "compute_code_diff", "render_time_machine_html", "show_time_machine",
    # 教师端 AST 语法树代码查重 (P2.3)
    "check_code_similarity", "scan_class_code_plagiarism", "render_plagiarism_report_html",
]
