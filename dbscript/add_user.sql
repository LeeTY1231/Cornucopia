CREATE TABLE public."user" (
	id uuid NOT NULL,
	username varchar NOT NULL,
	"password" varchar NOT NULL,
	mail varchar NOT NULL,
	"permission" varchar NULL,
	active bool DEFAULT false NOT NULL,
	last_login date NULL,
	CONSTRAINT user_pk PRIMARY KEY (id)
);
