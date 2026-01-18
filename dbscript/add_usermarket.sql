CREATE TABLE public.usermarket (
	id bigserial NOT NULL,
	userid uuid NULL,
	costprice decimal NULL,
	amount decimal NULL,
	total decimal NULL,
	cdt date NULL,
	CONSTRAINT usermarket_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.usermarket IS '用户行情表，比如成本价，盈利';

-- Column comments

COMMENT ON COLUMN public.usermarket.costprice IS '成本价';
COMMENT ON COLUMN public.usermarket.total IS '总市值';
