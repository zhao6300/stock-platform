# Requirements Document

## Introduction

本文档定义一个供个人使用的股票与基金分析平台的简洁首期版本。平台以本地、单用户、只读研究为边界，获取并整理 A 股、港股及基金的日频数据，提供基础分析、可复现研究和受明确假设约束的策略回测。首期优先保证数据来源可追溯、证券与日期语义一致、复权透明、质量问题可见以及密钥不泄露，而非追求实时行情、交易执行或复杂策略能力。

## Glossary

- **平台（Platform）**：本规格描述的个人股票与基金分析软件整体。
- **首期版本（MVP）**：本规格“首期范围”及各项验收标准共同限定的第一个可用版本。
- **本地用户（Local_User）**：在个人设备上安装、配置和使用平台的唯一用户。
- **本地环境（Local_Environment）**：由本地用户控制的设备、文件系统、数据库和进程边界。
- **标的（Instrument）**：平台支持研究的 A 股股票、港股股票、交易所交易基金或开放式基金。
- **A 股（A_Share）**：在中国内地证券交易所上市、以人民币计价的股票。
- **港股（HK_Equity）**：在香港联合交易所上市的股票。
- **交易所交易基金（ETF）**：在证券交易所挂牌交易并具有交易行情的基金。
- **开放式基金（Open_End_Fund）**：按基金份额净值申购或赎回、首期不模拟盘中交易的基金。
- **日频数据（Daily_Data）**：以标的所属市场的一个交易日或估值日为一个时间粒度的数据。
- **日线行情（Daily_Bar）**：包含交易日、开盘价、最高价、最低价、收盘价、成交量和成交额的日频交易记录。
- **基金净值（Fund_NAV）**：包含估值日、单位净值以及供应商提供时的累计净值的开放式基金日频记录。
- **行情供应商（Market_Data_Provider）**：根据自身许可条款向本地用户提供行情、净值、证券资料、公司行动或交易日历的外部服务。
- **供应商端点（Provider_Endpoint）**：由本地用户配置并由行情供应商控制的网络服务地址。
- **供应商适配器（Provider_Adapter）**：把特定行情供应商的认证、请求、响应和错误语义转换为平台统一语义的组件。
- **适配器契约（Adapter_Contract）**：供应商适配器必须实现的能力、输入、输出、错误分类和版本信息约定。
- **合规档案（Compliance_Profile）**：记录行情供应商名称、数据来源、账户类型、许可用途、允许的保存方式、允许的导出方式和用户确认时间的本地配置。
- **规范证券标识（Canonical_Security_ID）**：由市场、证券类型和市场内代码组成的稳定平台标识，不把供应商代码直接用作平台主键。
- **证券映射（Security_Mapping）**：规范证券标识与供应商代码之间带有效起止日期的对应关系。
- **证券主数据（Security_Master）**：包含规范证券标识、名称、市场、证券类型、币种、上市或成立日期、终止日期和状态的版本化数据。
- **交易日历（Trading_Calendar）**：按市场、时区和版本记录交易日、开闭市状态及交易时段的日期集合。
- **估值日历（Valuation_Calendar）**：记录开放式基金预期公布净值日期及适用时区的日期集合。
- **公司行动（Corporate_Action）**：拆股、合股、送股、配股、现金分红或其他影响历史价格可比性的事件。
- **原始值（Raw_Value）**：供应商返回且未经过平台复权计算的字段值。
- **复权因子（Adjustment_Factor）**：带来源、适用日期和版本、用于形成可比价格序列的乘数或等价参数。
- **复权模式（Adjustment_Mode）**：不复权、前复权或后复权三种价格查看与研究口径之一。
- **规范化数据集（Canonical_Dataset）**：按照统一字段、类型、单位、币种、证券标识和日期语义保存的数据集合。
- **数据快照（Data_Snapshot）**：通过不可变标识引用的规范化数据集版本。
- **数据质量状态（Data_Quality_Status）**：有效、警告或拒绝三个等级之一。
- **数据质量报告（Data_Quality_Report）**：包含检查范围、规则版本、问题记录、数据质量状态和生成时间的报告。
- **数据摄取服务（Data_Ingestion_Service）**：按适配器契约获取、规范化、增量更新并记录数据来源的组件。
- **标识登记服务（Identifier_Registry）**：维护证券主数据和证券映射并解析供应商代码的组件。
- **日历服务（Calendar_Service）**：维护交易日历与估值日历并提供日期判定的组件。
- **复权服务（Adjustment_Service）**：依据公司行动或供应商复权因子生成指定复权模式序列的组件。
- **数据质量服务（Data_Quality_Service）**：执行质量检查、分配数据质量状态并生成数据质量报告的组件。
- **研究接口（Research_Interface）**：供本地用户的分析页面或本地脚本只读查询规范化数据集的统一入口。
- **研究运行（Research_Run）**：使用确定的数据快照、参数、研究逻辑版本和运行环境执行的一次分析或回测。
- **研究清单（Research_Manifest）**：记录研究运行标识、数据快照标识、证券范围、日期范围、行情供应商、日历版本、复权模式、质量规则版本、研究逻辑版本、参数、依赖环境标识和生成时间的机器可读记录。
- **研究运行器（Research_Runner）**：创建研究运行、保存研究清单并重放研究运行的组件。
- **策略（Strategy）**：根据日频输入产生目标持仓或交易信号的本地研究逻辑。
- **回测（Backtest）**：在历史日频数据和显式模拟假设下估算策略表现的研究运行，不代表真实可成交结果。
- **回测引擎（Backtest_Engine）**：执行回测规则、资产记账和结果计算的组件。
- **交易成本模型（Transaction_Cost_Model）**：由佣金、税费、滑点和最低费用参数组成的回测假设。
- **可交易状态（Tradability_Status）**：标的在指定日期可交易、停牌、涨跌停受限、已终止或未知的状态。
- **回测报告（Backtest_Report）**：包含策略收益序列、基准收益序列、持仓、交易、费用、年化收益率、年化波动率、最大回撤、夏普比率、换手率、参数和限制说明的研究结果。
- **凭据（Credential）**：访问行情供应商所需的 API 密钥、令牌、密码或等价秘密信息。
- **凭据管理器（Credential_Manager）**：保存、读取、遮蔽和删除凭据的组件。
- **敏感信息遮蔽（Secret_Redaction）**：以固定占位符替换凭据及可用于恢复凭据的内容。

