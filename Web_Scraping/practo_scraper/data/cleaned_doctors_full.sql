-- SQL file to import cleaned_doctors_full.csv into a database
CREATE TABLE doctors (
    city TEXT,
    speciality TEXT,
    profile_url TEXT,
    name TEXT,
    degree TEXT,
    year_of_experience TEXT,
    location TEXT,
    dp_score REAL,
    npv INTEGER,
    consultation_fee TEXT,
    google_map_link TEXT,
    scraped_at TEXT
);

-- Insert data
.mode csv
.import cleaned_doctors_full.csv doctors
