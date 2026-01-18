CREATE TABLE public.userpick (
	id uuid NOT NULL,
	userid uuid NULL,
	stockid varchar NULL,
	cdt date NULL,
	CONSTRAINT userpick_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.userpick IS '用户选择关注的股票';