## 首期范围

首期版本包含：

- 单用户本地部署和本地数据保存。
- A 股、港股和 ETF 的日线行情，以及开放式基金的日频净值。
- 可配置的行情供应商适配器与统一适配器契约。
- 证券主数据、供应商代码映射、交易日历和估值日历。
- 不复权、前复权和后复权价格序列，以及复权来源说明。
- 增量数据摄取、数据质量检查、基础可视化与常用统计分析。
- 面向本地脚本的只读研究查询、研究清单和可重放研究运行。
- 仅使用日频数据的多头、无杠杆策略回测。
- 本地凭据管理、日志遮蔽、备份与恢复验证。

## 未来扩展（不属于首期验收范围）

以下能力保留为后续方向，不构成本规格首期版本的验收标准：

- A 股和港股以外市场的内置适配器，以及更多商业或开源行情供应商适配器。
- 分钟、逐笔、实时流式行情及低延迟计算。
- 券商连接、模拟盘、实盘下单、自动执行和组合再平衡。
- 做空、融资融券、杠杆、期权、期货及其他衍生品回测。
- 点时成分股、完整退市样本、基本面、新闻、公告和另类数据。
- 参数寻优、机器学习训练、分布式计算和大规模因子平台。
- 多用户、权限管理、团队协作、云托管、移动客户端和跨设备同步。
- 面向第三方的数据再分发、公开数据服务或投资建议生成。

## Requirements

### Requirement 1: 本地个人使用边界

**User Story:** 作为本地用户，我希望平台保持本地、单用户和只读研究边界，以便用较低的部署与运维成本开展个人研究。

#### Acceptance Criteria

1. THE Platform SHALL permit exactly one Local_User to use the Platform within one Local_Environment.
2. IF a second distinct user attempts to use the Platform, THEN THE Platform SHALL deny the attempt, identify that the MVP supports exactly one Local_User, and preserve all provider data, configuration, Data_Snapshots, and Research_Runs unchanged.
3. WHEN the Local_User stores provider data, THE Platform SHALL persist the provider data only within the Local_Environment.
4. WHEN the Platform retrieves market data, THE Platform SHALL send the retrieval request only to Provider_Endpoints configured by the Local_User.
5. IF a market-data retrieval request targets an unconfigured Provider_Endpoint, THEN THE Platform SHALL reject the request, send no outbound request, identify the unconfigured Provider_Endpoint, and preserve all provider data, configuration, Data_Snapshots, and Research_Runs unchanged.
6. THE Platform SHALL provide research interactions without any capability to create, submit, modify, cancel, or execute securities or fund orders.
7. WHEN the Platform presents a Backtest result, THE Platform SHALL label the result as a research estimate that is neither investment advice nor an executable order.
8. IF the Local_User requests a capability documented as a future extension, THEN THE Platform SHALL identify the capability as unavailable in the MVP, perform no market interaction, and preserve all provider data, configuration, Data_Snapshots, and Research_Runs unchanged.

### Requirement 2: 标的与日频数据覆盖

**User Story:** 作为本地用户，我希望用统一方式查看 A 股、港股和基金的日频数据，以便在一个平台内完成基础研究。

#### Acceptance Criteria

