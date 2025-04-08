from flask import Flask, render_template, redirect, url_for, request, flash, send_file, session
from models import db, User, InspectionTemplate, InspectionUnit, InspectionItem, InspectionRecord, OperationLog
from config import Config
from functools import wraps
import pandas as pd
import io
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


# 权限装饰器
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in role:
                flash("权限不足", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# 初始化数据库和默认数据
template_data = {
    "name": "开始点检",
    "units": [
        {"name": "四轴机器人单元", "items": [
            {"sequence": 1, "device_name": "断路器", "part": "本体", "content": "状态检查",
             "standard": "触点接线牢靠，无放电、裂纹现象"},
            {"sequence": 2, "device_name": "托盘上料模块", "part": "气缸运行", "content": "状态检查",
             "standard": "将托盘正常输送到装配位置"},
            {"sequence": 3, "device_name": "操作面板模块", "part": "本体", "content": "状态检查",
             "standard": "按钮和指示灯功能正常"},
            {"sequence": 4, "device_name": "机器人本体", "part": "本体", "content": "状态检查",
             "standard": "开机正常运行，无报警"},
            {"sequence": 5, "device_name": "机器人夹具", "part": "夹具", "content": "状态检查",
             "standard": "吸盘正常工作"},
            {"sequence": 6, "device_name": "机器人本体", "part": "本体", "content": "检查温度",
             "standard": "本体运行温度正常"},
            {"sequence": 7, "device_name": "开关电源", "part": "本体", "content": "状态检查",
             "standard": "24V电源输出正常"},
            {"sequence": 8, "device_name": "托盘检测传感器", "part": "检测值", "content": "状态检查",
             "standard": "精准检测到物料托盘"},
            {"sequence": 9, "device_name": "托盘上料机构", "part": "本体", "content": "机械检查",
             "standard": "固定牢靠，螺丝无松动"},
            {"sequence": 10, "device_name": "托盘上料启动按钮", "part": "本体", "content": "状态检查",
             "standard": "按钮功能正常"},
        ]},
        {"name": "上料整列单元", "items": [
            {"sequence": 1, "device_name": "储料台装置", "part": "本体", "content": "状态检查",
             "standard": "固定牢靠，螺丝无松动"},
            {"sequence": 2, "device_name": "输送带机构", "part": "本体", "content": "状态检查",
             "standard": "固定牢靠，螺丝无松动"},
            {"sequence": 3, "device_name": "输送带电机", "part": "本体", "content": "检查温度",
             "standard": "电机运行温度正常"},
            {"sequence": 4, "device_name": "定位传感器", "part": "检测值", "content": "状态检查",
             "standard": "精准检测到遥控器"},
            {"sequence": 5, "device_name": "储料台传感器", "part": "检测值", "content": "状态检查",
             "standard": "精准检测到遥控器"},
            {"sequence": 6, "device_name": "操作面板模块", "part": "本体", "content": "状态检查",
             "standard": "电源控制功能正常"},
            {"sequence": 7, "device_name": "断路器", "part": "本体", "content": "机械检查",
             "standard": "1.外壳表面及缝隙不能有破损、开裂、露铜；2.无油渍、污渍"},
            {"sequence": 8, "device_name": "桌面线路板组件", "part": "本体", "content": "状态检查",
             "standard": "24V电源供电正常"},
            {"sequence": 9, "device_name": "触摸屏装置", "part": "本体", "content": "状态检查",
             "standard": "固定牢靠，螺丝无松动"},
            {"sequence": 10, "device_name": "备用项", "part": "本体", "content": "状态检查", "standard": "无异常"},
        ]},
        {"name": "加盖单元", "items": [
            {"sequence": 1, "device_name": "加盖装置", "part": "本体", "content": "状态检查",
             "standard": "固定牢靠，螺丝无松动"},
            {"sequence": 2, "device_name": "输送带机构", "part": "本体", "content": "状态检查",
             "standard": "固定牢靠，螺丝无松动"},
            {"sequence": 3, "device_name": "升降台电机", "part": "本体", "content": "检查温度",
             "standard": "电机运行温度正常"},
            {"sequence": 4, "device_name": "升降台装置", "part": "推料气缸", "content": "状态检查",
             "standard": "推料气缸伸缩顺畅，运行正常"},
            {"sequence": 5, "device_name": "按钮控制板", "part": "本体", "content": "状态检查",
             "standard": "固定牢靠，外观无破损，无灰尘，无油渍"},
            {"sequence": 6, "device_name": "加盖升降气缸", "part": "本体", "content": "机械检查",
             "standard": "固定牢靠，螺丝无松动"},
            {"sequence": 7, "device_name": "物料台传感器", "part": "本体", "content": "状态检查",
             "standard": "正常检测到物料盒底"},
            {"sequence": 8, "device_name": "物料台装置", "part": "本体", "content": "状态检查",
             "standard": "固定牢靠，螺丝无松动"},
            {"sequence": 9, "device_name": "加盖移动气缸", "part": "运行状态", "content": "状态检查",
             "standard": "气缸移动顺畅，无卡顿"},
            {"sequence": 10, "device_name": "加盖夹具", "part": "运行状态", "content": "状态检查",
             "standard": "正常抓取遥控器盖子，无松动"},
        ]},
        {"name": "搬运入仓单元", "items": [
            {"sequence": 1, "device_name": "开关电源", "part": "本体", "content": "状态检查",
             "standard": "开关电源外观无破损，无灰尘，无油渍"},
            {"sequence": 2, "device_name": "搬运入仓装置", "part": "运行状态", "content": "检查",
             "standard": "运行功能正常"},
            {"sequence": 3, "device_name": "操作面板模块", "part": "本体", "content": "状态检查",
             "standard": "电源控制功能正常"},
            {"sequence": 4, "device_name": "横轴伺服驱动器", "part": "本体", "content": "状态检查",
             "standard": "伺服驱动器外观无破损，无灰尘，无油渍"},
            {"sequence": 5, "device_name": "列轴伺服驱动器", "part": "本体", "content": "状态检查",
             "standard": "运行正常，无报警"},
            {"sequence": 6, "device_name": "列轴伺服电机", "part": "本体", "content": "检查升温",
             "standard": "电机运行温度正常"},
            {"sequence": 7, "device_name": "气源二联件", "part": "气压", "content": "状态检查",
             "standard": "气源气压正常，压力值在0.4-0.5MPa"},
            {"sequence": 8, "device_name": "搬运入仓装置", "part": "本体", "content": "机械检查",
             "standard": "固定牢靠，螺丝无松动"},
            {"sequence": 9, "device_name": "输送带", "part": "运行状态", "content": "状态检查",
             "standard": "运行正常，无卡顿"},
            {"sequence": 10, "device_name": "输送带装置", "part": "本体", "content": "机械检查",
             "standard": "固定牢靠，螺丝无松动"},
        ]},
    ]
}

with app.app_context():
    db.drop_all()  # 清空现有数据库
    db.create_all()  # 重新创建表
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='admin123', role='admin')
        db.session.add(admin)
        db.session.commit()
    template = InspectionTemplate(name=template_data["name"])
    db.session.add(template)
    db.session.commit()
    for unit_data in template_data["units"]:
        unit = InspectionUnit(template_id=template.id, name=unit_data["name"])
        db.session.add(unit)
        db.session.commit()
        for item_data in unit_data["items"]:
            item = InspectionItem(
                unit_id=unit.id, sequence=item_data["sequence"], device_name=item_data["device_name"],
                part=item_data["part"], content=item_data["content"], standard=item_data["standard"]
            )
            db.session.add(item)
        db.session.commit()


