#!/usr/bin/env python3
import sys
sys.path.append('..')  # fix import directory

from app import app, db
from app.models import *
from datetime import datetime

BASEDIR = '../data/misteach'

def parse_file(filename):
    data = []
    with open(BASEDIR + '/' + filename) as f:
        # The first line
        for line in f:
            keys = [ col.strip() for col in line.split('\t') ]
            break

        for line in f:
            cols = [ col.strip() for col in line.split('\t') ]
            if len(keys) != len(cols):
                continue
            data.append(dict(zip(keys, cols)))

    return data

def load_students():
    count = 0
    for c in parse_file('XJ_XJQL_TJB.txt'):
        if c['XNXQ'] == '20141':
            stu = Student()
            stu.sno = c['SNO']
            stu.name = c['XM']
            stu.dept = c['XZYXMC']
            stu.dept_class = c['XZBJMC']
            stu.major = c['XDYXMC']
            db.session.add(stu)
            count+=1

    db.session.commit()
    print('%d students loaded' % count)

def load_teacher():
    count = 0
    for c in parse_file('T_YHXXB.txt'):
        t = Teacher()
        t.id = c['YHID']
        t.name = c['XM']
        t.email = c['EMAIL']
        t.description = c['INTRODUCTION']
        db.session.add(t)
        count+=1

    db.session.commit()
    print('%d teachers loaded' % count)

def load_course():
    course_major_dict = dict(
        ES   =   '电子科学技术',
        NU   =   '核科学类',
        IS   =   '信息安全',
        PS   =   '政治学',
        FL   =   '外国语言',
        CO   =   '传播学',
        SH   =   '科学技术史',
        HS   =   '人文社科类',
        SW   =   '软件工程',
        PE   =   '体育',
        LW   =   '法学类',
        AY   =   '天文学',
        MA   =   '数学',
        PH   =   '物理学',
        EM   =   '经济管理',
        CH   =   '化学',
        MS   =   '材料科学',
        GP   =   '地球物理',
        AE   =   '大气科学',
        GE   =   '地球化学',
        EN   =   '环境科学',
        BI   =   '生物学',
        ME   =   '力学',
        PI   =   '仪器与机械类',
        TS   =   '动力工程',
        SE   =   '安全工程',
        IN   =   '信息类',
        CN   =   '控制科学',
        CS   =   '计算机科学技术',
    )

    course_type_dict = dict()
    course_type_dict['1'] = '本科计划内课程'
    course_type_dict['2'] = '入学考试'
    course_type_dict['4'] = '全校公修'
    course_type_dict['5'] = '研究生课'
    course_type_dict['7'] = '外校交流课程'
    course_type_dict['8'] = '双学位'
    course_type_dict['15'] = '体育选项'
    course_type_dict['16'] = '英语拓展'
    course_type_dict['99'] = '本科计划内/全校公修'

    course_level_dict = [
        None,
        '全校通修',
        '学科群基础课',
        '专业核心课',
        '专业硕士课',
        '专业方向课',
        '本研衔接',
        '硕士层次',
        '博士层次',
    ]

    grading_type_dict = [
        None,
        '百分制',
        '二分制',
        '五分制',
    ]

    int_allow_empty = lambda string: int(string) if string.strip() else 0
    course_kcbh = {}
    for c in parse_file('JH_KC_ZK.txt'):
        course_kcbh[c['KCBH']] = dict(
            kcid = c['KCID'],
            kcbh = c['KCBH'],
            name = c['KCZW'],
            name_eng = c['KCYW'],
            credit = c['XF'],
            hours = c['XS'],
            hours_per_week = c['ZXS'],
            teaching_material = c['JC'],
            reference_material = c['CKS'],
            student_requirements = c['XSYQ'],
            description = c['KCJJ'],
            description_eng = c['YWJJ'],
            course_major = course_major_dict[c['XKLB']] if c['XKLB'] in course_major_dict else None,
            course_type = course_type_dict[c['KCFC']] if c['KCFC'] in course_type_dict else None,
            grading_type = grading_type_dict[int_allow_empty(c['PFZ'])],
        )

    count = 0
    for c in parse_file('MV_PK_PKJGXS.txt'):
        if not c['KCBH'] in course_kcbh:
            print('Course ' + c['KCBH'] + ' exists in MV_PK_PKJGXS but not in JH_KC_ZK: ' + str(c))
            continue

        info = course_kcbh[c['KCBH']]
        info['term'] = c['XQ']
        info['cno'] = c['KCBJH']
        info['courseries'] = c['KCBH']
        info['dept'] = c['DWMC']
        info['class_numbers'] = c['SKBJH']
        info['teacher_id'] = c['JS']
        info['start_week'] = c['QSZ']
        info['end_week'] = c['JZZ']
        info['course_level'] = course_level_dict[int_allow_empty(c['KCCCDM'])]

        course = Course()
        for key in info:
            setattr(course, key, info[key])
        db.session.add(course)
        count+=1
        if count == 20:
            break

    db.session.commit()
    print('%d courses loaded' % count)

def load_course_locations():
    int_allow_empty = lambda string: int(string) if string.strip() else None
    def get_begin_hour(code, num_hours):
        if code == '1': # (1,2)
            return 1
        elif code == '2': # (3,4) (3,4,5)
            return 3
        elif code == '3': # (6,7)
            return 6
        elif code == '4': # (8,9) (8,9,10)
            return 8
        elif code == '5': # 晚上
            return 11
        elif code == 'a': # (7,8) (6,7,8)
            return 7 if num_hours == 2 else 6
        elif code == 'b': # (9,10)
            return 9
        else:
            return None

    count = 0
    for c in parse_file('PK_PKJGB.txt'):
        course = Course.query.filter_by(cno = c['KCBJH'], term = c['ND'] + c['XQ']).first()
        if not course:
            print('Course not found: ' + str(c))
            continue

        loc = CourseTimeLocation()
        loc.course = course
        loc.location = c['JSBH']
        if len(c['SJPDM']) == 2:
            loc.weekday = int_allow_empty(c['SJPDM'][0])
            loc.num_hours = int_allow_empty(c['KS'])
            loc.begin_hour = get_begin_hour(c['SJPDM'][1], c['KS'])
        else:
            loc.note = c['BEIY1']

        db.session.add(loc)
        count+=1

    db.session.commit()
    print('%d course locations loaded' % count)

def load_join_course():
    count = 0
    for c in parse_file('XK_XKJGB.txt'):
        course = Course.query.filter_by(cno = c['KCBJH'], term=c['XNXQ']).first()
        if not course:
            print('Course not found:' + str(c))
            continue

        join_course = JoinCourse()
        join_course.course = course
        join_course.student_id = c['XH']
        join_course.course_type = c['KCLB']
        join_course.course_attr = c['KCSX']
        join_course.join_time = datetime.strptime(c['XZSJ'], "%Y-%m-%dT%H:%M:%S")

        db.session.add(join_course)
        db.session.commit()
        count+=1

    print('%d xuanke info loaded' % count)


db.drop_all()
db.create_all()
#load_teacher()
load_course()
#load_course_locations()
#load_students()
#load_join_course()