1. THE Platform SHALL classify each supported Instrument as exactly one of A_Share, HK_Equity, ETF, or Open_End_Fund.
2. WHEN Daily_Bar data is available from a configured Market_Data_Provider, THE Data_Ingestion_Service SHALL normalize the record only when the trading date is open in the applicable Trading_Calendar, each price is greater than zero, the high price is greater than or equal to the open price, low price, and close price, the low price is less than or equal to the open price and close price, and volume and turnover value are greater than or equal to zero.
3. WHEN Fund_NAV data is available from a configured Market_Data_Provider, THE Data_Ingestion_Service SHALL normalize the record only when the valuation date is expected in the applicable Valuation_Calendar and the unit net asset value is greater than zero.
4. WHEN a Market_Data_Provider supplies cumulative net asset value, THE Data_Ingestion_Service SHALL preserve the cumulative net asset value as a provider-sourced field only when the value is greater than zero and greater than or equal to the unit net asset value for the same Instrument and valuation date.
5. IF a requested Instrument type lacks an enabled Provider_Adapter, THEN THE Platform SHALL return an unsupported-coverage result containing the Instrument type and requested market while preserving the selected Canonical_Dataset unchanged.
6. IF a Daily_Bar or Fund_NAV record violates an applicable date or numeric constraint, THEN THE Data_Ingestion_Service SHALL reject the complete record, assign rejected Data_Quality_Status, identify every violated constraint in the Data_Quality_Report, and preserve all previously accepted observations unchanged.
7. IF the configured Market_Data_Provider is unavailable during a Daily_Bar or Fund_NAV request, THEN THE Data_Ingestion_Service SHALL return a provider-unavailable result identifying the Market_Data_Provider, mark the request as failed, and preserve the selected Canonical_Dataset unchanged.
8. THE Canonical_Dataset SHALL contain at most one Daily_Bar for each Canonical_Security_ID and trading date and at most one Fund_NAV for each Canonical_Security_ID and valuation date.

### Requirement 3: 行情供应商适配

**User Story:** 作为本地用户，我希望能够更换行情供应商，以便根据数据覆盖、许可和个人账户条件选择数据来源。

#### Acceptance Criteria

1. THE Provider_Adapter SHALL declare exactly one Adapter_Contract version and implement that declared version.
2. THE Adapter_Contract SHALL define authentication, capability discovery, data requests, normalized responses, rate-limit signals, and error categories.
3. WHEN the Local_User enables a Provider_Adapter, THE Platform SHALL display the supported markets, Instrument types, data fields, date ranges, and request limits using each reported value and an unknown status for each unreported value.
4. WHEN a Provider_Adapter returns provider-specific identifiers, THE Provider_Adapter SHALL retain each provider-specific identifier, the provider name, and the association with the normalized response as provenance metadata.
5. IF a Market_Data_Provider rejects or throttles a request because of a request limit, THEN THE Provider_Adapter SHALL return a categorized rate-limit error containing the provider name, request category, and retry eligibility.
6. WHEN a Market_Data_Provider supplies a provider correlation identifier for a rejected or throttled request, THE Provider_Adapter SHALL include the provider correlation identifier in the categorized error.
7. IF the Adapter_Contract version declared by a Provider_Adapter is incompatible with the Platform, THEN THE Platform SHALL keep the Provider_Adapter disabled, send no data request through the Provider_Adapter, and report both the declared and supported Adapter_Contract versions.
8. IF enabling a replacement Provider_Adapter returns a categorized error, THEN THE Platform SHALL keep the previously enabled Provider_Adapter enabled and identify the replacement Provider_Adapter as disabled.

### Requirement 4: 数据许可与合规控制

**User Story:** 作为本地用户，我希望记录并遵守每个数据源的使用约束，以便降低未经授权保存、导出或再分发数据的风险。

#### Acceptance Criteria

1. WHEN the Local_User configures a Market_Data_Provider for the first time, THE Platform SHALL require a valid Compliance_Profile before making the first data request.
2. THE Compliance_Profile SHALL record a provider name of 1 to 128 characters, a data source of 1 to 512 characters, an account type selected from free, trial, paid personal, paid professional, or institutional, one to four distinct permitted purposes selected from personal research, academic research, commercial research, or redistribution, a retention permission selected from prohibited, normalized provider data only, or raw and normalized provider data, an export permission selected from prohibited, derived results only, normalized provider data, or raw provider data, and a confirmation time containing a calendar date, a clock time to one-second precision, and an explicit UTC offset from −12:00 through +14:00 inclusive.
3. WHEN the Local_User changes a Compliance_Profile, THE Platform SHALL create a new Compliance_Profile version with a change time containing a calendar date, a clock time to one-second precision, and an explicit UTC offset from −12:00 through +14:00 inclusive while retaining every prior version unchanged.
4. IF a Compliance_Profile has a retention permission of prohibited, THEN THE Data_Ingestion_Service SHALL process the provider response without creating a retained raw response, normalized observation, Canonical_Dataset version, or Data_Snapshot and preserve all previously persisted provider data and Compliance_Profile versions unchanged.
5. IF a Compliance_Profile export permission does not permit the requested export category, THEN THE Platform SHALL return an export-denied result referencing the applicable Compliance_Profile version without producing export output and preserve persisted provider data, Canonical_Dataset versions, Data_Snapshots, and Compliance_Profile versions unchanged.
6. WHERE a Compliance_Profile has a retention permission of raw and normalized provider data, THE Data_Ingestion_Service SHALL associate each retained raw response with the provider, request parameters, applicable Compliance_Profile version, and a request time containing a calendar date, a clock time to one-second precision, and an explicit UTC offset from −12:00 through +14:00 inclusive.
7. THE Platform SHALL label data provenance and provider attribution in each user-visible dataset view.
8. IF any Compliance_Profile field violates an applicable length, enumeration, count, uniqueness, time-precision, or UTC-offset constraint, THEN THE Platform SHALL return a validation-failure result identifying every invalid field without creating a Compliance_Profile version or making a provider request and preserve persisted provider data and prior Compliance_Profile versions unchanged.
9. IF the Local_User requests modification or deletion of a prior Compliance_Profile version, THEN THE Platform SHALL reject the request, identify prior versions as immutable, and retain every Compliance_Profile version and persisted provider dataset unchanged.