# 根路由，重定向到登录页面
@app.route('/')
def index():
    return redirect(url_for('login'))


# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = user.username
            session['role'] = user.role
            log = OperationLog(username=username, action="登录")
            db.session.add(log)
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'danger')
    return render_template('login.html')


# 仪表盘
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    templates = InspectionTemplate.query.all()
    records = InspectionRecord.query.all()
    units = ["四轴机器人单元", "上料整列单元", "加盖单元", "搬运入仓单元"]

    # 点检完成率数据
    completion_data = []
    for unit in units:
        total = sum(1 for r in records if r.unit_name == unit)
        completion_data.append(total * 10 if total else 0)  # 假设每单元10项，简单计算

    # 故障率数据
    failure_data = []
    normal_data = []
    for unit in units:
        total = sum(1 for r in records if r.unit_name == unit)
        abnormal = sum(1 for r in records if r.unit_name == unit and r.result == "异常")
        normal = total - abnormal
        failure_data.append((abnormal / total * 100) if total else 0)
        normal_data.append((normal / total * 100) if total else 0)

    chart_data = {"labels": units, "numbers": completion_data}
    failure_chart_data = {
        "labels": units,
        "failure": failure_data,
        "normal": normal_data
    }
    return render_template('dashboard.html', username=session['username'], templates=templates,
                           chart_data=chart_data, failure_chart_data=failure_chart_data)


