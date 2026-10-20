"""IEV CloudLab 学生管理（名册）| Student Roster Admin

平台账号由学生用学校邮箱自助注册（邮箱验证码登录），教师侧管理的是
**班级名册**：谁应该在本班、学号/班级信息、是否已结课归档。

存储：labs/data/students.json（教师/admin环境内）
字段：username(邮箱前缀), email, name, student_id, class_name,
      status(active|archived), enrolled_at, note

Hub账号核对（可选）：若环境变量 JUPYTERHUB_API_TOKEN 可用，
可调用Hub API核对"名册 vs 已登录过的真实账号"。
"""
import csv
import io
import json
import os
from datetime import datetime

DATA_ROOT = os.path.join(os.path.dirname(__file__), '..', 'data')
REGISTRY_PATH = os.path.join(DATA_ROOT, 'students.json')
STUDENT_DOMAIN = 'zhjpec.edu.cn'


def _load():
    if not os.path.exists(REGISTRY_PATH):
        return {'students': []}
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def _save(data):
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _username_from_email(email):
    email = email.strip().lower()
    if '@' not in email:
        # 允许只给前缀，自动补学校域名
        return email, f'{email}@{STUDENT_DOMAIN}'
    return email.split('@')[0], email


def add_student(email, name='', student_id='', class_name='', note=''):
    """添加一名学生到名册。返回学生dict。重复添加返回已有记录。"""
    username, full_email = _username_from_email(email)
    data = _load()
    for s in data['students']:
        if s['username'] == username:
            return s
    stu = {
        'username': username,
        'email': full_email,
        'name': name,
        'student_id': student_id,
        'class_name': class_name,
        'status': 'active',
        'enrolled_at': datetime.now().strftime('%Y-%m-%d'),
        'note': note,
    }
    data['students'].append(stu)
    _save(data)
    return stu


def import_students_csv(csv_text):
    """批量导入CSV。列：email,name,student_id,class_name（表头可中英文）。

    支持表头： email/邮箱, name/姓名, student_id/学号, class_name/班级
    返回 (成功数, 跳过数, 错误列表)。
    """
    header_map = {
        'email': 'email', '邮箱': 'email',
        'name': 'name', '姓名': 'name',
        'student_id': 'student_id', '学号': 'student_id',
        'class_name': 'class_name', '班级': 'class_name',
    }
    reader = csv.reader(io.StringIO(csv_text.strip()))
    rows = list(reader)
    if not rows:
        return 0, 0, ['CSV为空']
    headers = [header_map.get(h.strip().lower(), header_map.get(h.strip(), ''))
               for h in rows[0]]
    if 'email' not in headers:
        return 0, 0, ['CSV缺少email/邮箱列']
    ok, skip, errors = 0, 0, []
    before = len(_load()['students'])
    for i, row in enumerate(rows[1:], start=2):
        if not row or all(not c.strip() for c in row):
            continue
        rec = {}
        for h, v in zip(headers, row):
            if h:
                rec[h] = v.strip()
        if not rec.get('email'):
            errors.append(f'第{i}行：邮箱为空')
            continue
        add_student(rec.get('email', ''), rec.get('name', ''),
                    rec.get('student_id', ''), rec.get('class_name', ''))
        ok += 1
    after = len(_load()['students'])
    skip = ok - (after - before)
    return after - before, skip, errors


def update_student(username, **fields):
    """更新学生信息（name/student_id/class_name/note）。"""
    data = _load()
    for s in data['students']:
        if s['username'] == username:
            for k in ('name', 'student_id', 'class_name', 'note'):
                if k in fields:
                    s[k] = fields[k]
            _save(data)
            return s
    return None


def archive_student(username):
    """归档学生（已结课）：status -> archived，保留全部信息与成绩关联。"""
    data = _load()
    for s in data['students']:
        if s['username'] == username:
            s['status'] = 'archived'
            s['archived_at'] = datetime.now().strftime('%Y-%m-%d')
            _save(data)
            return s
    return None


def unarchive_student(username):
    data = _load()
    for s in data['students']:
        if s['username'] == username:
            s['status'] = 'active'
            s.pop('archived_at', None)
            _save(data)
            return s
    return None


def list_students(status=None, class_name=None):
    """列出学生，可按状态/班级过滤。"""
    data = _load()
    out = data['students']
    if status:
        out = [s for s in out if s['status'] == status]
    if class_name:
        out = [s for s in out if s.get('class_name') == class_name]
    return out


def roster_stats():
    students = _load()['students']
    classes = {}
    for s in students:
        c = s.get('class_name') or '(未分班)'
        classes[c] = classes.get(c, 0) + 1
    return {
        'total': len(students),
        'active': sum(1 for s in students if s['status'] == 'active'),
        'archived': sum(1 for s in students if s['status'] == 'archived'),
        'classes': classes,
    }


if __name__ == '__main__':
    print(roster_stats())
