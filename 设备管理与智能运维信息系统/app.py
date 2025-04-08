from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json, os, sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
DATA_FILE = 'data/storage.json'
DATABASE = 'data/inspection.db'

# === JSON 数据相关 ===
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "base_info": {
                    "line_equip": [],
                    "material": [],
                    "inspection_route": [],
                    "position_id": [],
                    "inspection_standard": []
                },
                "check_task": [],
                "repair_order": []
            }, f, ensure_ascii=False, indent=4)
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# === SQLite 数据库相关 ===
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs('data', exist_ok=True)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS inspection_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit TEXT NOT NULL,
            seq INTEGER,
            device_name TEXT,
            check_part TEXT,
            check_item TEXT,
            standard TEXT,
            check_result TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS inspection_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit TEXT NOT NULL,
            seq INTEGER,
            device_name TEXT,
            check_part TEXT,
            check_item TEXT,
            standard TEXT,
            check_result TEXT,
            record_time TEXT
        )
    ''')
    conn.commit()
    cur.execute("SELECT COUNT(*) as count FROM inspection_items")
    count = cur.fetchone()['count']
    if count == 0:
        predata = {
            "四轴机器人单元": [
                {"seq": 1, "device_name": "断路器", "check_part": "本体", "check_item": "状态检查", "standard": "触点接线牢靠，无放电、裂纹现象"},
                {"seq": 2, "device_name": "托盘上料模块", "check_part": "气缸运行", "check_item": "状态检查", "standard": "将托盘正常输送到装配位置"}
                # …其它数据…
            ]
        }
        for unit, items in predata.items():
            for item in items:
                cur.execute(
                    'INSERT INTO inspection_items (unit, seq, device_name, check_part, check_item, standard, check_result) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (unit, item.get("seq"), item.get("device_name"), item.get("check_part"), item.get("check_item"), item.get("standard"), "")
                )
        conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/base-info', methods=['GET', 'POST'])
def base_info():
    data = load_data()
    section = request.args.get('section', 'line_equip')
    if request.method == 'POST':
        if section == 'line_equip':
            entry = {
                'line_code': request.form.get('line_code', ''),
                'device_code': request.form.get('device_code', '')
            }
            data["base_info"]["line_equip"].append(entry)
        elif section == 'material':
            entry = {
                'unit': request.form.get('unit', ''),
                'spare': request.form.get('spare', ''),
                'tool': request.form.get('tool', '')
            }
            data["base_info"]["material"].append(entry)
        elif section == 'inspection_route':
            entry = {
                'route_name': request.form.get('route_name'),
                'route_code': request.form.get('route_code'),
                'device_code': request.form.get('device_code'),
                'device_name': request.form.get('device_name')
            }
            data["base_info"]["inspection_route"].append(entry)
        elif section == 'position_id':
            entry = {
                'position_id': request.form.get('position_id', ''),
                'position': request.form.get('position', ''),
                'position_type': request.form.get('position_type', ''),
                'position_category': request.form.get('position_category', '')
            }
            data["base_info"]["position_id"].append(entry)
        elif section == 'inspection_standard':
            entry = {
                'serial': request.form.get('serial'),
                'device_name': request.form.get('device_name'),
                'check_part': request.form.get('check_part'),
                'check_content': request.form.get('check_content'),
                'standard': request.form.get('standard')
            }
            data["base_info"]["inspection_standard"].append(entry)
        save_data(data)
        return redirect(url_for('base_info', section=section))
    return render_template('base_info.html', section=section, data=data["base_info"])

@app.route('/delete/base-info/<section>/<int:index>')
def delete_base_info(section, index):
    data = load_data()
    if section in data["base_info"] and 0 <= index < len(data["base_info"][section]):
        data["base_info"][section].pop(index)
        save_data(data)
    return redirect(url_for('base_info', section=section))

# ===== 设备检维修模块 =====

# 显示工单列表页面，同时将工单数据以 JSON 传给前端（用于批量模态对话框）
@app.route('/repair-order', methods=['GET'])
def repair_order():
    data = load_data()
    return render_template('repair_order.html', orders=data["repair_order"])

# 添加工单：点击“送审”按钮后，状态置为“待审核”
@app.route('/repair-order/add', methods=['POST'])
def add_repair_order():
    data = load_data()
    entry = {
        'order_name': request.form.get('order_name'),
        'specialty': request.form.get('specialty'),
        'repair_category': request.form.get('repair_category'),
        'task_type': request.form.get('task_type'),
        'project_category': request.form.get('project_category'),
        'acceptance_level': request.form.get('acceptance_level'),
        'commission_type': request.form.get('commission_type'),
        'affect_production': request.form.get('affect_production'),
        'repair_time': request.form.get('repair_time'),
        'repair_content': request.form.get('repair_content'),
        'spare': request.form.get('spare'),
        'tool': request.form.get('tool'),
        'status': '待审核'
    }
    data["repair_order"].append(entry)
    save_data(data)
    return redirect(url_for('repair_order'))

# 单个订单直接操作（不弹对话框）：根据当前状态直接更新订单状态
@app.route('/repair-order/direct_update/<int:index>/<action>')
def direct_update_repair_order(index, action):
    data = load_data()
    if 0 <= index < len(data["repair_order"]):
        order = data["repair_order"][index]
        if action == 'review' and order.get('status') == '待审核':
            order['status'] = '已审核'
        elif action == 'implement' and order.get('status') == '已审核':
            order['status'] = '已实施'
        elif action == 'accept' and order.get('status') == '已实施':
            order['status'] = '已验收'
        elif action == 'actual' and order.get('status') == '已验收':
            order['status'] = '已实绩录入'
        save_data(data)
    return redirect(url_for('repair_order'))

# 批量更新（批量操作弹出对话框）：更新所有选中订单
@app.route('/repair-order/batch_update_dialog', methods=['POST'])
def batch_update_repair_order_dialog():
    data = load_data()
    order_indexes = request.form.get('order_indexes')
    if order_indexes:
        indexes = [int(x) for x in order_indexes.split(',')]
        action = request.form.get('action_type')
        # 对于批量更新，统一使用批量对话框中填写的12项内容
        for i in indexes:
            if 0 <= i < len(data["repair_order"]):
                order = data["repair_order"][i]
                order['order_name'] = request.form.get('order_name')
                order['specialty'] = request.form.get('specialty')
                order['repair_category'] = request.form.get('repair_category')
                order['task_type'] = request.form.get('task_type')
                order['project_category'] = request.form.get('project_category')
                order['acceptance_level'] = request.form.get('acceptance_level')
                order['commission_type'] = request.form.get('commission_type')
                order['affect_production'] = request.form.get('affect_production')
                order['repair_time'] = request.form.get('repair_time')
                order['repair_content'] = request.form.get('repair_content')
                order['spare'] = request.form.get('spare')
                order['tool'] = request.form.get('tool')
                if action == 'review' and order.get('status') == '待审核':
                    order['status'] = '已审核'
                elif action == 'implement' and order.get('status') == '已审核':
                    order['status'] = '已实施'
                elif action == 'accept' and order.get('status') == '已实施':
                    order['status'] = '已验收'
                elif action == 'actual' and order.get('status') == '已验收':
                    order['status'] = '已实绩录入'
        save_data(data)
    return redirect(url_for('repair_order'))

# 删除订单（修正路由参数格式）
@app.route('/delete/repair-order/<int:index>')
def delete_repair_order(index):
    data = load_data()
    if 0 <= index < len(data["repair_order"]):
        data["repair_order"].pop(index)
        save_data(data)
    return redirect(url_for('repair_order'))

# ===== 以下其它模块代码保持不变 =====

@app.route('/check-task', methods=['GET', 'POST'])
def check_task():
    conn = get_db_connection()
    cur = conn.cursor()
    if 'check_task_visited' not in session:
        session['check_task_visited'] = True
        session['expanded_units'] = []
    if request.method == 'POST' and 'item_id' in request.form:
        item_id = request.form.get('item_id')
        check_result = request.form.get('check_result')
        if item_id:
            cur.execute('UPDATE inspection_items SET check_result=? WHERE id=?', (check_result, item_id))
            cur.execute('SELECT * FROM inspection_items WHERE id=?', (item_id,))
            item = cur.fetchone()
            if item:
                record_time = datetime.now().strftime('%Y-%m-%d')
                cur.execute(
                    'INSERT INTO inspection_records (unit, seq, device_name, check_part, check_item, standard, check_result, record_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (item['unit'], item['seq'], item['device_name'], item['check_part'], item['check_item'], item['standard'], check_result, record_time)
                )
            conn.commit()
    cur.execute('SELECT * FROM inspection_items ORDER BY unit, seq')
    items = cur.fetchall()
    conn.close()
    units = {}
    for item in items:
        unit = item['unit']
        units.setdefault(unit, []).append(item)
    return render_template('check_task.html', units=units, expanded_units=session.get('expanded_units', []))

@app.route('/toggle-unit', methods=['POST'])
def toggle_unit():
    unit = request.form.get('unit')
    if not unit:
        return jsonify({'status': 'error', 'message': 'No unit provided'}), 400
    expanded_units = session.get('expanded_units', [])
    if unit in expanded_units:
        expanded_units.remove(unit)
        is_expanded = False
    else:
        expanded_units.append(unit)
        is_expanded = True
    session['expanded_units'] = expanded_units
    return jsonify({'status': 'success', 'is_expanded': is_expanded})

@app.route('/add_item', methods=['POST'])
def add_item():
    unit = request.form.get('unit')
    seq = request.form.get('seq')
    device_name = request.form.get('device_name')
    check_part = request.form.get('check_part')
    check_item = request.form.get('check_item')
    standard = request.form.get('standard')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO inspection_items (unit, seq, device_name, check_part, check_item, standard, check_result) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (unit, seq, device_name, check_part, check_item, standard, "")
    )
    conn.commit()
    conn.close()
    return redirect(url_for('check_task'))

@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM inspection_items WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('check_task'))

@app.route('/check-record', methods=['GET', 'POST'])
def check_record():
    conn = get_db_connection()
    cur = conn.cursor()

    filters = {
        'unit': request.form.get('unit', ''),
        'seq': request.form.get('seq', ''),
        'device_name': request.form.get('device_name', ''),
        'check_part': request.form.get('check_part', ''),
        'check_item': request.form.get('check_item', ''),
        'standard': request.form.get('standard', ''),
        'check_result': request.form.get('check_result', ''),
        'record_time': request.form.get('record_time', '')
    }

    query = 'SELECT * FROM inspection_records WHERE 1=1'
    params = []
    for field, value in filters.items():
        if value:
            query += f' AND {field} = ?'
            params.append(value)
    query += ' ORDER BY record_time DESC, unit, seq'
    cur.execute(query, params)
    records = cur.fetchall()

    options = {
        'unit': [row['unit'] for row in cur.execute('SELECT DISTINCT unit FROM inspection_records ORDER BY unit').fetchall()],
        'seq': [row['seq'] for row in cur.execute('SELECT DISTINCT seq FROM inspection_records ORDER BY seq').fetchall()],
        'device_name': [row['device_name'] for row in cur.execute('SELECT DISTINCT device_name FROM inspection_records ORDER BY device_name').fetchall()],
        'check_part': [row['check_part'] for row in cur.execute('SELECT DISTINCT check_part FROM inspection_records ORDER BY check_part').fetchall()],
        'check_item': [row['check_item'] for row in cur.execute('SELECT DISTINCT check_item FROM inspection_records ORDER BY check_item').fetchall()],
        'standard': [row['standard'] for row in cur.execute('SELECT DISTINCT standard FROM inspection_records ORDER BY standard').fetchall()],
        'check_result': [row['check_result'] for row in cur.execute('SELECT DISTINCT check_result FROM inspection_records ORDER BY check_result').fetchall()],
        'record_time': [row['record_time'] for row in cur.execute('SELECT DISTINCT record_time FROM inspection_records ORDER BY record_time').fetchall()]
    }
    conn.close()

    return render_template('check_record.html', records=records, filters=filters, options=options)

@app.route('/delete_record/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM inspection_records WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('check_record'))

@app.route('/delete_all_records', methods=['POST'])
def delete_all_records():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM inspection_records')
    conn.commit()
    conn.close()
    return redirect(url_for('check_record'))

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(DATA_FILE):
        save_data({
            "base_info": {
                "line_equip": [],
                "material": [],
                "inspection_route": [],
                "position_id": [],
                "inspection_standard": []
            },
            "check_task": [],
            "repair_order": []
        })
    app.run(debug=True)
