
CREATE TABLE IF NOT EXISTS university_chapters (
    chapter_id VARCHAR(50) PRIMARY KEY,
    chapter_name VARCHAR(255) NOT NULL,
    city VARCHAR(150) NOT NULL,
    state CHAR(2) NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_state CHECK (state = 'CA'),
    CONSTRAINT valid_longitude CHECK (
        longitude BETWEEN -180 AND 180
    ),
    CONSTRAINT valid_latitude CHECK (
        latitude BETWEEN -90 AND 90
    )
);
