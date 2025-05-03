CREATE TABLE organizations (
  id SERIAL PRIMARY KEY,
  date_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  email VARCHAR(255) NOT NULL,
  hashed_password BYTEA NOT NULL,
  salt BYTEA NOT NULL,
  display_name VARCHAR(255) NOT NULL
);

CREATE TABLE interviews (
  id SERIAL PRIMARY KEY,
  date_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  date_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  organization_id INT REFERENCES organizations(id) ON DELETE CASCADE,

  language VARCHAR(4) NOT NULL,
  display_name VARCHAR(255) NOT NULL,
  description_text VARCHAR(255) NOT NULL,
  thank_you_text VARCHAR(255) NOT NULL,
  thank_you_url VARCHAR(255),

  contact_required BOOLEAN DEFAULT FALSE,
  video_required BOOLEAN DEFAULT FALSE,
  visible BOOLEAN DEFAULT TRUE
);

CREATE TABLE questions (
  id SERIAL PRIMARY KEY,
  interview_id INT REFERENCES interviews(id) ON DELETE CASCADE,
  question_num INT NOT NULL,
  question TEXT NOT NULL,
  expected TEXT NOT NULL
);

CREATE TABLE respondents (
  id SERIAL PRIMARY KEY,
  date_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  interview_id INT REFERENCES interviews(id) ON DELETE CASCADE,
  organization_id INT REFERENCES organizations(id) ON DELETE CASCADE,

  interview_display_name VARCHAR(255) NOT NULL,
  contact VARCHAR(255),
  language VARCHAR(4) NOT NULL,
  status VARCHAR(10) NOT NULL,
  respondent_hash VARCHAR(255),
  
  score FLOAT,
  visible BOOLEAN DEFAULT TRUE
);

CREATE TABLE reviews (
  respondent_id INT PRIMARY KEY REFERENCES respondents(id) ON DELETE CASCADE,
  interview_id INT REFERENCES interviews(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  review_data JSONB
);