# 点检页面
@app.route('/inspection/<int:template_id>', methods=['GET', 'POST'])
@role_required(['technician', 'admin'])
def inspection(template_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    template = InspectionTemplate.query.get_or_404(template_id)
    if request.method == 'POST':
        anomalies = []
        for key in request.form:
            if key.startswith('normal_') or key.startswith('abnormal_'):
                item_id = int(key.split('_')[1])
                normal = request.form.get(f'normal_{item_id}') == 'on'
                abnormal = request.form.get(f'abnormal_{item_id}') == 'on'
                note = request.form.get(f'note_{item_id}', '')
                item = InspectionItem.query.get(item_id)
                if item:
                    if normal and abnormal:
                        flash(f"{item.device_name} - {item.content} 不能同时选择正常和异常", "danger")
                        continue
                    result = "正常" if normal else "异常" if abnormal else "未检查"
                    record = InspectionRecord(
                        template_id=template_id, unit_name=item.unit.name, device_name=item.device_name,
                        part=item.part, content=item.content, standard=item.standard, result=result, note=note,
                        inspected_by=session['username'], is_custom=False
                    )
                    db.session.add(record)
                    if abnormal:
                        anomalies.append(f"{item.device_name} - {item.content}")
        db.session.commit()
        if anomalies:
            flash(f"检测到异常: {', '.join(anomalies)}", "warning")
        else:
            flash("点检记录保存成功", "success")
        return redirect(url_for('dashboard'))
    units = InspectionUnit.query.filter_by(template_id=template_id).all()
    unit_items = [
        {"unit": unit, "items": InspectionItem.query.filter_by(unit_id=unit.id).order_by(InspectionItem.sequence).all()}
        for unit in units]
    return render_template("inspection.html", username=session['username'], template=template, unit_items=unit_items)


# 用户管理页面
@app.route('/manage_users', methods=['GET', 'POST'])
@role_required(['admin'])
def manage_users():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            username = request.form['username']
            password = request.form['password']
            role = request.form['role']
            if User.query.filter_by(username=username).first():
                flash("用户名已存在", "danger")
            else:
                new_user = User(username=username, password=password, role=role)
                db.session.add(new_user)
                db.session.commit()
                flash("用户添加成功", "success")
        elif action == 'edit':
            user_id = request.form['user_id']
            user = User.query.get(user_id)
            if user:
                user.username = request.form['username']
                user.password = request.form['password']
                user.role = request.form['role']
                db.session.commit()
                flash("用户信息修改成功", "success")
            else:
                flash("用户不存在", "danger")
    users = User.query.all()
    return render_template('manage_users.html', users=users)


# 点检记录页面
@app.route('/records', methods=['GET', 'POST'])
def records():
    if 'username' not in session:
        return redirect(url_for('login'))

    # 获取筛选参数
    unit_name = request.form.get('unit_name', '')
    result = request.form.get('result', '')
    inspected_by = request.form.get('inspected_by', '')
    device_name = request.form.get('device_name', '')
    part = request.form.get('part', '')
    content = request.form.get('content', '')
    standard = request.form.get('standard', '')
    note = request.form.get('note', '')
    created_at = request.form.get('created_at', '')

    # 构建查询
    query = InspectionRecord.query
    if unit_name:
        query = query.filter(InspectionRecord.unit_name.ilike(f'%{unit_name}%'))
    if result:
        query = query.filter(InspectionRecord.result == result)
    if inspected_by:
        query = query.filter(InspectionRecord.inspected_by.ilike(f'%{inspected_by}%'))
    if device_name:
        query = query.filter(InspectionRecord.device_name.ilike(f'%{device_name}%'))
    if part:
        query = query.filter(InspectionRecord.part.ilike(f'%{part}%'))
    if content:
        query = query.filter(InspectionRecord.content.ilike(f'%{content}%'))
    if standard:
        query = query.filter(InspectionRecord.standard.ilike(f'%{standard}%'))
    if note:
        query = query.filter(InspectionRecord.note.ilike(f'%{note}%'))
    if created_at:
        try:
            date = datetime.strptime(created_at, '%Y-%m-%d')
            query = query.filter(db.func.date(InspectionRecord.created_at) == date)
        except ValueError:
            flash("日期格式错误，请使用 YYYY-MM-DD 格式", "danger")

    records = query.all()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            record_id = request.form['record_id']
            record = InspectionRecord.query.get(record_id)
            if record:
                db.session.delete(record)
                db.session.commit()
                flash("记录已删除", "success")
        elif action == 'delete_all':
            for record in records:
                db.session.delete(record)
            db.session.commit()
            flash("所有记录已删除", "success")
        return redirect(url_for('records'))

    units = ["四轴机器人单元", "上料整列单元", "加盖单元", "搬运入仓单元"]
    users = User.query.all()
    return render_template('records.html', records=records, units=units, users=users,
                           selected_unit=unit_name, selected_result=result, selected_inspected_by=inspected_by,
                           selected_device_name=device_name, selected_part=part, selected_content=content,
                           selected_standard=standard, selected_note=note, selected_created_at=created_at)


# 导出 Excel 路由（支持筛选）
@app.route('/export_excel', methods=['GET', 'POST'])
def export_excel():
    if 'username' not in session:
        return redirect(url_for('login'))

    unit_name = request.args.get('unit_name', '')
    result = request.args.get('result', '')
    inspected_by = request.args.get('inspected_by', '')
    device_name = request.args.get('device_name', '')
    part = request.args.get('part', '')
    content = request.args.get('content', '')
    standard = request.args.get('standard', '')
    note = request.args.get('note', '')
    created_at = request.args.get('created_at', '')

    query = InspectionRecord.query
    if unit_name:
        query = query.filter(InspectionRecord.unit_name.ilike(f'%{unit_name}%'))
    if result:
        query = query.filter(InspectionRecord.result == result)
    if inspected_by:
        query = query.filter(InspectionRecord.inspected_by.ilike(f'%{inspected_by}%'))
    if device_name:
        query = query.filter(InspectionRecord.device_name.ilike(f'%{device_name}%'))
    if part:
        query = query.filter(InspectionRecord.part.ilike(f'%{part}%'))
    if content:
        query = query.filter(InspectionRecord.content.ilike(f'%{content}%'))
    if standard:
        query = query.filter(InspectionRecord.standard.ilike(f'%{standard}%'))
    if note:
        query = query.filter(InspectionRecord.note.ilike(f'%{note}%'))
    if created_at:
        try:
            date = datetime.strptime(created_at, '%Y-%m-%d')
            query = query.filter(db.func.date(InspectionRecord.created_at) == date)
        except ValueError:
            pass

    records = query.all()

    if not records:
        flash("暂无点检记录可导出", "warning")
        return redirect(url_for('dashboard'))

    data = [{
        "模板ID": record.template_id,
        "单元名称": record.unit_name,
        "设备名称": record.device_name,
        "点检部位": record.part,
        "点检内容": record.content,
        "判断标准": record.standard,
        "结果": record.result,
        "备注": record.note,
        "检查人": record.inspected_by,
        "创建时间": record.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for record in records]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='点检记录')
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='inspection_records.xlsx'
    )


# 登出
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)