CREATE TABLE public.financemodel (
	stockid varchar NULL,
	"date" date NULL,
	total_revenue decimal NULL,
	net_profit decimal NULL,
	total_assets decimal NULL,
	total_liabilities decimal NULL,
	net_assets decimal NULL,
	roe decimal NULL,
	roa decimal NULL,
	gross_margin decimal NULL,
	net_margin decimal NULL,
	debt_ratio decimal NULL,
	current_ratio decimal NULL,
	quick_ratio decimal NULL,
	eps decimal NULL,
	bps decimal NULL,
	cdt date NULL,
	id uuid NOT NULL,
	CONSTRAINT financemodel_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.financemodel IS '个股财务指标模型';

-- Column comments

COMMENT ON COLUMN public.financemodel."date" IS '代表公司何时更新的财务数据';
COMMENT ON COLUMN public.financemodel.total_revenue IS '营业总收入';
COMMENT ON COLUMN public.financemodel.net_profit IS '净利润';
COMMENT ON COLUMN public.financemodel.total_assets IS '总资产';
COMMENT ON COLUMN public.financemodel.total_liabilities IS '总负债';
COMMENT ON COLUMN public.financemodel.net_assets IS '净资产';
COMMENT ON COLUMN public.financemodel.roe IS '净资产收益率%';
COMMENT ON COLUMN public.financemodel.roa IS '总资产收益率%';
COMMENT ON COLUMN public.financemodel.gross_margin IS '毛利率%';
COMMENT ON COLUMN public.financemodel.net_margin IS '净利率';
COMMENT ON COLUMN public.financemodel.debt_ratio IS '资产负债率';
COMMENT ON COLUMN public.financemodel.current_ratio IS '流动比率';
COMMENT ON COLUMN public.financemodel.quick_ratio IS '速动比率';
COMMENT ON COLUMN public.financemodel.eps IS '每股收益';
COMMENT ON COLUMN public.financemodel.bps IS '每股净资产';
