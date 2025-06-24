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

CREATE TABLE interview_costs (
  respondent_id INT PRIMARY KEY REFERENCES respondents(id) ON DELETE CASCADE,
  interview_id INT REFERENCES interviews(id) ON DELETE CASCADE,
  org_id INT REFERENCES organizations(id) ON DELETE CASCADE,
  total_cost FLOAT NOT NULL,
  transcribe_cost FLOAT NOT NULL,
  reasoning_cost FLOAT NOT NULL,
  cost_details JSONB NOT NULL,
  duration_sec FLOAT NOT NULL,
  processing_time_sec FLOAT NOT NULL,
  processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE billing_accounts (
  org_id INTEGER PRIMARY KEY REFERENCES organizations(id) ON DELETE CASCADE,
  cash_balance NUMERIC(10, 2) NOT NULL DEFAULT 50.00,    -- starts with $50 free credit
  last_billed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,    -- tracks last cost deducted
  auto_recharge BOOLEAN DEFAULT FALSE,
  recharge_threshold NUMERIC(10, 2) DEFAULT 5.00,
  recharge_amount NUMERIC(10, 2) DEFAULT 20.00
);

CREATE TABLE organization_payments (
  id SERIAL PRIMARY KEY,
  org_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
  amount NUMERIC(10, 2) NOT NULL,
  method VARCHAR(50),                  -- e.g. 'stripe', 'manual', 'promo'
  reference TEXT,                      -- e.g. Stripe session ID or admin note
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);