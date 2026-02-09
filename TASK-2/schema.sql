CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    dept_code VARCHAR(20) UNIQUE NOT NULL,
    dept_name VARCHAR(100) NOT NULL
);


CREATE TABLE add_students (
    id SERIAL PRIMARY KEY,

    name VARCHAR(100) NOT NULL,

    birth DATE,

    student_id VARCHAR(50) UNIQUE NOT NULL,

    department VARCHAR(20) NOT NULL,

    email VARCHAR(100) UNIQUE NOT NULL,

    phone VARCHAR(15),

    address TEXT,

    active BOOLEAN DEFAULT TRUE,

    resume_path TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_department
        FOREIGN KEY (department)
        REFERENCES departments (dept_code)
        ON UPDATE CASCADE
);

CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,

    student_id VARCHAR(50) NOT NULL,

    attendance_date DATE NOT NULL,

    check_in_time TIME,
    check_out_time TIME,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_student
      FOREIGN KEY (student_id)
      REFERENCES add_students (student_id)
      ON DELETE CASCADE,

    UNIQUE (student_id, attendance_date)
);

