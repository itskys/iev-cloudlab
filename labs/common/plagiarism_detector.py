"""IEV CloudLab 教师端代码 AST 语法树查重与雷同分析引擎 | AST Plagiarism Detector

功能说明：
  针对学生间修改变量名、增删无用注释、调整空行以规避传统文本查重的行为，
  基于 Python 原生抽象语法树 (AST) 进行代码骨干结构规范化、核心算法子树差分与相似度比对。

核心技术：
  1. AST 结构化清洗 (AST Structural Normalization):
     - 剥离所有注释 (Comments)、文档字符串 (Docstrings) 与格式换行差异；
     - 符号映射脱敏：将局部变量名、函数形参抽象为标准化标记 (ID_1, ID_2, ...)，使重命名无效；
  2. 核心算法子树差分抽取 (Core Algorithm Subtree Extraction):
     - 深度遍历过滤掉绘图 (plt/ax/fig)、日志打印 (print/logging) 与模块导入 (import) 等外围展示代码；
     - 提取决策分支 (If/While/For)、数学运算符 (BinOp/UnaryOp/Compare) 与控制返回值 (Return) 组成的核心计算流；
  3. 双轨融合查重与最长公共子序列 (LCS / SequenceMatcher) 判定：
     - 核心算法子树相似度 (Core Algo Sim) 与整体工程框架相似度 (Framework Sim) 双轨并进；
  4. 智能 4 级风险诊断看板 (HTML):
     - 🚨 核心算法抄袭 (CRITICAL_PLAGIARISM, 核心算法相似度 >= 85%)
     - ⚠️ 算法逻辑相似 (MODERATE_SIMILARITY, 核心算法相似度 70% ~ 84%)
     - 📘 框架自然收敛 (TEMPLATE_CONVERGENCE, 框架同源但核心算法独立，排除抄袭)
     - 🟢 独立自研 (INDEPENDENT, 核心算法相似度 < 70%)
"""

import ast
import difflib
import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple, Set


class ASTNormalizer(ast.NodeTransformer):
    """AST 访问器：消除变量名与函数名命名差异，保留纯语法结构"""

    def __init__(self):
        super().__init__()
        self.var_map = {}
        self.var_counter = 0

    def visit_Name(self, node):
        # 保留内置关键字 (True, False, None, range, len, print 等)
        if node.id in (__builtins__ if isinstance(__builtins__, dict) else dir(__builtins__)):
            return node
        if node.id not in self.var_map:
            self.var_counter += 1
            self.var_map[node.id] = f"VAR_{self.var_counter}"
        node.id = self.var_map[node.id]
        return node

    def visit_FunctionDef(self, node):
        # 匿名化函数名（除非是 __init__ 等特殊方法）
        if not node.name.startswith('__'):
            if node.name not in self.var_map:
                self.var_counter += 1
                self.var_map[node.name] = f"FUNC_{self.var_counter}"
            node.name = self.var_map[node.name]
        self.generic_visit(node)
        return node


class BoilerplateStripper(ast.NodeTransformer):
    """AST 访问器：剥离绘图、控制台打印、模块导入等脚手架代码"""

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            func = node.value.func
            attr_or_id = ''
            if isinstance(func, ast.Attribute):
                attr_or_id = func.attr
            elif isinstance(func, ast.Name):
                attr_or_id = func.id
            if attr_or_id in (
                'plot', 'show', 'figure', 'subplots', 'legend', 'xlabel', 'ylabel',
                'title', 'grid', 'print', 'clf', 'savefig', 'close', 'suptitle',
                'tight_layout', 'display', 'HTML', 'save_result'
            ):
                return None
        return node

    def visit_Import(self, node):
        return None

    def visit_ImportFrom(self, node):
        return None


def clean_ast_for_algo(tree: ast.AST) -> ast.AST:
    """从 AST 中剔除外围脚手架与展示代码"""
    stripper = BoilerplateStripper()
    cleaned = stripper.visit(tree)
    ast.fix_missing_locations(cleaned)
    return cleaned


