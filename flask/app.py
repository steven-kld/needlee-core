from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import threading
from services.interview_manager import InterviewManager
from services.questions_manager import QuestionsManager
from services.answer_manager import AnswersManager
from services.process_manager import ProcessManager
load_dotenv()

app = Flask(__name__)
CORS(app)

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
        traceback.print_exc()  # ← log full stack trace to terminal
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
        # process = ProcessManager() TODO
        return jsonify({"status": "ok"})
    
    except Exception as e:
        print("❌ Error setting interview complete:", e)
        return jsonify({"error": "Failed to complete interview"}), 500

@app.route('/api/process/<organization_id>/<interview_id>/<user_id>')
def api_process_interview(organization_id, interview_id, user_id):
    # threading.Thread(target=lambda: process_interview(organization_id, interview_id, user_id), daemon=True).start()
    return {"r": "none"}, 200

if __name__ == "__main__":
    app.run(debug=True)