### Requirement 5: 证券标识与主数据

**User Story:** 作为本地用户，我希望不同供应商和市场的证券代码映射到稳定标识，以便避免代码复用、市场混淆和历史映射错误。

#### Acceptance Criteria

1. WHEN the Identifier_Registry registers a combination of market, Instrument type, and market-local code, THE Identifier_Registry SHALL assign exactly one Canonical_Security_ID that is not assigned to any other combination.
2. IF a Canonical_Security_ID has been assigned to a market, Instrument type, and market-local code combination, THEN THE Identifier_Registry SHALL preserve that exclusive assignment after every lifecycle status change and termination date.
3. THE Identifier_Registry SHALL store each Security_Mapping with one provider, one provider-specific identifier of 1 to 255 characters, one inclusive effective start date, and one inclusive effective end date that is on or after the effective start date.
4. WHEN exactly one Security_Mapping matches the provider, provider-specific identifier, and observation date, THE Identifier_Registry SHALL return the associated Canonical_Security_ID.
5. IF zero Security_Mappings match the provider, provider-specific identifier, and observation date, THEN THE Identifier_Registry SHALL return an unresolved-identifier result containing those inputs without associating the observation with a Canonical_Security_ID.
6. IF more than one Security_Mapping matches the provider, provider-specific identifier, and observation date, THEN THE Identifier_Registry SHALL return an ambiguous-identifier result containing every matching Canonical_Security_ID and effective interval without associating the observation with a Canonical_Security_ID.
7. WHEN a security name, lifecycle status, or Security_Mapping changes, THE Identifier_Registry SHALL create a new effective-dated version and preserve the prior effective-dated version unchanged.
8. THE Security_Master SHALL record the market, Instrument type, trading currency, listing or establishment date, termination date, and lifecycle status for each Canonical_Security_ID.
9. IF a required identifier field is absent or blank, a provider-specific identifier exceeds 255 characters, an Instrument type is outside A_Share, HK_Equity, ETF, and Open_End_Fund, a supplied date is invalid, or an effective end date precedes its effective start date, THEN THE Identifier_Registry SHALL reject the input, identify every invalid field, preserve all existing Security_Master and Security_Mapping versions, and create no Canonical_Security_ID or Security_Mapping from the input.

### Requirement 6: 交易日历与日期语义

**User Story:** 作为本地用户，我希望平台按标的所属市场解释日期，以便区分休市、停牌、缺失数据和基金未估值日期。

#### Acceptance Criteria

1. THE Calendar_Service SHALL assign each Trading_Calendar version a unique identifier, one market, one market time zone, an inclusive effective start date, and an inclusive effective end date such that the start date is not later than the end date and no effective dates overlap between versions for the same market.
2. THE Calendar_Service SHALL assign each Valuation_Calendar version a unique identifier, one fund market, one applicable time zone, an inclusive effective start date, and an inclusive effective end date such that the start date is not later than the end date and no effective dates overlap between versions for the same fund market.
3. WHEN exactly one Trading_Calendar version applies to a Daily_Bar timestamp, THE Calendar_Service SHALL convert the timestamp using that version's market time zone and map the converted timestamp to the Instrument market's trading date.
4. WHEN exactly one Valuation_Calendar version applies to a Fund_NAV timestamp, THE Calendar_Service SHALL convert the timestamp using that version's applicable time zone and map the converted timestamp to the valuation date.
5. IF zero or more than one applicable Trading_Calendar or Valuation_Calendar version exists for an observation timestamp, THEN THE Calendar_Service SHALL reject the date interpretation, identify the calendar type and missing or ambiguous condition, and preserve the Canonical_Dataset unchanged.
6. IF a Daily_Bar is absent on a date classified as closed by the applicable Trading_Calendar version, THEN THE Data_Quality_Service SHALL classify the absence as an expected calendar gap.
7. IF a Daily_Bar is absent on a date classified as open by the applicable Trading_Calendar version and the matching Tradability_Status is suspended, THEN THE Data_Quality_Service SHALL classify the absence as a suspended-trading gap.
8. IF a Daily_Bar is absent on a date classified as open by the applicable Trading_Calendar version and no matching Tradability_Status exists or the matching Tradability_Status is unknown, THEN THE Data_Quality_Service SHALL classify the absence as an unresolved gap.
9. IF a Fund_NAV is absent on a date identified by the applicable Valuation_Calendar version as an expected valuation date, THEN THE Data_Quality_Service SHALL classify the absence as a delayed-or-missing valuation.

