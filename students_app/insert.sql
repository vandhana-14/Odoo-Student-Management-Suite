INSERT INTO student_department
(create_uid, write_uid, name, code, create_date, write_date)
VALUES
(1, 1, 'Computer Science', 'CSE', NOW(), NOW()),
(1, 1, 'Electronics', 'ECE', NOW(), NOW()),
(1, 1, 'Mechanical', 'MECH', NOW(), NOW()),
(1, 1, 'Civil Engineering', 'CIVIL', NOW(), NOW()),
(1, 1, 'Information Technology', 'IT', NOW(), NOW()),
(1, 1, 'Electrical Engineering', 'EEE', NOW(), NOW()),
(1, 1, 'Artificial Intelligence', 'AI', NOW(), NOW()),
(1, 1, 'Data Science', 'DS', NOW(), NOW()),
(1, 1, 'Robotics', 'ROBO', NOW(), NOW()),
(1, 1, 'Cyber Security', 'CYBER', NOW(), NOW());

INSERT INTO student_skills
(name, color, create_uid, write_uid, create_date, write_date)
VALUES
('Python', 1, 1, 1, NOW(), NOW()),
('Java', 2, 1, 1, NOW(), NOW()),
('C++', 3, 1, 1, NOW(), NOW()),
('SQL', 4, 1, 1, NOW(), NOW()),
('HTML', 5, 1, 1, NOW(), NOW()),
('CSS', 6, 1, 1, NOW(), NOW()),
('JavaScript', 7, 1, 1, NOW(), NOW()),
('AI', 8, 1, 1, NOW(), NOW()),
('Machine Learning', 9, 1, 1, NOW(), NOW()),
('Data Science', 10, 1, 1, NOW(), NOW());