def load_template_ast_fingerprints(exp_name: str) -> Set[Tuple[str, ...]]:
    """加载官方母版 Notebook 的所有代码单元格 AST 语法序列指纹，用于过滤课程自带模板代码"""
    clean_exp = exp_name.replace('.ipynb', '').replace('_pro', '')
    template_fp = set()

    # 1. 优先从同目录预生成的 template_fingerprints.json 读取官方母版指纹（快且不受沙箱挂载限制）
    json_cache = os.path.join(os.path.dirname(__file__), "template_fingerprints.json")
    if os.path.isfile(json_cache):
        try:
            with open(json_cache, "r", encoding="utf-8") as f:
                all_fps = json.load(f)
            if clean_exp in all_fps:
                return {tuple(seq) for seq in all_fps[clean_exp]}
        except Exception:
            pass

    # 2. 动态扫描备选母版路径
    candidates = []
    src_base = os.environ.get("IEVLAB_SRC", "/opt/ievlab/scenarios")

    candidates.append(os.path.join(src_base, "notebooks", f"{clean_exp}_pro.ipynb"))
    candidates.append(os.path.join(src_base, "notebooks", f"{clean_exp}.ipynb"))
    candidates.append(os.path.join(os.path.dirname(__file__), "..", "..", "notebooks", f"{clean_exp}_pro.ipynb"))
    candidates.append(os.path.join(os.path.dirname(__file__), "..", "..", "notebooks", f"{clean_exp}.ipynb"))

    master_path = None
    for cand in candidates:
        if os.path.exists(cand):
            master_path = cand
            break

    if not master_path:
        return template_fp

    try:
        with open(master_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for c in data.get('cells', []):
            if c.get('cell_type') == 'code':
                src = "".join(c.get('source', [])).strip()
                clean_lines = [l for l in src.splitlines() if not l.startswith(('%', '!'))]
                code = "\n".join(clean_lines).strip()
                if code:
                    seq = get_ast_sequence(code)
                    if seq:
                        template_fp.add(tuple(seq))
    except Exception:
        pass
    return template_fp


def get_ast_sequence(code_str: str) -> List[str]:
    """将 Python 源码解析为归一化的 AST 语法标记序列（保持与官方指纹库完全一致的 12 种骨干类型）"""
    if not code_str.strip():
        return []
    try:
        parsed = ast.parse(code_str)
        normalizer = ASTNormalizer()
        normalized_tree = normalizer.visit(parsed)
        ast.fix_missing_locations(normalized_tree)

        nodes = []
        for n in ast.walk(normalized_tree):
            node_type = type(n).__name__
            if node_type in ('Assign', 'BinOp', 'UnaryOp', 'Compare', 'If', 'For', 'While',
                             'Call', 'FunctionDef', 'Return', 'Attribute', 'Subscript'):
                nodes.append(node_type)
        return nodes
    except Exception:
        tokens = re.findall(r'[a-zA-Z_]\w+|==|!=|<=|>=|[+\-*/=<>]', code_str)
        return tokens


def get_core_algorithm_sequence(code_str: str) -> List[str]:
    """提取代码中纯算法决策、控制流与数学运算子树的 DFS 深度优先语法序列（剔除外围展示代码）"""
    if not code_str.strip():
        return []
    try:
        parsed = ast.parse(code_str)
        cleaned_tree = clean_ast_for_algo(parsed)
        normalizer = ASTNormalizer()
        normalized_tree = normalizer.visit(cleaned_tree)
        ast.fix_missing_locations(normalized_tree)
    except Exception:
        # 容错：退化为控制流与运算符匹配
        return [tok for tok in re.findall(r'[+\-*/=<>!]+|\b(?:if|while|for|return|break|continue)\b', code_str)]

    tokens = []

    def _dfs_collect(node):
        if node is None:
            return

        node_type = type(node).__name__
        if node_type in ('If', 'While', 'For', 'Return', 'BinOp', 'UnaryOp', 'Compare', 'AugAssign', 'Subscript'):
            tokens.append(node_type)
        elif node_type in ('Add', 'Sub', 'Mult', 'Div', 'FloorDiv', 'Mod', 'Pow', 'Lt', 'Gt', 'LtE', 'GtE', 'Eq', 'NotEq'):
            tokens.append(node_type)

        for child in ast.iter_child_nodes(node):
            _dfs_collect(child)

    _dfs_collect(normalized_tree)
    return tokens


def calculate_jaccard_similarity(seq_a: List[str], seq_b: List[str], n_gram: int = 3) -> float:
    """基于 N-Gram 语法指纹计算 Jaccard 相似度 (0.0 ~ 1.0)"""
    if not seq_a or not seq_b:
        return 0.0

    if len(seq_a) < n_gram or len(seq_b) < n_gram:
        set_a = set(seq_a)
        set_b = set(seq_b)
    else:
        set_a = set(tuple(seq_a[i:i+n_gram]) for i in range(len(seq_a) - n_gram + 1))
        set_b = set(tuple(seq_b[i:i+n_gram]) for i in range(len(seq_b) - n_gram + 1))

    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))

    if union == 0:
        return 0.0
    return round(intersection / union, 3)


