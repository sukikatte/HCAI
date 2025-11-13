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
        "description": "A patient shows mild cough and runny nose, but the chest X-ray image appears normal.",
        "ai_decision": "The AI predicts that the patient has pneumonia (positive).",
        "ground_truth": "The patient does not have pneumonia (false positive).",
        "error_type": "FP",
        "explanation": "The system noticed higher brightness in the image center and therefore predicted pneumonia.",
    },
    {
        "stimulus_id": "PRAC_FN",
        "description": "A patient has a temperature of 38.8°C along with shortness of breath and chest tightness.",
        "ai_decision": "The AI predicts that the patient does not have pneumonia (negative).",
        "ground_truth": "The patient does have pneumonia (false negative).",
        "error_type": "FN",
        "explanation": "The model did not detect abnormal patterns, so it kept the negative prediction.",
    },
]


TRIALS = [
    # FP + Poor explanation
    {
        "stimulus_id": "FP_Poor_1",
        "description": "An online homework submission shows two minor similarities to a classmate, but the system logs match normal behavior.",
        "ai_decision": "The AI flags the student for plagiarism (positive).",
        "ground_truth": "The student did not plagiarize (false positive).",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "The system thought the answers looked too similar, so it labeled the submission as plagiarism.",
    },
    {
        "stimulus_id": "FP_Poor_2",
        "description": "A customer makes a nighttime credit card purchase of $120, which fits their typical spending pattern.",
        "ai_decision": "The AI flags the purchase as fraud (positive).",
        "ground_truth": "The transaction is legitimate (false positive).",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "The model saw the amount appear suddenly and assumed it must be fraud.",
    },
    {
        "stimulus_id": "FP_Poor_3",
        "description": "Factory sensors occasionally show a temperature spike, yet the average readings remain normal.",
        "ai_decision": "The AI predicts the equipment is about to fail (positive).",
        "ground_truth": "The equipment is operating normally (false positive).",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "Because the data looked jumpy, the system concluded the machine would soon break.",
    },
    {
        "stimulus_id": "FP_Poor_4",
        "description": "A patient’s blood glucose is measured at 6.0 mmol/L, which is within the healthy range.",
        "ai_decision": "The AI flags the blood glucose as abnormal (positive).",
        "ground_truth": "The level is normal (false positive).",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "The model saw the number was not 5, so it labeled it as abnormal.",
    },
    {
        "stimulus_id": "FP_Poor_5",
        "description": "Airport security scans a traveler’s bag containing a 90 ml bottle, and valid documentation is provided.",
        "ai_decision": "The AI flags the liquid as prohibited (positive).",
        "ground_truth": "The item fully complies with regulations (false positive).",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "The system thought the liquid looked dangerous and therefore denied it.",
    },
    {
        "stimulus_id": "FP_Poor_6",
        "description": "A smart agriculture monitor notices a slightly lighter color on one plot of leaves.",
        "ai_decision": "The AI predicts a crop disease outbreak (positive).",
        "ground_truth": "The leaves are healthy (false positive).",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "Because the color seemed off, the model assumed there was a disease.",
    },
    {
        "stimulus_id": "FP_Poor_7",
        "description": "A call-center sentiment tool detects minor pitch fluctuations in a customer’s voice.",
        "ai_decision": "The AI labels the caller as extremely angry (positive).",
        "ground_truth": "The caller’s tone is calm (false positive).",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "The system heard some variation and decided the caller must be upset.",
    },
    {
        "stimulus_id": "FP_Poor_8",
        "description": "A smart logistics scale finds a package weighing 30 grams more than the label indicates.",
        "ai_decision": "The AI flags the package as hazardous (positive).",
        "ground_truth": "The weight difference is normal variance (false positive).",
        "error_type": "FP",
        "explanation_quality": "Poor",
        "explanation": "The model saw a slight excess weight and triggered an alarm.",
    },
    # FP + Good explanation
    {
        "stimulus_id": "FP_Good_1",
        "description": "A warehouse security camera captures nighttime movement and a brief spike in heat signatures.",
        "ai_decision": "The AI reports an intruder (positive).",
        "ground_truth": "It was a security guard on patrol (false positive).",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "The system matched the unusual motion pattern and heat peak with past intrusion incidents, leading to an alert.",
    },
    {
        "stimulus_id": "FP_Good_2",
        "description": "A university network logs 30 login attempts from the same IP over 30 minutes.",
        "ai_decision": "The AI flags a brute-force attack (positive).",
        "ground_truth": "A student simply forgot their password (false positive).",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "The model compared the failure frequency and timing to known attack patterns, so it raised an alarm.",
    },
    {
        "stimulus_id": "FP_Good_3",
        "description": "An autonomous car detects flickering reflections ahead while radar readings stay steady.",
        "ai_decision": "The AI reports an obstacle (positive).",
        "ground_truth": "The reflection came from a wet road surface (false positive).",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "Visual sensors found bright points matching obstacle signatures, so the system issued a hazard warning despite radar stability.",
    },
    {
        "stimulus_id": "FP_Good_4",
        "description": "A banking risk model observes three large international transfers in quick succession.",
        "ai_decision": "The AI flags the account as compromised (positive).",
        "ground_truth": "The customer is paying overseas tuition (false positive).",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "Short-term spikes in amount, geography, and frequency resembled past fraud cases, so it triggered a security warning.",
    },
    {
        "stimulus_id": "FP_Good_5",
        "description": "A public health dashboard registers three consecutive days of elevated temperatures in one neighborhood.",
        "ai_decision": "The AI declares a flu outbreak (positive).",
        "ground_truth": "The community is healthy (false positive).",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "The model compared rolling averages with historical baselines and found a sustained increase that exceeded its alert threshold.",
    },
    {
        "stimulus_id": "FP_Good_6",
        "description": "An academic integrity tool finds a 42% similarity between a student paper and database sources.",
        "ai_decision": "The AI flags the paper for plagiarism (positive).",
        "ground_truth": "The citations follow proper style (false positive).",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "Extended sections matched existing text and the reference count was below the model’s benchmark, so it labeled the submission as a violation.",
    },
    {
        "stimulus_id": "FP_Good_7",
        "description": "A warehouse robot registers that a pallet is tilted 6 degrees, slightly above the safety limit.",
        "ai_decision": "The AI predicts the pallet will collapse (positive).",
        "ground_truth": "The pallet remains stable (false positive).",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "The gyroscope exceeded 5 degrees for over 20 seconds, matching previous collapse data, so the system sent a warning.",
    },
    {
        "stimulus_id": "FP_Good_8",
        "description": "An anti-money-laundering system spots multiple transfers to the same offshore account within seven days.",
        "ai_decision": "The AI flags the activity as potential laundering (positive).",
        "ground_truth": "The customer is making legitimate investments (false positive).",
        "error_type": "FP",
        "explanation_quality": "Good",
        "explanation": "Transaction frequency, amounts, and destination all aligned with high-risk patterns in the training data, so it labeled the account as high risk.",
    },
    # FN + Poor explanation
    {
        "stimulus_id": "FN_Poor_1",
        "description": "A patient runs a fever of 39°C with a rapid pulse and a productive cough.",
        "ai_decision": "The AI predicts the patient does not have pneumonia (negative).",
        "ground_truth": "The patient has pneumonia (false negative).",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "The system did not see anything special, so it assumed the patient was fine.",
    },
    {
        "stimulus_id": "FN_Poor_2",
        "description": "Factory vibration sensors stay 15% above the safety line and show sudden spikes.",
        "ai_decision": "The AI predicts the machine is normal (negative).",
        "ground_truth": "The bearing is failing (false negative).",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "The model thought the vibration wasn’t too high, so it kept the normal label.",
    },
    {
        "stimulus_id": "FN_Poor_3",
        "description": "An email security system spots an executable attachment from an unfamiliar sender.",
        "ai_decision": "The AI labels the email as safe (negative).",
        "ground_truth": "The email contains malware (false negative).",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "The system skipped deeper analysis and concluded the message was harmless.",
    },
    {
        "stimulus_id": "FN_Poor_4",
        "description": "A bank account records purchases in three cities within half an hour.",
        "ai_decision": "The AI marks the account as normal (negative).",
        "ground_truth": "The account was compromised (false negative).",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "The model didn’t detect a strong pattern, so it allowed the activity.",
    },
    {
        "stimulus_id": "FN_Poor_5",
        "description": "A roadway monitoring system receives several driver reports about severe flooding on the same street.",
        "ai_decision": "The AI reports normal road conditions (negative).",
        "ground_truth": "The street is impassable (false negative).",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "Because it didn’t see major data changes, the system kept the road marked as clear.",
    },
    {
        "stimulus_id": "FN_Poor_6",
        "description": "A corporate security platform logs two failed logins from unusual regions.",
        "ai_decision": "The AI says the account is safe (negative).",
        "ground_truth": "The account was taken over (false negative).",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "The model felt the number of attempts was too low to matter, so it ignored them.",
    },
    {
        "stimulus_id": "FN_Poor_7",
        "description": "A smart farming system records an overnight temperature drop of 8°C and a sharp humidity increase.",
        "ai_decision": "The AI says the crops will not be harmed (negative).",
        "ground_truth": "The crops suffer frost damage (false negative).",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "The system thought the change was not extreme enough and took no action.",
    },
    {
        "stimulus_id": "FN_Poor_8",
        "description": "An automated support bot sees three consecutive messages complaining about billing errors.",
        "ai_decision": "The AI classifies the interaction as a non-complaint (negative).",
        "ground_truth": "The customer is filing a formal complaint (false negative).",
        "error_type": "FN",
        "explanation_quality": "Poor",
        "explanation": "Because nothing was specifically flagged, the system treated it as a routine inquiry.",
    },
    # FN + Good explanation
    {
        "stimulus_id": "FN_Good_1",
        "description": "A patient in the emergency department has an SpO₂ level of 90%, and the CT scan shows faint shadows under heavy noise.",
        "ai_decision": "The AI predicts no pneumonia (negative).",
        "ground_truth": "The patient has pneumonia (false negative).",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "The shadow area was below the internal threshold and the scan had low signal-to-noise ratio, so the model kept a negative result.",
    },
    {
        "stimulus_id": "FN_Good_2",
        "description": "A customer service bot receives a short message about a billing issue with mild emotional wording.",
        "ai_decision": "The AI classifies it as a non-complaint (negative).",
        "ground_truth": "The customer is formally complaining (false negative).",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "Phrase length and sentiment scores stayed below the complaint threshold, so it was labeled routine.",
    },
    {
        "stimulus_id": "FN_Good_3",
        "description": "A manufacturing line experiences a 5°C rise and mild noise increases, still near the historical boundary.",
        "ai_decision": "The AI predicts normal operation (negative).",
        "ground_truth": "Internal components are loosening (false negative).",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "Temperature and noise shifts did not cross multiple thresholds simultaneously, so the system kept the normal status.",
    },
    {
        "stimulus_id": "FN_Good_4",
        "description": "A cybersecurity monitor detects abnormal traffic spread across many ports with low peaks.",
        "ai_decision": "The AI reports no attack (negative).",
        "ground_truth": "A low-frequency scanning attack is underway (false negative).",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "Because no single port showed a large spike, the pattern was treated as background noise and ignored.",
    },
    {
        "stimulus_id": "FN_Good_5",
        "description": "A clinical decision tool analyzes a patient with chest pain, mild shortness of breath, and a noisy ECG.",
        "ai_decision": "The AI predicts no heart attack (negative).",
        "ground_truth": "The patient is experiencing a myocardial infarction (false negative).",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "The ST-segment elevation was below the alert threshold and the signal quality was poor, so the risk score remained low.",
    },
    {
        "stimulus_id": "FN_Good_6",
        "description": "An environmental monitor records factory emissions slightly above the daily mean.",
        "ai_decision": "The AI deems the emissions compliant (negative).",
        "ground_truth": "Emissions exceed legal limits (false negative).",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "The readings stayed within the historical fluctuation band, so the system did not label them as violations.",
    },
    {
        "stimulus_id": "FN_Good_7",
        "description": "A recommendation engine ignores user safety concerns that appear across several contexts.",
        "ai_decision": "The AI states the item is safe to use (negative).",
        "ground_truth": "The item has a safety risk (false negative).",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "Positive feedback carried greater weight than isolated warnings, so the risk signals were not reflected in the score.",
    },
    {
        "stimulus_id": "FN_Good_8",
        "description": "A smart grid observes city electricity demand rise by 12% for 30 minutes.",
        "ai_decision": "The AI labels supply as stable (negative).",
        "ground_truth": "Transmission lines are nearing overload (false negative).",
        "error_type": "FN",
        "explanation_quality": "Good",
        "explanation": "Based on historical patterns, similar short spikes usually drop within 45 minutes and remained within predicted upper bounds, so no alert fired.",
    },
]



def ensure_session():
    if "participant" not in session:
        flash("Session expired. Please restart the study.")
        return False
    return True


@app.route("/", methods=["GET", "POST"])
def intro():
    if request.method == "POST":
        consent = request.form.get("consent")
        participant_id = request.form.get("participant_id", "").strip()
        control_var = request.form.get("control_var", "").strip()

        if consent != "yes":
            flash("Please check the consent box to continue.")
            return render_template("intro.html")

        if not participant_id:
            flash("Please enter your participant ID or alias.")
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
            flash("Please complete all ratings in the practice trials to continue.")
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
            flash("Please rate all items before moving on.")
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
