import csv
import datetime
import os
import random

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

app = Flask(__name__)
app.secret_key = "hcaiexperimentsecret"


TOTAL_TRIALS_PER_SESSION = 16
TOTAL_POOL_SIZE = 32


PRACTICE_TRIALS = [
    {
        "stimulus_id": "PRAC_FP",
        "description": "患者出现轻微咳嗽与流鼻涕，但胸部 X 光影像显示正常。",
        "ai_decision": "AI 判断患者患有肺炎（阳性）。",
        "ground_truth": "真实情况：患者并未患有肺炎（假阳性）。",
        "error_type": "FP",
        "explanation": "系统认为影像中心亮度偏高，所以判定为肺炎。",
    },
    {
        "stimulus_id": "PRAC_FN",
        "description": "患者发热 38.8℃，伴随呼吸急促与胸闷。",
        "ai_decision": "AI 判断患者未患肺炎（阴性）。",
        "ground_truth": "真实情况：患者患有肺炎（假阴性）。",
        "error_type": "FN",
        "explanation": "模型没有检测到异常模式，因此保持阴性判断。",
    },
]


TRIALS = [
    # FP + Poor 解释
    {
        "stimulus_id": "FP_Poor_1",
        "description": "学生在线作业中有 2 次轻微抄袭嫌疑，但系统日志记录与同伴一致。",
        "ai_decision": "AI 判定该学生抄袭（阳性）。",
        "ground_truth": "真实情况：该学生未抄袭（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "因为系统觉得题目太像，所以认为是抄袭。",
    },
    {
        "stimulus_id": "FP_Poor_2",
        "description": "客户信用卡夜间消费 120 元，与其历史夜间消费接近。",
        "ai_decision": "AI 判定为欺诈交易（阳性）。",
        "ground_truth": "真实情况：该交易合法（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "模型感觉金额突然出现，就判定为欺诈。",
    },
    {
        "stimulus_id": "FP_Poor_3",
        "description": "制造车间传感器偶尔出现温度浮动，但平均值正常。",
        "ai_decision": "AI 判定设备即将故障（阳性）。",
        "ground_truth": "真实情况：设备运行正常（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "系统觉得数据乱跳，所以判定会坏。",
    },
    {
        "stimulus_id": "FP_Poor_4",
        "description": "患者血糖检测为 6.0 mmol/L，处于正常阈值范围内。",
        "ai_decision": "AI 判定患者血糖异常（阳性）。",
        "ground_truth": "真实情况：血糖正常（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "模型看到数值不是 5，就判为异常。",
    },
    {
        "stimulus_id": "FP_Poor_5",
        "description": "机场安检识别旅客包中液体体积 90 毫升，且旅客出示合法证明。",
        "ai_decision": "AI 判定该液体属于违禁品（阳性）。",
        "ground_truth": "真实情况：液体合规（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "系统感觉液体看起来危险，所以拒绝放行。",
    },
    {
        "stimulus_id": "FP_Poor_6",
        "description": "智能农作物监测系统发现一块地的叶片颜色略浅。",
        "ai_decision": "AI 判定该地块感染病害（阳性）。",
        "ground_truth": "真实情况：叶片正常生长（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "模型觉得颜色不太对劲，就认定是病害。",
    },
    {
        "stimulus_id": "FP_Poor_7",
        "description": "呼叫中心情绪分析系统检测用户语音稍有起伏。",
        "ai_decision": "AI 判定用户非常愤怒（阳性）。",
        "ground_truth": "真实情况：用户语气平稳（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "系统听到有波动，就认定用户生气。",
    },
    {
        "stimulus_id": "FP_Poor_8",
        "description": "智慧物流系统检测包裹重量比标签重 30 克。",
        "ai_decision": "AI 判定包裹有危险品（阳性）。",
        "ground_truth": "真实情况：重量正常误差（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "模型觉得重量多了一点点，就报警。",
    },
    # FP + Good 解释
    {
        "stimulus_id": "FP_Good_1",
        "description": "仓库安全摄像头捕捉到夜间移动影像，热感应信号短暂升高。",
        "ai_decision": "AI 判定发生入侵（阳性）。",
        "ground_truth": "真实情况：为巡逻保安（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "系统检测到夜间非常规移动轨迹与热量峰值，与历史入侵模式高度相似，因此给出入侵判断。",
    },
    {
        "stimulus_id": "FP_Good_2",
        "description": "高校网络上出现 30 次来自同一 IP 的登陆尝试，分布在 30 分钟内。",
        "ai_decision": "AI 判定为暴力破解攻击（阳性）。",
        "ground_truth": "真实情况：为学生忘记密码反复尝试（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "模型依据连续失败次数与固定时间间隔匹配典型暴力破解特征，因此输出攻击警报。",
    },
    {
        "stimulus_id": "FP_Good_3",
        "description": "自动驾驶车辆检测到前方路面闪烁反光，雷达距离数据稳定。",
        "ai_decision": "AI 判定前方存在障碍物（阳性）。",
        "ground_truth": "真实情况：为地面水坑反光（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "视觉模块识别到亮点并与障碍物特征库比对高度相似，尽管雷达未提示异常，因此输出障碍警告。",
    },
    {
        "stimulus_id": "FP_Good_4",
        "description": "银行风控模型监测到用户连续三笔跨国大额转账。",
        "ai_decision": "AI 判定账户被盗用（阳性）。",
        "ground_truth": "真实情况：用户正在海外支付学费（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "模型根据短时间内的异常交易金额、地区跨度与历史频率差异显著，故判断为被盗用风险。",
    },
    {
        "stimulus_id": "FP_Good_5",
        "description": "公共卫生监测系统检测到某社区连续三日体温申报超出平均值。",
        "ai_decision": "AI 判定该社区爆发流感（阳性）。",
        "ground_truth": "真实情况：社区健康状况正常（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "模型使用移动平均对比历史数据，发现连续偏高并超过内部阈值，因此发出流感预警。",
    },
    {
        "stimulus_id": "FP_Good_6",
        "description": "高校学术诚信系统检测学生上传论文与数据库相似度 42%。",
        "ai_decision": "AI 判定论文存在抄袭（阳性）。",
        "ground_truth": "真实情况：引用符合规范（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "系统根据长段重复及引用数量少于阈值判断存在潜在抄袭，因而输出违规结论。",
    },
    {
        "stimulus_id": "FP_Good_7",
        "description": "自动化仓储机器人检测托盘倾斜 6°，略超安全线。",
        "ai_decision": "AI 判定托盘将倒塌（阳性）。",
        "ground_truth": "真实情况：托盘稳定（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "模型根据陀螺仪持续 20 秒超过 5° 的阈值，并与过往倒塌事件相似模式高度匹配，故发出预警。",
    },
    {
        "stimulus_id": "FP_Good_8",
        "description": "银行反洗钱系统发现客户在 7 天内分多笔转账至相同离岸账户。",
        "ai_decision": "AI 判定存在洗钱行为（阳性）。",
        "ground_truth": "真实情况：客户合法投资（假阳性）。",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "模型对比交易模式与历史洗钱案例，在频率、金额和目的地上均超过风险阈值，因而判定为高风险交易。",
    },
    # FN + Poor 解释
    {
        "stimulus_id": "FN_Poor_1",
        "description": "患者持续发热 39℃ 并伴有脉搏加快和咳痰。",
        "ai_decision": "AI 判定患者未患肺炎（阴性）。",
        "ground_truth": "真实情况：患者确实患有肺炎（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "系统没看到特殊东西，就判断没病。",
    },
    {
        "stimulus_id": "FN_Poor_2",
        "description": "工厂震动传感器持续超过警戒线 15%，并出现尖峰。",
        "ai_decision": "AI 判定机器状态正常（阴性）。",
        "ground_truth": "真实情况：机器轴承损坏（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "模型觉得震动不算高，因此保持正常。",
    },
    {
        "stimulus_id": "FN_Poor_3",
        "description": "邮件安全系统发现附件为可执行文件且历史未见发送者。",
        "ai_decision": "AI 判定邮件安全（阴性）。",
        "ground_truth": "真实情况：邮件包含恶意软件（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "系统没有进一步分析，就认为没问题。",
    },
    {
        "stimulus_id": "FN_Poor_4",
        "description": "客户转账记录显示半小时内在 3 个城市消费。",
        "ai_decision": "AI 判定账号正常（阴性）。",
        "ground_truth": "真实情况：账号遭到盗用（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "模型没有发现十分异常的模式，所以放行。",
    },
    {
        "stimulus_id": "FN_Poor_5",
        "description": "智能路况监控系统收到多辆车举报同一路段积水严重。",
        "ai_decision": "AI 判定道路状况正常（阴性）。",
        "ground_truth": "真实情况：该路段已无法通行（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "系统没看到特别的数据变化，就保持正常。",
    },
    {
        "stimulus_id": "FN_Poor_6",
        "description": "企业安全系统记录员工连续两次错误登录且地区异常.",
        "ai_decision": "AI 判定账户安全（阴性）。",
        "ground_truth": "真实情况：账户被盗用（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "模型认为次数不多，所以没有报警。",
    },
    {
        "stimulus_id": "FN_Poor_7",
        "description": "智能农业系统监测到夜间温度急降 8℃，湿度飙升。",
        "ai_decision": "AI 判定作物不会受损（阴性）。",
        "ground_truth": "真实情况：作物冻害严重（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "系统觉得变化不算太极端，就没处理。",
    },
    {
        "stimulus_id": "FN_Poor_8",
        "description": "智能客服系统看到用户连续三条抱怨账单错误的信息。",
        "ai_decision": "AI 判定非投诉（阴性）。",
        "ground_truth": "真实情况：用户正式投诉（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "模型没有特别标记，就归为普通咨询。",
    },
    # FN + Good 解释
    {
        "stimulus_id": "FN_Good_1",
        "description": "医院急诊患者血氧 90%，CT 图像存在少量阴影，但噪声较大。",
        "ai_decision": "AI 判定未患肺炎（阴性）。",
        "ground_truth": "真实情况：患者患有肺炎（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "模型依据阴影面积未达到内部阈值，且图像信噪比较差，未触发肺炎特征组合，因此输出阴性判断。",
    },
    {
        "stimulus_id": "FN_Good_2",
        "description": "智能客服收到用户关于账单的短语式抱怨，仅 15 个词且情绪较弱。",
        "ai_decision": "AI 判定非投诉（阴性）。",
        "ground_truth": "真实情况：用户正式投诉（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "系统根据语气强度与词汇长度未达到投诉模型阈值，因而被归类为一般咨询。",
    },
    {
        "stimulus_id": "FN_Good_3",
        "description": "制造生产线温度上升 5℃ 并伴随轻微噪声，但仍在历史波动范围边缘。",
        "ai_decision": "AI 判定设备正常（阴性）。",
        "ground_truth": "真实情况：设备内部部件松动（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "模型检查到温度与噪声变化但未同时超过设定阈值，因此继续判定为正常运行。",
    },
    {
        "stimulus_id": "FN_Good_4",
        "description": "网络安全系统监测到异常流量，但分布在多个端口且峰值较低。",
        "ai_decision": "AI 判定无攻击（阴性）。",
        "ground_truth": "真实情况：存在低频扫描攻击（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "由于单一端口未出现显著峰值，流量被判为背景噪声，未触发攻击检测阈值。",
    },
    {
        "stimulus_id": "FN_Good_5",
        "description": "临床诊断系统接收患者胸痛和轻微呼吸困难信息，心电图噪声较大。",
        "ai_decision": "AI 判定未发生心梗（阴性）。",
        "ground_truth": "真实情况：患者正经历心肌梗死（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "模型依据心电图中 ST 段抬高幅度不足阈值且信号噪声过大，因此未触发心梗风险评分。",
    },
    {
        "stimulus_id": "FN_Good_6",
        "description": "环境监测系统检测到工厂废气指标略高于日常平均值。",
        "ai_decision": "AI 判定排放正常（阴性）。",
        "ground_truth": "真实情况：排放超标（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "模型因使用 7 日滑动平均进行平滑，导致单日峰值被抵消，未达到超标阈值，故判定正常。",
    },
    {
        "stimulus_id": "FN_Good_7",
        "description": "智能招聘系统接收候选人经历，关键词匹配度略低。",
        "ai_decision": "AI 判定候选人不符合岗位（阴性）。",
        "ground_truth": "真实情况：候选人高度匹配（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "模型依赖的语义匹配分数未超过 0.72 阈值，因此未进入推荐列表。",
    },
    {
        "stimulus_id": "FN_Good_8",
        "description": "智能电网系统观测到城区用电负载上升 12%，持续 30 分钟。",
        "ai_decision": "AI 判定供电稳定（阴性）。",
        "ground_truth": "真实情况：线路即将过载（假阴性）。",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "模型依据历史模式判断此类短时上涨通常在 45 分钟内回落，且未超过预测区间上界，因此未触发告警。",
    },
]


