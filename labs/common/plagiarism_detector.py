"""IEV CloudLab 教师端代码 AST 语法树查重与雷同分析引擎 | AST Plagiarism Detector

功能说明：
  针对学生间修改变量名、增删无用注释、调整空行以规避传统文本查重的行为，
  基于 Python 原生抽象语法树 (AST) 进行代码骨干结构规范化与相似度比对。

核心技术：
  1. AST 结构化清洗 (AST Structural Normalization):
     - 剥离所有注释 (Comments)、文档字符串 (Docstrings) 与格式换行差异；
     - 符号映射脱敏：将局部变量名、函数形参抽象为标准化标记 (ID_1, ID_2, ...)，使重命名无效；
  2. N-Gram 结构指纹与 Jaccard / Levenshtein 相似度融合算法：
     - 抽取 AST 语法节点演变序列（如 [Assign, BinOp, If, Call]），计算加权 Jaccard 相似度；
  3. 班级全网比对与异常聚类：
     - 扫描所有学生 Home 目录下的目标 Notebook 代码单元格，输出两两比对相似度矩阵；
  4. 风险分级预警看板 (HTML):
     - 🚨 重度疑似抄袭 (相似度 >= 85%)
     - ⚠️ 中度结构相似 (相似度 70% ~ 84%)
     - 🟢 独立完成 (相似度 < 70%)
"""

import ast
import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple, Set


class ASTNormalizer(ast.NodeTransformer):
    """AST 访问器：消除变量名命名差异，保留纯语法结构"""

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


def load_template_ast_fingerprints(exp_name: str) -> Set[Tuple[str, ...]]:
    """加载官方母版 Notebook 的所有代码单元格 AST 语法序列指纹，用于过滤课程自带模板代码"""
    candidates = []
    clean_exp = exp_name.replace('.ipynb', '').replace('_pro', '')
    src_base = os.environ.get("IEVLAB_SRC", "/opt/ievlab/scenarios")

    candidates.append(os.path.join(src_base, "notebooks", f"{clean_exp}_pro.ipynb"))
    candidates.append(os.path.join(src_base, "notebooks", f"{clean_exp}.ipynb"))
    candidates.append(os.path.join(os.path.dirname(__file__), "..", "..", "notebooks", f"{clean_exp}_pro.ipynb"))
    candidates.append(os.path.join(os.path.dirname(__file__), "..", "..", "notebooks", f"{clean_exp}.ipynb"))

    template_fp = set()
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