### Requirement 7: 数据摄取、增量更新与来源追溯

**User Story:** 作为本地用户，我希望可靠地获取和更新历史数据，以便在重复运行时获得可追溯且不重复的数据集。

#### Acceptance Criteria

1. WHEN the Local_User requests a valid inclusive date range without refresh, THE Data_Ingestion_Service SHALL request exactly the maximal contiguous segments of expected observation dates absent from the selected Canonical_Dataset version according to the applicable Trading_Calendar or Valuation_Calendar.
2. WHEN an ingested observation has the same Canonical_Security_ID, data type, observation date, and normalized field values as the latest stored version, THE Data_Ingestion_Service SHALL retain the existing logical observation and version identifier without creating a new data version.
3. WHEN an ingested observation has the same Canonical_Security_ID, data type, and observation date as a stored observation but at least one normalized field value differs, THE Data_Ingestion_Service SHALL create one new data version that references the immediately preceding version and preserves every prior version.
4. WHEN the Data_Ingestion_Service accepts an observation, THE Data_Ingestion_Service SHALL associate the observation with the provider, provider-specific identifier, source version when available, and a retrieval time containing a calendar date, a clock time to one-second precision, and an explicit UTC offset.
5. WHEN an ingestion run completes, THE Data_Ingestion_Service SHALL report mutually exclusive requested, accepted, warning, rejected, and unresolved observation counts for which accepted plus warning plus rejected plus unresolved equals requested.
6. IF a Market_Data_Provider request fails before an ingestion run completes, THEN THE Data_Ingestion_Service SHALL mark the run incomplete, preserve all finalized observations, report the categorized provider failure, and expose the earliest requested observation not finalized as the resumable boundary.
7. IF one or more required provider fields are absent from an observation, THEN THE Data_Ingestion_Service SHALL reject the observation, identify every absent field, preserve any prior stored version, and create no logical observation or data version from the rejected observation.
8. WHEN the Local_User requests refresh for a valid inclusive date range, THE Data_Ingestion_Service SHALL request every expected observation date in that range according to the applicable Trading_Calendar or Valuation_Calendar regardless of observations already present.
9. IF a requested date range omits a boundary, contains an invalid boundary, or has a start date later than its end date, THEN THE Data_Ingestion_Service SHALL reject the request before contacting a Market_Data_Provider, identify the supplied boundaries and violated condition, and preserve the selected Canonical_Dataset version unchanged.
10. WHEN the Local_User resumes an incomplete ingestion run, THE Data_Ingestion_Service SHALL continue from the resumable boundary, request only expected observation dates not finalized for that run, and retain the logical observations and version identifiers finalized before the interruption.

### Requirement 8: 复权与公司行动透明度

**User Story:** 作为本地用户，我希望明确选择并检查价格复权口径，以便避免在收益分析和回测中混用不一致的价格序列。

#### Acceptance Criteria

1. THE Adjustment_Service SHALL keep every Raw_Value price field equal to its provider-supplied value across all Adjustment_Mode selections, Adjustment_Factor updates, and adjusted-series generations.
2. WHEN the Local_User requests an A_Share, HK_Equity, or ETF price series, THE Adjustment_Service SHALL require exactly one Adjustment_Mode selected from unadjusted, forward-adjusted, or backward-adjusted.
3. IF an Adjustment_Mode is absent or outside unadjusted, forward-adjusted, and backward-adjusted, THEN THE Adjustment_Service SHALL reject the request without returning a price series and identify the three permitted values.
4. WHEN the Local_User selects the unadjusted Adjustment_Mode, THE Adjustment_Service SHALL return the unchanged Raw_Value prices.
5. WHEN the Local_User selects the forward-adjusted or backward-adjusted Adjustment_Mode, THE Adjustment_Service SHALL return prices derived from one versioned Adjustment_Factor series.
6. THE Adjustment_Service SHALL associate every Adjustment_Factor with exactly one provider or Corporate_Action source, an effective date, a retrieval time, and a version.
7. IF the selected Adjustment_Factor series contains a missing effective date or a value less than or equal to zero, THEN THE Data_Quality_Service SHALL assign rejected Data_Quality_Status to the requested adjusted series.
8. IF the selected Adjustment_Factor series contains a missing effective date or a value less than or equal to zero, THEN THE Adjustment_Service SHALL return no adjusted price values and identify the selected Adjustment_Factor series as invalid.
9. WHEN an adjusted series is displayed or queried, THE Platform SHALL display the Adjustment_Mode, factor source, and factor version used to generate the series.
10. THE Platform SHALL use only provider-supplied cumulative net asset value for an Open_End_Fund.
11. IF an Open_End_Fund lacks provider-supplied cumulative net asset value, THEN THE Platform SHALL return the provider-supplied unit net asset value and identify cumulative net asset value as unavailable.

