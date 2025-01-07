INSERT INTO "users" (
        "id",
        "firstname",
        "lastname",
        "email",
        "password"
    )
VALUES (
        'f928c455-d2f3-4e30-bf58-178ae041e8c2',
        'John',
        'Doe',
        'john@doe.com',
        '$2y$10$3pJS/zU.28UtbDYMo/piHOQ3rGTp3Fa7eCx0teSw2cdSmnwzwzPi6'
    );
INSERT INTO "tasks" (
        "content",
        "createdAt",
        "completedAt",
        "completed",
        "updatedAt",
        "id",
        "user_id"
    )
VALUES (
        'Faire du sport',
        '18:43:54.669',
        NULL,
        'f',
        NULL,
        7,
        'f928c455-d2f3-4e30-bf58-178ae041e8c2'
    );