def calculate_sequence_ratio(seq_a: List[str], seq_b: List[str]) -> float:
    """基于最长公共子序列 (LCS) 计算语法序列的编辑距离匹配比率 (0.0 ~ 1.0)"""
    if not seq_a or not seq_b:
        return 0.0
    matcher = difflib.SequenceMatcher(None, seq_a, seq_b)
    return round(matcher.ratio(), 3)


def extract_custom_code_profiles(
    nb_path: str,
    template_fp: Optional[Set[Tuple[str, ...]]] = None
) -> Dict[str, Any]:
    """提取学生在 Notebook 中自主编写或实质性修改的代码单元格特征（含整体 AST 与核心算法子树）。"""
    if not os.path.exists(nb_path):
        return {'custom_nodes': [], 'custom_core_nodes': [], 'is_unmodified': True}
    try:
        with open(nb_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cells = data.get('cells', [])
        custom_nodes = []
        custom_core_nodes = []
        has_any_code = False
        has_custom_code = False

        for c in cells:
            if c.get('cell_type') == 'code':
                src = "".join(c.get('source', [])).strip()
                clean_lines = [l for l in src.splitlines() if not l.startswith(('%', '!'))]
                code = "\n".join(clean_lines).strip()
                if not code:
                    continue
                has_any_code = True
                seq = get_ast_sequence(code)
                if not seq:
                    continue

                # 若与母版任一单元格 AST 结构指纹完全一致，说明是课程自带模板，排除出查重池
                if template_fp and tuple(seq) in template_fp:
                    continue

                has_custom_code = True
                custom_nodes.extend(seq)
                core_seq = get_core_algorithm_sequence(code)
                custom_core_nodes.extend(core_seq)

        if not has_any_code or not has_custom_code:
            return {'custom_nodes': [], 'custom_core_nodes': [], 'is_unmodified': True}
        return {
            'custom_nodes': custom_nodes,
            'custom_core_nodes': custom_core_nodes,
            'is_unmodified': False
        }
    except Exception:
        return {'custom_nodes': [], 'custom_core_nodes': [], 'is_unmodified': True}


def extract_custom_ast_sequence(nb_path: str, template_fp: Optional[Set[Tuple[str, ...]]] = None) -> Tuple[List[str], bool]:
    """保持向后兼容：提取学生在 Notebook 中自主编写的代码单元格 AST 序列。"""
    prof = extract_custom_code_profiles(nb_path, template_fp)
    return prof['custom_nodes'], prof['is_unmodified']


def extract_code_from_notebook(nb_path: str) -> str:
    """提取 Notebook 中所有非空 Python 代码单元格源码"""
    if not os.path.exists(nb_path):
        return ""
    try:
        with open(nb_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cells = data.get('cells', [])
        code_blocks = []
        for c in cells:
            if c.get('cell_type') == 'code':
                src = "".join(c.get('source', [])).strip()
                clean_lines = [l for l in src.splitlines() if not l.startswith(('%', '!'))]
                if clean_lines:
                    code_blocks.append("\n".join(clean_lines))
        return "\n\n".join(code_blocks)
    except Exception:
        return ""


def check_code_similarity(code_a: str, code_b: str) -> Dict[str, Any]:
    """比对两段代码的 AST 结构与核心算法子树相似度"""
    # 整体 AST 比对
    seq_a = get_ast_sequence(code_a)
    seq_b = get_ast_sequence(code_b)
    overall_jaccard = calculate_jaccard_similarity(seq_a, seq_b, n_gram=3)
    overall_pct = overall_jaccard * 100.0

    # 核心算法子树比对
    core_a = get_core_algorithm_sequence(code_a)
    core_b = get_core_algorithm_sequence(code_b)

    if core_a and core_b:
        core_jaccard = calculate_jaccard_similarity(core_a, core_b, n_gram=2)
        core_ratio = calculate_sequence_ratio(core_a, core_b)
        core_pct = round((0.3 * core_jaccard + 0.7 * core_ratio) * 100.0, 1)
    else:
        core_pct = 0.0

    if core_pct >= 85.0:
        status = 'CRITICAL_PLAGIARISM'
        desc = f'高度雷同：核心决策算法与数学运算流几乎完全吻合 ({core_pct:.1f}%)，存在重大抄袭嫌疑。'
    elif core_pct >= 70.0:
        status = 'MODERATE_SIMILARITY'
        desc = f'中度相似：核心控制结构与算法主干逻辑相近 ({core_pct:.1f}%)，建议重点复核。'
    elif overall_pct >= 65.0 and core_pct < 55.0:
        status = 'TEMPLATE_CONVERGENCE'
        desc = f'框架自然收敛：整体模板骨架同源 ({overall_pct:.1f}%)，但核心算法子树独立自研 ({core_pct:.1f}%)，排除抄袭。'
    else:
        status = 'INDEPENDENT'
        desc = f'独立完成：代码语法结构与算法子树具有显著差异 (算法相似度 {core_pct:.1f}%)。'

    return {
        'similarity_pct': core_pct,
        'core_algo_pct': core_pct,
        'overall_pct': round(overall_pct, 1),
        'status': status,
        'description': desc,
        'nodes_count': (len(core_a), len(core_b)),
    }


def scan_class_code_plagiarism(
    homes_base: str = '/opt/ievlab/home',
    exp_name: str = 'A1_cutin_aeb',
) -> Dict[str, Any]:
    """在全班学生目录下批量扫描指定实验的代码相似度矩阵。
    基于母版指纹自动过滤课程自带模板与纯标量参数微调，区分核心控制算法与外层脚手架。
    """
    if not os.path.exists(homes_base):
        return {'exp_name': exp_name, 'n_students': 0, 'flagged_count': 0, 'pairs': []}

    template_fps = load_template_ast_fingerprints(exp_name)

    student_profiles = {}
    unmodified_students = set()
    users = sorted(os.listdir(homes_base))

    for u in users:
        if u in ('admin', 'teacher', 'lost+found') or u.startswith('.'):
            continue
        u_nb_dir = os.path.join(homes_base, u, 'notebooks')
        if not os.path.exists(u_nb_dir):
            continue

        target_nb = None
        for cand in [f"{exp_name}_pro.ipynb", f"{exp_name}.ipynb"]:
            p = os.path.join(u_nb_dir, cand)
            if os.path.exists(p):
                target_nb = p
                break

        if target_nb:
            prof = extract_custom_code_profiles(target_nb, template_fps)
            if prof['is_unmodified'] or len(prof['custom_nodes']) < 3:
                unmodified_students.add(u)
                student_profiles[u] = {'custom_nodes': [], 'custom_core_nodes': [], 'is_unmodified': True}
            else:
                student_profiles[u] = prof

    student_list = list(student_profiles.keys())
    n = len(student_list)
    flagged_pairs = []

    # 两两比对
    for i in range(n):
        for j in range(i + 1, n):
            u1 = student_list[i]
            u2 = student_list[j]
            p1 = student_profiles[u1]
            p2 = student_profiles[u2]

            # 核心防误判规则：若任一方为标准母版跟跑，不计入雷同抄袭预警
            if p1['is_unmodified'] or p2['is_unmodified']:
                continue

            core_a = p1['custom_core_nodes']
            core_b = p2['custom_core_nodes']
            all_a = p1['custom_nodes']
            all_b = p2['custom_nodes']

            overall_sim = round(calculate_jaccard_similarity(all_a, all_b, n_gram=3) * 100.0, 1)

            if core_a and core_b:
                core_jaccard = calculate_jaccard_similarity(core_a, core_b, n_gram=2)
                core_ratio = calculate_sequence_ratio(core_a, core_b)
                core_sim = round((0.3 * core_jaccard + 0.7 * core_ratio) * 100.0, 1)
            else:
                core_sim = 0.0

            if core_sim >= 85.0:
                st = 'CRITICAL_PLAGIARISM'
                desc = f'高度雷同：核心控制决策与数学运算子树几乎完全吻合 ({core_sim:.1f}%)，存在重大抄袭嫌疑。'
            elif core_sim >= 70.0:
                st = 'MODERATE_SIMILARITY'
                desc = f'中度相似：核心算法逻辑与控制结构相近 ({core_sim:.1f}%)，建议重点复核。'
            elif overall_sim >= 65.0 and core_sim < 55.0:
                st = 'TEMPLATE_CONVERGENCE'
                desc = f'框架自然收敛：整体工程框架同源 ({overall_sim:.1f}%)，但核心算法独立编写 ({core_sim:.1f}%)，排除抄袭。'
            else:
                st = 'INDEPENDENT'
                desc = f'独立完成：算法子树结构具有显著独创性 ({core_sim:.1f}%)。'

            # 记录需要展示的记录：疑似抄袭、算法相近，或框架高度同源需要告知教师的对
            if core_sim >= 65.0 or (overall_sim >= 75.0 and core_sim >= 40.0):
                flagged_pairs.append({
                    'student_a': u1,
                    'student_b': u2,
                    'similarity_pct': core_sim,
                    'overall_similarity_pct': overall_sim,
                    'status': st,
                    'description': desc,
                })

    flagged_pairs.sort(key=lambda x: x['similarity_pct'], reverse=True)

    return {
        'exp_name': exp_name,
        'n_students': n,
        'n_custom_authors': n - len(unmodified_students),
        'n_template_baseline': len(unmodified_students),
        'flagged_count': len([p for p in flagged_pairs if p['status'] in ('CRITICAL_PLAGIARISM', 'MODERATE_SIMILARITY')]),
        'total_analyzed_pairs': len(flagged_pairs),
        'pairs': flagged_pairs,
    }


def render_plagiarism_report_html(report: Dict[str, Any]) -> str:
    """生成具备现代工程质感、4级状态胶囊的教师面板代码查重警报看板 (HTML)"""
    exp = report.get('exp_name', '未知实验')
    n_stu = report.get('n_students', 0)
    pairs = report.get('pairs', [])
    n_base = report.get('n_template_baseline', 0)
    n_cust = report.get('n_custom_authors', 0)
    n_flagged = report.get('flagged_count', 0)

    if not pairs or n_flagged == 0:
        return f"""
        <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 10px; padding: 16px 20px; margin: 12px 0; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <strong style="color: #15803d; font-size: 15px;">✅ 【{exp}】全班代码 AST 语法树查重健康</strong>
                    <p style="margin: 4px 0 0 0; color: #4b5563; font-size: 13px;">
                        共比对 <b>{n_stu}</b> 名学生提交的实验课件（已自动分离母版脚手架：<b>{n_base}</b> 人标准模板跟跑，<b>{n_cust}</b> 人含自主编写算法），未发现异常算法雷同。
                    </p>
                </div>
                <span style="background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 14px; font-size: 12px; font-weight: 700;">
                    学术防线正常
                </span>
            </div>
        </div>
        """

    rows = ""
    for p in pairs:
        st = p['status']
        if st == 'CRITICAL_PLAGIARISM':
            badge = '<span style="background: #fef2f2; color: #dc2626; border: 1px solid #f87171; padding: 3px 10px; border-radius: 6px; font-weight: 700; font-size: 11px;">🚨 疑似抄袭</span>'
            color_sim = "#dc2626"
        elif st == 'MODERATE_SIMILARITY':
            badge = '<span style="background: #fffbeb; color: #d97706; border: 1px solid #fcd34d; padding: 3px 10px; border-radius: 6px; font-weight: 700; font-size: 11px;">⚠️ 逻辑雷同</span>'
            color_sim = "#d97706"
        elif st == 'TEMPLATE_CONVERGENCE':
            badge = '<span style="background: #eff6ff; color: #2563eb; border: 1px solid #93c5fd; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 11px;">📘 框架同源(算法独立)</span>'
            color_sim = "#2563eb"
        else:
            badge = '<span style="background: #f0fdf4; color: #16a34a; border: 1px solid #86efac; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 11px;">🟢 独立自研</span>'
            color_sim = "#16a34a"

        rows += f"""
        <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='white'">
            <td style="padding: 10px 14px; font-weight: 600; color: #0f172a; font-family: monospace;">{p['student_a']} ↔ {p['student_b']}</td>
            <td style="padding: 10px 14px; font-weight: 700; color: {color_sim}; font-size: 14px;">{p['similarity_pct']:.1f}%</td>
            <td style="padding: 10px 14px; color: #64748b; font-size: 12px;">{p.get('overall_similarity_pct', '--')}%</td>
            <td style="padding: 10px 14px;">{badge}</td>
            <td style="padding: 10px 14px; font-size: 12px; color: #334155;">{p['description']}</td>
        </tr>
        """

    html = f"""
    <div style="background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 18px; margin: 14px 0; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; margin-bottom: 14px;">
            <div>
                <h4 style="margin: 0; color: #0f172a; font-size: 16px; font-weight: 700;">
                    🛡️ 代码 AST 语法树子树差分查重预警: {exp} ({n_stu} 名学生)
                </h4>
                <p style="margin: 4px 0 0 0; color: #64748b; font-size: 12px;">
                    剥离绘图与打印脚手架，精准比对核心决策与数学运算流，有效消除模板同源引起的假警报
                </p>
            </div>
            <div style="text-align: right;">
                <span style="background: #fef2f2; border: 1px solid #fca5a5; color: #b91c1c; padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: 700;">
                    预警 {n_flagged} 组异常雷同
                </span>
            </div>
        </div>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                <thead>
                    <tr style="background: #f8fafc; color: #475569; border-bottom: 1px solid #e2e8f0; font-weight: 600;">
                        <th style="padding: 10px 14px;">比对学生对 (Pair)</th>
                        <th style="padding: 10px 14px;">核心算法雷同度 (Core Algo)</th>
                        <th style="padding: 10px 14px;">工程框架相似度</th>
                        <th style="padding: 10px 14px;">风险诊断级别</th>
                        <th style="padding: 10px 14px;">诊断说明与复核建议</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    </div>
    """
    return html