def ensure_session():
    if "participant" not in session:
        flash("会话已过期，请重新开始实验。")
        return False
    return True


@app.route("/", methods=["GET", "POST"])
def intro():
    if request.method == "POST":
        consent = request.form.get("consent")
        participant_id = request.form.get("participant_id", "").strip()
        control_var = request.form.get("control_var", "").strip()

        if consent != "yes":
            flash("请勾选同意继续参与实验。")
            return render_template("intro.html")

        if not participant_id:
            flash("请输入参与者编号或代号。")
            return render_template("intro.html")

        session.clear()
        session["participant"] = {
            "id": participant_id,
            "control_var": control_var,
        }
        selected_indices = random.sample(range(len(TRIALS)), TOTAL_TRIALS_PER_SESSION)
        random.shuffle(selected_indices)
        session["trial_order"] = selected_indices
        session["current_trial"] = 0
        session["responses"] = []
        session["practice_index"] = 0

        return redirect(url_for("practice"))

    return render_template("intro.html")


@app.route("/practice", methods=["GET", "POST"])
def practice():
    if not ensure_session():
        return redirect(url_for("intro"))

    practice_index = session.get("practice_index", 0)

    if practice_index >= len(PRACTICE_TRIALS):
        return redirect(url_for("experiment"))

    trial = PRACTICE_TRIALS[practice_index]

    if request.method == "POST":
        clarity = request.form.get("clarity")
        sufficiency = request.form.get("sufficiency")
        predictive = request.form.get("predictive_capability")
        actionability = request.form.get("actionability")
        trustworthiness = request.form.get("trustworthiness")
        accountability = request.form.get("accountability")
        satisfaction = request.form.get("satisfaction")

        if not all(
            [
                clarity,
                sufficiency,
                predictive,
                actionability,
                trustworthiness,
                accountability,
                satisfaction,
            ]
        ):
            flash("请在练习题中完成所有评分，以熟悉流程。")
            return render_template(
                "practice.html",
                trial=trial,
                step=practice_index + 1,
                total=len(PRACTICE_TRIALS),
            )

        session["practice_index"] = practice_index + 1

        if session["practice_index"] >= len(PRACTICE_TRIALS):
            return redirect(url_for("experiment"))

        return redirect(url_for("practice"))

    return render_template(
        "practice.html",
        trial=trial,
        step=practice_index + 1,
        total=len(PRACTICE_TRIALS),
    )


