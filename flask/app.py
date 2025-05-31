from flask import Flask, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
import threading, uuid, os, traceback
from services.interview_manager import InterviewManager
from services.questions_manager import QuestionsManager
from services.answer_manager import AnswersManager
from services.process_manager import ProcessManager
from services.organizations_manager import OrganizationManager
from services.interview_generator import InterviewGenerator
from services.interview_viewer import InterviewViewer
from services.respondent_viewer import RespondentViewer

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")

CORS(app,
    supports_credentials=True,
    origins=[
        "https://caretaker.needleetools.com",
        "https://echo.needleetools.com",
        "https://hub.needleetools.com",
        "https://caretaker.needlee.ai",
        "https://echo.needlee.ai",
        "https://hub.needlee.ai",
    ],
    allow_headers=["Content-Type"],
    methods=["GET", "POST", "OPTIONS"])

@app.route("/api/me", methods=["GET"])
def me():
    try:
        org = OrganizationManager.from_session(session)
        return jsonify({
            "user": {
                "id": session['user_id'],
                "org_id": org.org_id,
                "email": org.email,
                "display_name": org.display_name,
                "interviews": org.interviews
            }
        })
    except ValueError:
        return jsonify({"user": None}), 200  # frontend decides what to show

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    try:
        org = OrganizationManager.create(email=email, password=password)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    session.clear()
    session['user_id'] = str(uuid.uuid4())
    session['email'] = org.email
    session['org_id'] = org.org_id
    session['display_name'] = org.display_name

    return jsonify({
        "user": {
            "id": session['user_id'],
            "org_id": org.org_id,
            "email": org.email,
            "display_name": org.display_name,
            "interviews": org.interviews
        }
    })

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    try:
        org = OrganizationManager.from_login(email, password)
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    session.clear()
    session['user_id'] = str(uuid.uuid4())
    session['email'] = org.email
    session['org_id'] = org.org_id
    session['display_name'] = org.display_name

    return jsonify({
        "user": {
            "id": session['user_id'],
            "org_id": org.org_id,
            "email": org.email,
            "display_name": org.display_name,
            "interviews": org.interviews
        }
    })

@app.route("/api/logout", methods=["POST"])
def logout():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    session.clear()
    return jsonify({"message": "Logged out successfully"})

@app.route("/api/interview-details/<int:interview_id>", methods=["GET"])
def get_interview_details(interview_id):
    org_id = session.get("org_id")
    viewer = InterviewViewer(org_id, interview_id)
    if viewer.exists:
        return jsonify(viewer.to_dict())
    else:
        message, status = viewer.err
        return jsonify({"error": message}), status

@app.route("/api/respondent-details/<int:respondent_id>", methods=["GET"])
def get_respondent_details(respondent_id):
    org_id = session.get("org_id")
    viewer = RespondentViewer(org_id, respondent_id)

    if not viewer.exists:
        return jsonify({"error": "respondent does not exist"}), 400
    
    data_required = request.args.get("data_required", "false").lower() == "true"

    if data_required:
        viewer.get_required_respondent_data()

    return jsonify(viewer.to_dict()), 200
    
    
@app.route("/api/gen-interview", methods=["POST"])
def gen_interview():
    data = request.get_json()
    raw_text = data.get("text")
    if not raw_text:
        return jsonify({"error": "No raw text provided"}), 400

    if "org_id" not in session:
        return jsonify({"error": "Not authenticated"}), 403
    org_id = session["org_id"]

    try:
        generator = InterviewGenerator(org_id=org_id)
        generator.from_raw_text(raw_text)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Interview generation failed", "detail": str(e)}), 500

    return jsonify({
        "status": "ok",
        "interview": generator.to_dict()
    })

@app.route("/api/build-interview", methods=["POST"])
def build_interview():
    if "org_id" not in session:
        return jsonify({"error": "Not authenticated"}), 403

    try:
        data = request.get_json().get("data")
        print(data)

        generator = InterviewGenerator(org_id=session["org_id"])
        generator.apply_result(data)

        def async_process():
            try:
                generator.insert_interview_to_db()
                generator.build()
                print(f"✅ Interview #{generator.interview_id} built successfully")
            except Exception as e:
                print(f"❌ Interview build failed: {e}")

        threading.Thread(target=async_process).start()

        return jsonify({
            "status": "ok",
            "interview": data  # echo back for now
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Build failed", "detail": str(e)}), 500


@app.route("/api/interview-session", methods=["POST"])
def interview_session():
    data = request.get_json()
    org_id = data.get("o")
    interview_id = data.get("i")
    contact = data.get("c")
    uuid = data.get("uuid")

    manager = InterviewManager(org_id, interview_id, contact, uuid)
    response, code = manager.get_initial_response()

    return jsonify(response), code

@app.route("/api/get-questions", methods=["POST"])
def get_questions_route():
    data = request.get_json()
    org_id = data.get("o")
    interview_id = data.get("i")
    uuid = data.get("uuid")
    respondent_exists = data.get("respondent_exists")

    if not org_id or not interview_id or not uuid:
        return jsonify({"error": "Missing required fields"}), 400

    qm = QuestionsManager(org_id, interview_id, uuid, respondent_exists)
    attempt = qm.prepare_respondent()
    ready = qm.wait_for_ready(attempt)

    questions = qm.get_questions()
    texts = [q["question"] for q in questions]
    urls = qm.generate_signed_urls(questions)

    return jsonify({
        "ready": ready,
        "attempt": attempt,
        "questions": texts,
        "urls": urls
    })

@app.route('/api/upload-chunk', methods=['POST'])
def upload_chunk():
    try:
        file = request.files['file']
        attempt = int(request.form['attempt'])
        question_num = int(request.form['question_num'])
        chunk_index = int(request.form['chunk_index'])
        uuid = request.form['uuid']
        org_id = int(request.args.get('o'))
        interview_id = int(request.args.get('i'))

        if not all([file, uuid, org_id, interview_id]):
            return "Missing required fields", 400

        manager = AnswersManager(org_id, interview_id, uuid)
        manager.save_chunk(attempt, question_num, chunk_index, file)

        return '', 204

    except Exception as e:
        import traceback
        traceback.print_exc() 
        return f"Upload failed: {str(e)}", 500

@app.route('/api/close-interview', methods=['POST'])
def close_interview():
    data = request.get_json()
    org_id = data.get('o')
    interview_id = data.get('i')
    uuid = data.get('uuid')
    attempt = data.get('attempt')

    if not org_id or not interview_id or not uuid or not attempt:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        manager = InterviewManager(org_id, interview_id, None, uuid)
        manager.close_interview()

        process_interview(org_id, interview_id, uuid, attempt)

        return jsonify({"status": "ok"})
    
    except Exception as e:
        print("❌ Error setting interview complete:", e)
        return jsonify({"error": "Failed to complete interview"}), 500

@app.route('/api/process/<organization_id>/<interview_id>/<user_id>/<attempt>')
def api_process_interview(organization_id, interview_id, user_id, attempt):
    process_interview(organization_id, interview_id, user_id, attempt)
    return {"r": "none"}, 200

def process_interview(organization_id, interview_id, user_id, attempt):    
    process = ProcessManager(organization_id, interview_id, user_id, attempt)
    if process.valid == False: print("Invalid")
    threading.Thread(target=lambda: process.process(), daemon=True).start()
    return

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9091, debug=True)