### Requirement 9: 数据质量与异常可见性

**User Story:** 作为本地用户，我希望数据问题被自动检测并明确展示，以便决定数据是否适合分析或回测。

#### Acceptance Criteria

1. THE Data_Quality_Service SHALL test each Daily_Bar for exactly one observation per Canonical_Security_ID and trading-date combination.
2. THE Data_Quality_Service SHALL test each Daily_Bar for non-missing open price, high price, low price, close price, volume, and turnover value fields.
3. THE Data_Quality_Service SHALL test each Daily_Bar for a high price greater than or equal to the open price, close price, and low price.
4. THE Data_Quality_Service SHALL test each Daily_Bar for a low price less than or equal to the open price, close price, and high price.
5. THE Data_Quality_Service SHALL test each open price, high price, low price, close price, unit net asset value, and supplied cumulative net asset value for a value greater than zero.
6. THE Data_Quality_Service SHALL test each volume and turnover value for a value greater than or equal to zero.
7. THE Data_Quality_Service SHALL test each observation date against the applicable versioned Trading_Calendar or Valuation_Calendar.
8. IF a quality rule fails, THEN THE Data_Quality_Service SHALL record the Canonical_Security_ID, observation date, affected field, observed value, rule identifier, and rule version.
9. WHEN quality checks complete, THE Data_Quality_Service SHALL assign each checked observation the most severe Data_Quality_Status produced by the applicable versioned quality rules, with rejected more severe than warning and warning more severe than valid.
10. IF a calendar, Security_Mapping, Adjustment_Factor, or other input required by an applicable quality rule is unavailable, THEN THE Data_Quality_Service SHALL assign warning or rejected Data_Quality_Status according to the applicable versioned quality rule and record the unavailable input.
11. IF a selected Data_Snapshot contains one or more rejected observations, THEN THE Research_Runner SHALL identify the rejected observations and require explicit Local_User confirmation for that Data_Snapshot before creating the Research_Run.
12. WHEN the Platform returns a series containing a missing observation, THE Platform SHALL preserve the expected observation date and exactly one reason code for that missing observation.
13. WHEN quality checks complete for an ingestion run, THE Data_Quality_Service SHALL generate a Data_Quality_Report containing the checked scope, quality rule version, recorded issues, resulting Data_Quality_Status values, and generation time.

### Requirement 10: 基础分析与个人量化研究

**User Story:** 作为本地用户，我希望通过界面和本地脚本分析统一数据，以便完成日常标的比较和个人量化研究。

#### Acceptance Criteria

1. WHEN the Local_User selects an Instrument and a date range, THE Platform SHALL display the applicable price or Fund_NAV series with provenance, Adjustment_Mode, and Data_Quality_Status.
2. WHEN the Local_User selects a valid numeric series containing at least two non-missing observations ordered by date, THE Platform SHALL calculate each simple periodic return as `r_t = V_t / V_(t-1) - 1` using consecutive non-missing observations and display that convention.
3. WHEN the Local_User selects a valid return series containing `n >= 2` non-missing returns, THE Platform SHALL calculate annualized volatility as `sqrt(252) * sqrt(sum((r_i - mean(r))^2) / (n - 1))` and display the annualization factor 252.
4. WHEN the Local_User selects a valid value series containing at least one positive non-missing observation ordered by date, THE Platform SHALL calculate drawdown at each date as `D_t = V_t / max(V_1...V_t) - 1` and maximum drawdown as `min(D_1...D_n)` using only non-missing observations through each date.
5. WHEN the Local_User selects an integer moving-average window from 1 through 10000 observations, THE Platform SHALL calculate each moving average as the arithmetic mean of the current observation and preceding `w - 1` non-missing observations, returning an explicit missing value until `w` non-missing observations are available.
6. WHEN the Local_User selects two return series having `n >= 2` shared non-missing dates and each aligned series has a non-zero sum of squared deviations, THE Platform SHALL calculate Pearson correlation as `sum((x_i - mean(x)) * (y_i - mean(y))) / sqrt(sum((x_i - mean(x))^2) * sum((y_i - mean(y))^2))` using only shared non-missing dates.
7. THE Research_Interface SHALL provide read-only queries for Security_Master, Daily_Bar, Fund_NAV, Trading_Calendar, Adjustment_Factor, and Data_Quality_Status data while preserving the queried Canonical_Dataset unchanged.
8. THE Research_Interface SHALL limit each query to at most 10000 returned observations and at most 20 filters.
9. WHEN the Research_Interface returns query results, THE Research_Interface SHALL include the Data_Snapshot identifier, query parameters, applied filter count, returned observation count, and an indication of additional matching observations beyond the 10000-observation limit.
10. IF an analysis has fewer valid observations than required by the selected calculation, THEN THE Platform SHALL return an insufficient-data result containing the required and available observation counts while preserving the selected inputs and previously displayed analysis results unchanged.
11. IF either aligned return series has a zero sum of squared deviations during a Pearson correlation calculation, THEN THE Platform SHALL return an undefined-correlation result identifying the zero-variance series while preserving the selected inputs and previously displayed analysis results unchanged.
12. IF a moving-average window is outside the integer range from 1 through 10000, THEN THE Platform SHALL return an invalid-window result containing the permitted range while preserving the selected inputs and previously displayed analysis results unchanged.
13. IF a Research_Interface query specifies more than 20 filters, THEN THE Research_Interface SHALL reject the query with a filter-limit result containing the permitted maximum while preserving the query inputs and previously returned query results unchanged.