@app.route("/experiment", methods=["GET", "POST"])
def experiment():
    if not ensure_session():
        return redirect(url_for("intro"))

    current_trial = session.get("current_trial", 0)
    order = session.get("trial_order", [])

    if current_trial >= len(order):
        return redirect(url_for("debrief"))

    trial_idx = order[current_trial]
    trial = TRIALS[trial_idx]

    if request.method == "POST":
        clarity = request.form.get("clarity")
        sufficiency = request.form.get("sufficiency")
        predictive = request.form.get("predictive_capability")
        actionability = request.form.get("actionability")
        trustworthiness = request.form.get("trustworthiness")
        accountability = request.form.get("accountability")
        satisfaction = request.form.get("satisfaction")

        if not all(
            [
                clarity,
                sufficiency,
                predictive,
                actionability,
                trustworthiness,
                accountability,
                satisfaction,
            ]
        ):
            flash("请完成所有评分，再继续下一题。")
            return render_template(
                "trial.html",
                trial=trial,
                trial_number=current_trial + 1,
                total=len(order),
            )

        responses = session.get("responses", [])
        responses.append(
            {
                "trial_idx": trial_idx,
                "clarity": int(clarity),
                "sufficiency": int(sufficiency),
                "predictive_capability": int(predictive),
                "actionability": int(actionability),
                "trustworthiness": int(trustworthiness),
                "accountability": int(accountability),
                "satisfaction": int(satisfaction),
            }
        )
        session["responses"] = responses
        session["current_trial"] = current_trial + 1

        if session["current_trial"] >= len(order):
            return redirect(url_for("debrief"))

        return redirect(url_for("experiment"))

    return render_template(
        "trial.html",
        trial=trial,
        trial_number=current_trial + 1,
        total=len(order),
    )


