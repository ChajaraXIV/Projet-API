INSERT INTO public.users (
        id,
        email,
        "password",
        refreshtoken,
        createdat,
        updatedat,
        lastsigninat,
        firstname,
        lastname
    )
VALUES (
        'f928c455-d2f3-4e30-bf58-178ae041e8c2'::uuid,
        'john@doe.com',
        '$2y$10$L6V/Mdi8VToHNuOUvJvKi.n7VmGYFcMyGjCRLl/J.16JtVqsqMnW.',
        NULL,
        '19:08:26.746',
        NULL,
        NULL,
        'John',
        'Doe'
    );