### Requirement 11: 研究可复现性

**User Story:** 作为本地用户，我希望每次分析和回测都能记录输入与环境，以便日后重放并解释结果差异。

#### Acceptance Criteria

1. WHEN the Research_Runner creates a Research_Run, THE Research_Runner SHALL persist exactly one Research_Manifest before publishing any result for that Research_Run.
2. THE Research_Manifest SHALL contain every field defined for Research_Manifest in the Glossary.
3. THE Research_Runner SHALL assign an immutable identifier to each Data_Snapshot referenced by a Research_Manifest.
4. WHEN the Local_User requests replay, THE Research_Runner SHALL use exactly the Data_Snapshot, calendar version, Adjustment_Mode, quality rule version, research logic version, parameters, and dependency environment identifier recorded in the Research_Manifest.
5. IF any artifact or recorded version required by a Research_Manifest is unavailable, THEN THE Research_Runner SHALL stop the replay, publish no replay result, and list every unavailable artifact or version.
6. WHEN a deterministic Research_Run is replayed with every required artifact and recorded version available, THE Research_Runner SHALL reproduce every discrete output exactly.
7. WHEN a deterministic Research_Run is replayed with every required artifact and recorded version available, THE Research_Runner SHALL reproduce each floating-point output such that `abs(replayed - original) <= 1e-10 * max(1, abs(original))`.
8. WHEN two Research_Runs produce different results, THE Research_Runner SHALL report the differing Research_Manifest fields and their values for both Research_Runs.

### Requirement 12: 日频策略回测边界

**User Story:** 作为本地用户，我希望在保守且透明的假设下回测简单策略，以便评估研究思路而不把模拟结果误认为真实交易表现。

#### Acceptance Criteria

1. THE Backtest_Engine SHALL maintain Instrument position quantities and cash balances greater than or equal to zero throughout each Backtest.
2. THE Backtest_Engine SHALL process Strategy signals using Daily_Data only.
3. WHEN a Strategy produces a signal from a completed trading day's data, THE Backtest_Engine SHALL schedule the earliest corresponding trade for the first applicable open trading session after that trading date.
4. THE Backtest_Engine SHALL use the Trading_Calendar version referenced by the Research_Manifest to determine each applicable open trading session.
5. WHEN the Backtest_Engine executes a simulated trade, THE Backtest_Engine SHALL apply the selected Transaction_Cost_Model to that trade.
6. WHEN the Backtest_Engine executes a simulated trade, THE Backtest_Engine SHALL record the requested quantity, filled quantity, execution price, gross trade value, each configured cost component, total transaction cost, and net cash change.
7. IF the Tradability_Status for a requested trade is suspended, price-limited against the requested trade, terminated, or unknown, THEN THE Backtest_Engine SHALL assign a filled quantity of zero for that Instrument and date and record the applicable Tradability_Status as the reason.
8. IF the available cash is less than the requested purchase value plus the Transaction_Cost_Model cost, THEN THE Backtest_Engine SHALL assign a filled quantity of zero and preserve positions and cash unchanged for that request.
9. THE Backtest_Engine SHALL offer exactly two missing-price policies: mark affected Instrument valuation and dependent portfolio performance outputs unavailable for the affected date, or use the most recent earlier valid closing price from no more than five applicable open trading sessions before the affected date and otherwise mark those outputs unavailable.
10. IF a Daily_Bar required for valuation is missing, THEN THE Backtest_Engine SHALL apply the selected missing-price policy and record the Instrument, affected date, selected policy, source observation date when applicable, and resulting valuation availability.
11. WHEN a Backtest completes, THE Backtest_Engine SHALL generate a Backtest_Report linked to the Research_Manifest.
12. THE Backtest_Report SHALL contain separate sections for Strategy signal generation, simulated execution, portfolio valuation, and performance calculation.
13. THE Backtest_Report SHALL disclose the data range, Instrument universe, benchmark, Adjustment_Mode, Transaction_Cost_Model, missing-price policy, and Tradability_Status coverage.
14. IF the Backtest uses an Instrument universe without point-in-time membership history for any date in the data range, THEN THE Backtest_Report SHALL identify the affected Instrument universe and display a survivorship-bias warning.
15. IF the Backtest uses an observation with warning or rejected Data_Quality_Status, THEN THE Backtest_Report SHALL list each affected Canonical_Security_ID, observation date, and Data_Quality_Status.
16. IF a Strategy requests short selling, leverage, intraday execution, or derivative positions, THEN THE Backtest_Engine SHALL execute zero simulated trades, preserve initial positions and cash unchanged, and return an unsupported-MVP-rule result identifying every requested unsupported capability.