@app.route("/debrief", methods=["GET", "POST"])
def debrief():
    if not ensure_session():
        return redirect(url_for("intro"))

    if request.method == "POST":
        comment = request.form.get("comment", "").strip()
        session["debrief_comment"] = comment
        save_responses()
        data_file = session.get("data_file")
        comment_file = session.get("comment_file")
        session.clear()
        session["data_file"] = data_file
        session["comment_file"] = comment_file
        return redirect(url_for("complete"))

    return render_template("debrief.html")


@app.route("/complete")
def complete():
    data_file = session.get("data_file")
    comment_file = session.get("comment_file")
    return render_template("complete.html", data_file=data_file, comment_file=comment_file)


def save_responses():
    participant = session.get("participant")
    responses = session.get("responses", [])
    order = session.get("trial_order", [])
    comment = session.get("debrief_comment", "")

    if not participant or not responses or not order:
        return

    os.makedirs(DATA_DIR, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    participant_id = participant["id"]
    filename = f"participant_{participant_id}_{timestamp}.csv"
    file_path = os.path.join(DATA_DIR, filename)

    fieldnames = [
        "ParticipantID",
        "TrialNum",
        "ErrorType",
        "ExplanationQuality",
        "Clarity",
        "Sufficiency",
        "PredictiveCapability",
        "Actionability",
        "Trustworthiness",
        "Accountability",
        "Satisfaction",
        "ControlVar",
    ]

    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for idx, response in enumerate(responses, start=1):
            trial_info = TRIALS[response["trial_idx"]]
            writer.writerow(
                {
                    "ParticipantID": participant_id,
                    "TrialNum": idx,
                    "ErrorType": trial_info["error_type"],
                    "ExplanationQuality": trial_info["explanation_quality"],
                    "Clarity": response["clarity"],
                    "Sufficiency": response["sufficiency"],
                    "PredictiveCapability": response["predictive_capability"],
                    "Actionability": response["actionability"],
                    "Trustworthiness": response["trustworthiness"],
                    "Accountability": response["accountability"],
                    "Satisfaction": response["satisfaction"],
                    "ControlVar": participant.get("control_var", ""),
                }
            )

    session["data_file"] = file_path

    if comment:
        comment_filename = filename.replace(".csv", "_comment.txt")
        comment_path = os.path.join(DATA_DIR, comment_filename)
        with open(comment_path, "w", encoding="utf-8") as comment_file:
            comment_file.write(comment)
        session["comment_file"] = comment_path


if __name__ == "__main__":
    app.run(debug=True)
