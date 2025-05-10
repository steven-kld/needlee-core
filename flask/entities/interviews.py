from atoms import run_query, get_bucket, get_signed_url

def get_interviews_for_org(org_id):
    sql = """
        SELECT i.id AS interview_id,
               i.display_name AS title,
               i.description_text,
               COUNT(r.*) AS total_respondents,
               COUNT(CASE WHEN r.status IN ('processed') THEN 1 END) AS completed
        FROM interviews i
        LEFT JOIN respondents r ON i.id = r.interview_id
        WHERE i.organization_id = %s AND i.visible = TRUE
        GROUP BY i.id, i.description_text
        ORDER BY i.id ASC
    """
    rows = run_query(sql, (org_id,), fetch_all=True)
    return [
        {
            "interview_id": row["interview_id"],
            "title": row["title"],
            "description": row["description_text"] or "[No description]",
            "inited": row["total_respondents"],
            "completed": row["completed"]
        }
        for row in rows
    ]

def get_interview_by_id(org_id, interview_id):
    """
    Fetch a single visible interview for a given organization by ID.
    
    Returns:
        dict or None: Interview row if found, else None.
    """
    return run_query(
        """
        SELECT * FROM interviews
        WHERE id = %s AND organization_id = %s AND visible = TRUE
        """,
        (interview_id, org_id),
        fetch_one=True
    )

def get_interview_questions(interview_id):
    """
    Fetch all questions for a given interview, ordered by question number.
    
    Returns:
        list of dicts: Each with question_num, question, and expected.
    """
    return run_query(
        """
        SELECT question_num, question, expected FROM questions
        WHERE interview_id = %s
        ORDER BY question_num ASC
        """,
        (interview_id,),
        fetch_all=True
    )

def create_interview_with_questions(
    org_id,
    language,
    display_name,
    description_text,
    thank_you_text,
    question_list,
    thank_you_url=None,
    contact_required=False,
    video_required=False,
    visible=True
):
    """
    Insert a new interview and its questions as one transaction.

    Args:
        org_id (int): Organization ID.
        language (str): Language code (e.g., 'en', 'ru').
        display_name (str): Interview name for UI.
        description_text (str): Description shown at the start.
        thank_you_text (str): Message shown at the end.
        question_list (list of tuples): Each tuple is (question_num, question, expected).
        thank_you_url (str, optional): Optional redirect URL after completion.
        contact_required (bool): Whether contact info is required.
        video_required (bool): Whether interview is video-based.
        visible (bool): Whether the interview is visible in admin.

    Returns:
        int: ID of the newly created interview.
    """
    insert_interview_query = """
        INSERT INTO interviews (
            organization_id, language, display_name, description_text,
            thank_you_text, thank_you_url, contact_required,
            video_required, visible
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    
    interview_params = (
        org_id, language, display_name, description_text,
        thank_you_text, thank_you_url, contact_required,
        video_required, visible
    )

    interview = run_query(insert_interview_query, interview_params, fetch_one=True)
    interview_id = interview['id']

    if question_list:
        values = ', '.join(["(%s, %s, %s, %s)"] * len(question_list))
        flat_params = []
        for q in question_list:
            flat_params.extend([interview_id, q[0], q[1], q[2]])

        run_query(
            f"""
            INSERT INTO questions (interview_id, question_num, question, expected)
            VALUES {values}
            """,
            tuple(flat_params)
        )

    return interview_id

def set_interview_invisible(org_id, interview_id):
    """
    Mark an interview as invisible (soft delete).

    Returns:
        None
    """
    return run_query(
        """
        UPDATE interviews SET visible = FALSE
        WHERE id = %s AND organization_id = %s
        """,
        (interview_id, org_id)
    )

def get_interview_recording_url(org_id, interview_id, respondent_hash):
    bucket = get_bucket(org_id)
    path = f"{interview_id}/respondents/{respondent_hash}/interview.webm"
    return get_signed_url(bucket, path, 3600)