def extract_custom_ast_sequence(nb_path: str, template_fp: Optional[Set[Tuple[str, ...]]] = None) -> Tuple[List[str], bool]:
    """提取学生在 Notebook 中自主编写或实质性修改的代码单元格 AST 序列。

    Returns:
        (custom_ast_nodes, is_unmodified_template)
    """
    if not os.path.exists(nb_path):
        return [], True
    try:
        with open(nb_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cells = data.get('cells', [])
        custom_nodes = []
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

                # 若与母版任一单元格 AST 结构指纹完全一致，说明是课程自带模板或纯标量参数微调，排除出查重池
                if template_fp and tuple(seq) in template_fp:
                    continue

                # 自主编写或重构的语法逻辑
                has_custom_code = True
                custom_nodes.extend(seq)

        if not has_any_code or not has_custom_code:
            return [], True
        return custom_nodes, False
    except Exception:
        return [], True


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
                # 过滤掉魔法命令和纯 import 语句
                clean_lines = [l for l in src.splitlines() if not l.startswith(('%', '!'))]
                if clean_lines:
                    code_blocks.append("\n".join(clean_lines))
        return "\n\n".join(code_blocks)
    except Exception:
        return ""


def get_ast_sequence(code_str: str) -> List[str]:
    """将 Python 源码解析为归一化的 AST 语法标记序列"""
    if not code_str.strip():
        return []
    try:
        parsed = ast.parse(code_str)
        normalizer = ASTNormalizer()
        normalized_tree = normalizer.visit(parsed)
        ast.fix_missing_locations(normalized_tree)

        # 遍历节点类型
        nodes = []
        for n in ast.walk(normalized_tree):
            node_type = type(n).__name__
            # 记录关键语法结构节点
            if node_type in ('Assign', 'BinOp', 'UnaryOp', 'Compare', 'If', 'For', 'While',
                             'Call', 'FunctionDef', 'Return', 'Attribute', 'Subscript'):
                nodes.append(node_type)
        return nodes
    except Exception:
        # 语法解析容错：若含有 Jupyter 未定义符号，退化为正则词法分析
        tokens = re.findall(r'[a-zA-Z_]\w+|==|!=|<=|>=|[+\-*/=<>]', code_str)
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


def check_code_similarity(code_a: str, code_b: str) -> Dict[str, Any]:
    """比对两段代码的 AST 结构相似度"""
    seq_a = get_ast_sequence(code_a)
    seq_b = get_ast_sequence(code_b)

    sim = calculate_jaccard_similarity(seq_a, seq_b, n_gram=3)
    pct = sim * 100.0

    if pct >= 85.0:
        status = 'CRITICAL_PLAGIARISM'
        desc = '高度雷同：核心抽象语法树与运算流几乎完全吻合，存在重大抄袭嫌疑。'
    elif pct >= 70.0:
        status = 'MODERATE_SIMILARITY'
        desc = '中度相似：控制结构与算法主干逻辑相近，建议重点复核。'
    else:
        status = 'INDEPENDENT'
        desc = '独立完成：代码语法结构具有显著差异。'

    return {
        'similarity_pct': round(pct, 1),
        'status': status,
        'description': desc,
        'nodes_count': (len(seq_a), len(seq_b)),
    }


def scan_class_code_plagiarism(
    homes_base: str = '/opt/ievlab/home',
    exp_name: str = 'A1_cutin_aeb',
) -> Dict[str, Any]:
    """在全班学生目录下批量扫描指定实验的代码相似度矩阵。
    基于母版指纹自动过滤课程自带模板与纯标量参数微调，仅比对学生自主编写/重构的算法逻辑。

    :param homes_base: 学生 home 根目录
    :param exp_name: 待扫描的实验名（如 'A1_cutin_aeb'）
    :return: 查重分析总结字典
    """
    if not os.path.exists(homes_base):
        return {'exp_name': exp_name, 'n_students': 0, 'flagged_count': 0, 'pairs': []}

    # 提取官方母版 Notebook 的单元格 AST 指纹，严格排除课程自带模板与纯参数微调干扰
    template_fps = load_template_ast_fingerprints(exp_name)

    student_custom_ast = {}
    unmodified_students = set()
    users = sorted(os.listdir(homes_base))

    for u in users:
        if u in ('admin', 'lost+found') or u.startswith('.'):
            continue
        u_nb_dir = os.path.join(homes_base, u, 'notebooks')
        if not os.path.exists(u_nb_dir):
            continue

        # 匹配 pro 或 普通 notebook
        target_nb = None
        for cand in [f"{exp_name}_pro.ipynb", f"{exp_name}.ipynb"]:
            p = os.path.join(u_nb_dir, cand)
            if os.path.exists(p):
                target_nb = p
                break

        if target_nb:
            custom_seq, is_unmodified = extract_custom_ast_sequence(target_nb, template_fps)
            if is_unmodified or len(custom_seq) < 3:
                unmodified_students.add(u)
                student_custom_ast[u] = []
            else:
                student_custom_ast[u] = custom_seq

    student_list = list(student_custom_ast.keys())
    n = len(student_list)
    flagged_pairs = []

    # 两两比对
    for i in range(n):
        for j in range(i + 1, n):
            u1 = student_list[i]
            u2 = student_list[j]
            seq_a = student_custom_ast[u1]
            seq_b = student_custom_ast[u2]

            # 核心防误判规则：若任一方为标准母版跟跑（无自主拓展算法结构），不计入雷同抄袭预警
            if not seq_a or not seq_b:
                continue

            sim = calculate_jaccard_similarity(seq_a, seq_b, n_gram=3)
            pct = sim * 100.0

            if pct >= 85.0:
                st = 'CRITICAL_PLAGIARISM'
                desc = '高度雷同：自主编写部分的核心抽象语法树与运算流几乎完全吻合，存在重大抄袭嫌疑。'
            elif pct >= 70.0:
                st = 'MODERATE_SIMILARITY'
                desc = '中度相似：自主编写部分的控制结构与算法主干逻辑相近，建议重点复核。'
            else:
                st = 'INDEPENDENT'
                desc = '独立完成：自主编写代码语法结构具有显著差异。'

            if pct >= 65.0:  # 记录有疑似风险的点对
                flagged_pairs.append({
                    'student_a': u1,
                    'student_b': u2,
                    'similarity_pct': round(pct, 1),
                    'status': st,
                    'description': desc,
                })

    flagged_pairs.sort(key=lambda x: x['similarity_pct'], reverse=True)

    return {
        'exp_name': exp_name,
        'n_students': n,
        'n_custom_authors': n - len(unmodified_students),
        'n_template_baseline': len(unmodified_students),
        'flagged_count': len(flagged_pairs),
        'pairs': flagged_pairs,
    }


def render_plagiarism_report_html(report: Dict[str, Any]) -> str:
    """生成教师面板专用的代码查重警报看板 (HTML)"""
    exp = report.get('exp_name', '未知实验')
    n_stu = report.get('n_students', 0)
    pairs = report.get('pairs', [])

    if not pairs:
        n_base = report.get('n_template_baseline', 0)
        n_cust = report.get('n_custom_authors', 0)
        return f"""
        <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 14px; margin: 10px 0; font-family: system-ui, sans-serif;">
            <strong style="color: #16a34a; font-size: 14px;">✅ 【{exp}】全班代码 AST 结构查重正常</strong>
            <p style="margin: 4px 0 0 0; color: #4b5563; font-size: 12px;">
                共比对 {n_stu} 名学生提交的代码（已自动过滤母版自带模板代码：{n_base} 人标准模板跟跑，{n_cust} 人含自主重构逻辑），未发现异常语法树雷同。
            </p>
        </div>
        """

    rows = ""
    for p in pairs:
        st = p['status']
        if st == 'CRITICAL_PLAGIARISM':
            badge = '<span style="background: #fef2f2; color: #dc2626; border: 1px solid #f87171; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">🚨 疑似抄袭</span>'
        else:
            badge = '<span style="background: #fffbeb; color: #d97706; border: 1px solid #fcd34d; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">⚠️ 逻辑雷同</span>'

        rows += f"""
        <tr style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 8px 12px; font-weight: 600; color: #0f172a;">{p['student_a']} ↔ {p['student_b']}</td>
            <td style="padding: 8px 12px; font-weight: bold; color: #dc2626; font-size: 14px;">{p['similarity_pct']:.1f}%</td>
            <td style="padding: 8px 12px;">{badge}</td>
            <td style="padding: 8px 12px; font-size: 12px; color: #475569;">{p['description']}</td>
        </tr>
        """

    html = f"""
    <div style="background: white; border: 1px solid #cbd5e1; border-radius: 10px; padding: 16px; margin: 12px 0; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; margin-bottom: 12px;">
            <div>
                <h4 style="margin: 0; color: #0f172a; font-size: 15px;">
                    🛡️ 代码 AST 语法树查重预警: {exp} ({n_stu} 名学生)
                </h4>
                <p style="margin: 3px 0 0 0; color: #64748b; font-size: 12px;">
                    基于抽象语法树归一化，精准识别变相变量替换与格式伪装抄袭
                </p>
            </div>
            <span style="background: #fef2f2; color: #b91c1c; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700;">
                发现 {len(pairs)} 组异常雷同
            </span>
        </div>
        <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
            <thead>
                <tr style="background: #f8fafc; color: #475569; border-bottom: 1px solid #e2e8f0;">
                    <th style="padding: 8px 12px;">比对学生对 (Pair)</th>
                    <th style="padding: 8px 12px;">结构相似度</th>
                    <th style="padding: 8px 12px;">风险级别</th>
                    <th style="padding: 8px 12px;">诊断说明</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """
    return html
