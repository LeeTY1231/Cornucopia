CREATE TABLE public.useroperate (
	id bigserial NOT NULL,
	userid uuid NULL,
	stockid varchar NULL,
	price decimal NULL,
	"change" decimal NULL,
	cdt date NULL,
	CONSTRAINT useroperate_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.useroperate IS '用户操作记录';
