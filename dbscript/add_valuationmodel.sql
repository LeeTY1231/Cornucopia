CREATE TABLE public.valuationmodel (
	id uuid NOT NULL,
	stockid varchar NULL,
	"date" date NULL,
	pe decimal NULL,
	pe_ttm decimal NULL,
	pb decimal NULL,
	ps decimal NULL,
	ps_ttm decimal NULL,
	total_mv decimal NULL,
	circ_mv decimal NULL,
	dividend_ratio decimal NULL,
	cdt date NULL,
	CONSTRAINT valuationmodel_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.valuationmodel IS '个股估值模型';

-- Column comments

COMMENT ON COLUMN public.valuationmodel.pe IS '市盈率';
COMMENT ON COLUMN public.valuationmodel.pe_ttm IS '市盈率TTM';
COMMENT ON COLUMN public.valuationmodel.pb IS '市净率';
COMMENT ON COLUMN public.valuationmodel.ps IS '市销率';
COMMENT ON COLUMN public.valuationmodel.ps_ttm IS '市销率TTM';
COMMENT ON COLUMN public.valuationmodel.total_mv IS '总市值';
COMMENT ON COLUMN public.valuationmodel.circ_mv IS '流通市值';
COMMENT ON COLUMN public.valuationmodel.dividend_ratio IS '股息率';