### Requirement 13: 凭据与本地安全

**User Story:** 作为本地用户，我希望行情凭据受到保护，以便降低密钥因配置、日志、报告或备份而泄露的风险。

#### Acceptance Criteria

1. THE Credential_Manager SHALL store each Credential outside version-controlled project files.
2. THE Credential_Manager SHALL make Credential content readable exclusively to processes executing under the Local_User identity.
3. WHEN the Platform prepares content for display, logging, export, or reporting, THE Credential_Manager SHALL apply Secret_Redaction to every Credential and every value from which a Credential can be recovered before making the content observable.
4. WHEN the Local_User deletes a Provider_Adapter configuration, THE Platform SHALL present each associated Credential as a separately selectable deletion option.
5. WHEN the Local_User confirms Credential deletion selections, THE Platform SHALL delete each selected Credential and preserve each unselected Credential.
6. IF a required Credential is absent or inaccessible, THEN THE Provider_Adapter SHALL send zero requests to the Market_Data_Provider and return a credential-unavailable error without Credential content.
7. IF an outbound connection target, including a redirect target, is not a Provider_Endpoint configured by the Local_User, THEN THE Platform SHALL block the connection before transmitting Credential content, request metadata, or provider data and report the blocked target.
8. WHEN the Platform records provider request metadata, THE Platform SHALL apply Secret_Redaction before persisting or exposing the metadata.
9. IF a backup includes protected Credential material, THEN THE Platform SHALL report the backup as complete only after backup encryption succeeds.
10. IF encryption of a backup containing protected Credential material fails, THEN THE Platform SHALL report the backup as failed, delete all backup data created by the failed operation, and preserve all pre-existing data unchanged.

### Requirement 14: 本地可运维性与数据恢复

**User Story:** 作为本地用户，我希望能够了解平台状态并恢复本地研究数据，以便在个人设备上独立维护平台。

#### Acceptance Criteria

1. THE Platform SHALL report the installed Platform version, enabled Provider_Adapter versions, Adapter_Contract versions, schema version, restore-compatible schema versions, available local storage in bytes, and latest successful ingestion time as individually named status fields, using an explicit no-success state when no ingestion has succeeded.
2. WHEN a local data schema change is required, THE Platform SHALL create and successfully verify a restorable pre-migration backup before changing the schema version or stored data.
3. WHEN the Local_User requests a backup, THE Platform SHALL include configuration excluding plaintext Credentials, Security_Master versions, Security_Mappings, calendars, permitted retained data, Data_Quality_Reports, Data_Snapshots, Research_Manifests, and research results.
4. WHEN the Local_User requests restoration of a verified backup whose schema version is included in the restore-compatible schema versions reported by the installed Platform, THE Platform SHALL restore every included item and report the post-restore record count and content-checksum result for each included dataset.
5. IF a restore operation or any post-restore record-count or content-checksum verification fails, THEN THE Platform SHALL make the complete pre-restore local state available unchanged and report every failed or unverified dataset.
6. IF available local storage in bytes is less than the estimated ingestion requirement in bytes, THEN THE Data_Ingestion_Service SHALL stop before requesting provider data and report both values as non-negative integer byte counts.
7. IF creation or verification of a pre-migration backup fails, THEN THE Platform SHALL preserve the schema version and all stored data unchanged and report the unapplied migration and failed backup verification.
8. IF a requested backup's schema version is absent from the restore-compatible schema versions or any backup record-count or content-checksum verification fails, THEN THE Platform SHALL reject the restoration, preserve the complete pre-restore local state unchanged, and report every failed compatibility or verification condition.
9. WHEN the Platform creates a backup, THE Platform SHALL verify the record count and content checksum of every included dataset against the backup manifest and mark the backup as restorable only when every verification succeeds.

### Requirement 15: AI Evidence Boundary

**User Story:** 作为本地用户，我希望 AI 能解释已冻结的数据快照，但不会引入外部结论或隐藏检索。

#### Acceptance Criteria

1. THE AI_Research_Assistant SHALL require a pinned Data_Snapshot before producing any AI_Research_Artifact.
2. THE AI_Research_Assistant SHALL restrict each request to whitelisted research entities and no more than 20 filters.
3. THE AI_Research_Assistant SHALL use the same bounded research-query result shape as the read-only research interface, with at most 10000 returned observations.
4. WHEN the AI_Research_Assistant returns a finding, THE AI_Research_Assistant SHALL include the model identifier, model version, prompt_template version, reasoning rule-set version, snapshot identifier, entity, filters, observation count, content-addressed analysis identifier, and at least one evidence reference.
5. IF no applicable numeric value or no matching observation is available, THEN THE AI_Research_Assistant SHALL return an insufficient-evidence result without inventing an external-market conclusion.
6. THE default AI_Research_Assistant SHALL perform zero outbound network requests and SHALL not receive credentials or secret material.
