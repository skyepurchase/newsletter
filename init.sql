CREATE TABLE IF NOT EXISTS newsletters (
    id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    passcode VARBINARY(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    newsletter_id INT NOT NULL,
    base TINYINT(1) NOT NULL DEFAULT 0,
    type ENUM('text', 'image') NOT NULL DEFAULT 'text',
    creator VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    issue INT NOT NULL,
    FOREIGN KEY (newsletter_id) REFERENCES newsletters(id)
);

CREATE TABLE IF NOT EXISTS answers (
    id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    question_id INT NOT NULL,
    img_path VARCHAR(100),
    name VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(id),
    -- Remove duplicates for a person responding twice
    UNIQUE INDEX(question_id, name)
);
