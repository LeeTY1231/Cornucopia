CREATE TABLE public.syslog (
	"event" varchar NULL,
	"level" int NULL,
	message varchar NULL,
	cdt date NULL,
	opid varchar NULL,
	id uuid NOT NULL,
	CONSTRAINT syslog_pk PRIMARY KEY (id)
);
