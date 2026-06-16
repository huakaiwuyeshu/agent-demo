window.AGENT_DEMO_KNOWLEDGE = {
  "manifest": {
    "name": "api-infra-agent-demo-knowledge",
    "version": "2026-06-16",
    "generated_at": "2026-06-16",
    "source_project": "D:/zuhaowan-ai/llm-wiki/projects/api-infra",
    "sources": [
      {
        "title": "API对接FAQ整理",
        "slug": "api-integration-faq",
        "pages": 3,
        "raw_pdf": "sources/raw-pdfs/API对接FAQ整理.pdf",
        "extracted_md": "sources/extracted-md/api-integration-faq.md",
        "wiki_source": "wiki/sources/api-integration-faq.md",
        "sha256_16": "ab6f0b4e294073bb"
      },
      {
        "title": "安卓上号 SDK 接入文档",
        "slug": "android-login-sdk-integration",
        "pages": 7,
        "raw_pdf": "sources/raw-pdfs/安卓上号 SDK 接入文档.pdf",
        "extracted_md": "sources/extracted-md/android-login-sdk-integration.md",
        "wiki_source": "wiki/sources/android-login-sdk-integration.md",
        "sha256_16": "06210546ee8391cb"
      },
      {
        "title": "API对接流程",
        "slug": "api-integration-process",
        "pages": 2,
        "raw_pdf": "sources/raw-pdfs/API对接流程.pdf",
        "extracted_md": "sources/extracted-md/api-integration-process.md",
        "wiki_source": "wiki/sources/api-integration-process.md",
        "sha256_16": "0c03fad540ca617b"
      },
      {
        "title": "API新续租完整说明",
        "slug": "api-new-renewal-guide",
        "pages": 3,
        "raw_pdf": "sources/raw-pdfs/API新续租完整说明.pdf",
        "extracted_md": "sources/extracted-md/api-new-renewal-guide.md",
        "wiki_source": "wiki/sources/api-new-renewal-guide.md",
        "sha256_16": "83b631b2467e913e"
      },
      {
        "title": "PC端游SDK说明",
        "slug": "pc-game-sdk-guide",
        "pages": 7,
        "raw_pdf": "sources/raw-pdfs/PC端游SDK说明.pdf",
        "extracted_md": "sources/extracted-md/pc-game-sdk-guide.md",
        "wiki_source": "wiki/sources/pc-game-sdk-guide.md",
        "sha256_16": "f0c023b35f29d707"
      },
      {
        "title": "三方标准号池方案",
        "slug": "third-party-standard-number-pool",
        "pages": 11,
        "raw_pdf": "sources/raw-pdfs/三方标准号池方案.pdf",
        "extracted_md": "sources/extracted-md/third-party-standard-number-pool.md",
        "wiki_source": "wiki/sources/third-party-standard-number-pool.md",
        "sha256_16": "901be40a7973f2ac"
      },
      {
        "title": "iOS API接口服务接入文档",
        "slug": "ios-api-service-integration",
        "pages": 20,
        "raw_pdf": "sources/raw-pdfs/iOS API接口服务接入文档.pdf",
        "extracted_md": "sources/extracted-md/ios-api-service-integration.md",
        "wiki_source": "wiki/sources/ios-api-service-integration.md",
        "sha256_16": "3371b5a7bc5fbf15"
      },
      {
        "title": "三方渠道整理",
        "slug": "third-party-channel-summary",
        "pages": 11,
        "raw_pdf": "sources/raw-pdfs/三方渠道整理.pdf",
        "extracted_md": "sources/extracted-md/third-party-channel-summary.md",
        "wiki_source": "wiki/sources/third-party-channel-summary.md",
        "sha256_16": "e20bf408e67fa9c7"
      },
      {
        "title": "货架共享第三方API接口文档",
        "slug": "shelf-sharing-third-party-api",
        "pages": 119,
        "raw_pdf": "sources/raw-pdfs/货架共享第三方API接口文档.pdf",
        "extracted_md": "sources/extracted-md/shelf-sharing-third-party-api.md",
        "wiki_source": "wiki/sources/shelf-sharing-third-party-api.md",
        "sha256_16": "693b4e52eccf0dd0"
      },
      {
        "title": "货架管理三方API文档",
        "slug": "shelf-management-third-party-api",
        "pages": 122,
        "raw_pdf": "sources/raw-pdfs/货架管理三方API文档.pdf",
        "extracted_md": "sources/extracted-md/shelf-management-third-party-api.md",
        "wiki_source": "wiki/sources/shelf-management-third-party-api.md",
        "sha256_16": "f4138d1575e4e92e"
      }
    ],
    "exports": [
      "api_docs.json",
      "faq.json",
      "error_codes.json",
      "sops.json"
    ],
    "boundary": "agent-demo should consume exports/agent-demo only, not raw PDFs or projects/agent-learning."
  },
  "api_docs": [
    {
      "id": "auth-signature-default",
      "category": "auth",
      "title": "默认 API 签名规则",
      "content": "接口调用前需要鉴权。除 sign 外所有请求参数按 ASCII 升序排序，拼接为 字段名=字段值，并用 & 连接；使用 hash_hmac/HMAC-SHA1 计算签名后转 base64，作为 sign 提交。timestamp 为秒级 Unix 时间戳。",
      "source": "wiki/concepts/api-auth-signature.md"
    },
    {
      "id": "auth-signature-status",
      "category": "auth",
      "title": "签名相关状态码",
      "content": "常见状态码：1 表示成功，0 表示错误提示，-1 表示签名错误，-100 表示系统内部异常。",
      "source": "wiki/concepts/api-auth-signature.md"
    },
    {
      "id": "integration-process",
      "category": "integration",
      "title": "API 对接流程",
      "content": "商务确认合作意向后，产品确认合作方式、接入平台、端游/手游、客户端形态、支付和客服问题；再确认开通游戏、上号方式和货架数据方案；合作方提供注册手机号、移动端包名和 SHA-1 签名；生成 appid/appsecret；SDK 包和 PHP 后台鉴权配置并行上线。",
      "source": "wiki/concepts/api-integration-process.md"
    },
    {
      "id": "shelf-sharing-core",
      "category": "shelf-sharing",
      "title": "货架共享核心接口",
      "content": "货架共享常见接口包括 /api/platformXYZ/hao/searchFilter、/api/platformXYZ/hao/search、/api/platformXYZ/hao/info、/api/platformXYZ/hao/detailInfo、/api/platformXYZ/order/placeOrder、/api/platformXYZ/order/relet、/api/platformXYZ/order/info、/api/platformXYZ/ts/getType、/api/platformXYZ/ts/add。",
      "source": "wiki/concepts/shelf-api.md"
    },
    {
      "id": "shelf-management-core",
      "category": "shelf-management",
      "title": "货架管理核心接口",
      "content": "货架管理常见接口包括 /shanghu/[platformXYZ]/v1/onRentHao、offRentHao、batchOnRentHao、batchOffRentHao、delHao，以及 /v2/hideHaoByIds、addBlackUser、getHaoChangeList、searchAccount 和 /v3/rentOutOrderList。",
      "source": "wiki/concepts/shelf-api.md"
    },
    {
      "id": "callback-retry",
      "category": "callback",
      "title": "回调与重试规则",
      "content": "投诉和货架状态、价格、段位、标题等状态变更会回调。回调接口存在 2 次重试机制；不需要约定响应格式，按 HTTP 状态码判断，超时或 500 会重试，返回 200 不重试。",
      "source": "wiki/concepts/callback-retry.md"
    },
    {
      "id": "new-renewal",
      "category": "renewal",
      "title": "新续租规则",
      "content": "新续租新增接口，老续租暂时保留。新续租单是新订单，有独立订单号和解锁码；系列续租单解锁码通用；进入续租时间后自动过渡，无需重新登录。投诉中、已有未开始续租单、被拉黑、与不可租时间冲突等会导致不允许续租或续租失败。",
      "source": "wiki/concepts/new-renewal.md"
    },
    {
      "id": "standard-number-pool",
      "category": "number-pool",
      "title": "三方标准号池规则",
      "content": "标准号池从大号池筛选符合要求的货架，只推送待租状态、非高危、无押金且上号方式匹配的货架；每半小时同步一次。三单连续撤单或七天状态无变化的货架会进入剔除逻辑。",
      "source": "wiki/concepts/standard-number-pool.md"
    },
    {
      "id": "sdk-login",
      "category": "sdk",
      "title": "SDK 上号接入",
      "content": "安卓 SDK 自带混淆规则，三方订单和租号玩官方订单不是同一体系，解锁码不能共用，需要通过 API 下单获取订单信息和解锁码。PC 端游 SDK 需要 Windows 签名，并通过 zhplatform.dll 的 ExchangeCallBack 接收通知。",
      "source": "wiki/concepts/sdk-login.md"
    },
    {
      "id": "defense-api",
      "category": "defense",
      "title": "防御检测接口",
      "content": "防御接口用于三方平台在下单、上号前接入风控能力。检测接口包括 /api/platformXYZ/defense/detect，回调接口包括 /api/platformXYZ/defense/callback；调用时至少存在一种检测类型，否则无实际作用。",
      "source": "wiki/concepts/defense-api.md"
    }
  ],
  "faq": [
    {
      "id": "faq-single-client-multi-game",
      "question": "同一个租号客户端能同时登录多个游戏账号吗？",
      "answer": "不能。同一个租号客户端不支持同时登录多个游戏账号，只支持先后进入；需要另一个游戏退出后才能继续。",
      "source": "wiki/faq/api-integration-faq.md"
    },
    {
      "id": "faq-callback-retry",
      "question": "回调接口失败会重试吗？",
      "answer": "会。当前回调接口存在 2 次重试机制；不需要约定响应格式，按 HTTP 状态码判断，超时或 500 会重试，返回 200 不重试。",
      "source": "wiki/faq/api-integration-faq.md"
    },
    {
      "id": "faq-complaint-callback",
      "question": "投诉状态会回调几次？",
      "answer": "投诉行为会按照结果持续回调，直到用户投诉完成。状态变更也会回调，包括货架状态、价格、段位、标题等信息。",
      "source": "wiki/faq/api-integration-faq.md"
    },
    {
      "id": "faq-other-platform-complaint",
      "question": "其他平台投诉会推给当前渠道吗？",
      "answer": "不会。其他平台投诉不会返回给当前渠道，存在鉴权隔离。",
      "source": "wiki/faq/api-integration-faq.md"
    },
    {
      "id": "faq-list-rentable",
      "question": "列表接口返回的都是可租货架吗？",
      "answer": "目前列表返回的都是可租货架。回调接口中会包含新增账号、状态变更、价格变更或商品其他信息变更等数据。",
      "source": "wiki/faq/api-integration-faq.md"
    },
    {
      "id": "faq-not-in-pool",
      "question": "平台新增货架没有进入号池，会推送给渠道吗？",
      "answer": "不会。平台新增货架不进入号池时，不会推送给渠道。",
      "source": "wiki/faq/api-integration-faq.md"
    },
    {
      "id": "faq-deleted-shelf",
      "question": "商品删除状态是什么意思？",
      "answer": "商品删除指号主将货架从平台删除，该货架 ID 后续可以不再关注，渠道侧基本收不到。",
      "source": "wiki/faq/api-integration-faq.md"
    },
    {
      "id": "faq-info-detailinfo",
      "question": "info 和 detailinfo 有什么区别？",
      "answer": "info 返回货架基础信息，detailinfo 返回货架装备信息、图片等详情内容。",
      "source": "wiki/faq/api-integration-faq.md"
    },
    {
      "id": "faq-signature-debug",
      "question": "签名错误应该排查什么？",
      "answer": "重点检查 app_id、app_secret 是否正确，timestamp 是否为秒级 Unix 时间戳，参数是否按 ASCII 升序排序，是否错误地把 sign 参与签名，是否使用正确算法，以及结果是否 base64 编码。",
      "source": "wiki/faq/api-integration-faq.md"
    },
    {
      "id": "faq-discount-renewal",
      "question": "特价游戏支持续租吗？",
      "answer": "不支持。FAQ 文档列出的特价游戏列表注明特价游戏不支持续租。",
      "source": "wiki/faq/api-integration-faq.md"
    },
    {
      "id": "faq-new-renewal-order",
      "question": "新续租单是否有独立订单号？",
      "answer": "有。新续租单是新订单，拥有独立订单号和解锁码；系列续租单之间解锁码通用。",
      "source": "wiki/faq/api-integration-faq.md"
    },
    {
      "id": "faq-new-renewal-failure",
      "question": "新续租失败常见业务原因有哪些？",
      "answer": "租客已有一个未开始的续租单、订单处于投诉中、租客被号主拉黑、续租时间与货架不可租时间冲突，都可能导致续租不允许或失败。",
      "source": "wiki/faq/api-integration-faq.md"
    }
  ],
  "error_codes": [
    {
      "code": "1",
      "meaning": "成功",
      "suggestion": "接口处理成功。",
      "source": "wiki/concepts/api-auth-signature.md"
    },
    {
      "code": "0",
      "meaning": "错误提示",
      "suggestion": "读取返回消息，根据具体业务错误处理。",
      "source": "wiki/concepts/api-auth-signature.md"
    },
    {
      "code": "-1",
      "meaning": "签名错误",
      "suggestion": "检查 app_id/app_secret、timestamp 秒级格式、参数 ASCII 升序、sign 是否排除、算法和 base64 编码。",
      "source": "wiki/concepts/api-auth-signature.md"
    },
    {
      "code": "-100",
      "meaning": "系统内部异常",
      "suggestion": "确认请求参数无误后，结合服务端日志排查内部异常。",
      "source": "wiki/concepts/api-auth-signature.md"
    },
    {
      "code": "ISSUE_1001",
      "meaning": "快速上号服务参数缺失无法上号",
      "suggestion": "检查解锁码等必要参数。",
      "source": "wiki/sources/android-login-sdk-integration.md"
    },
    {
      "code": "ISSUE_1002",
      "meaning": "未导入相应上号策略实现库",
      "suggestion": "检查安卓 SDK 依赖和上号策略库是否集成。",
      "source": "wiki/sources/android-login-sdk-integration.md"
    },
    {
      "code": "ISSUE_1003",
      "meaning": "quickInfo/dataVO 数据解析异常",
      "suggestion": "检查接口返回结构和 SDK 解析逻辑。",
      "source": "wiki/sources/android-login-sdk-integration.md"
    },
    {
      "code": "ISSUE_1004",
      "meaning": "上号策略初始化失败",
      "suggestion": "检查策略初始化参数和 SDK 环境。",
      "source": "wiki/sources/android-login-sdk-integration.md"
    },
    {
      "code": "ISSUE_1005",
      "meaning": "1.3 上号获取 Token 失败",
      "suggestion": "检查上号 token 获取接口和订单信息。",
      "source": "wiki/sources/android-login-sdk-integration.md"
    },
    {
      "code": "ISSUE_1006",
      "meaning": "1.3 获取云游戏备用 Token 失败",
      "suggestion": "检查云游戏备用 token 服务。",
      "source": "wiki/sources/android-login-sdk-integration.md"
    },
    {
      "code": "ISSUE_1007",
      "meaning": "没有可用的快速上号方式",
      "suggestion": "提示用户返回 APP 及时撤单并租用其他账号。",
      "source": "wiki/sources/android-login-sdk-integration.md"
    },
    {
      "code": "ISSUE_1008",
      "meaning": "暂时无法打开加速器",
      "suggestion": "检查 VPN/加速器启动链路。",
      "source": "wiki/sources/android-login-sdk-integration.md"
    },
    {
      "code": "ISSUE_5000",
      "meaning": "快速上号服务异常",
      "suggestion": "稍后重试或联系客服，并结合 SDK 日志排查。",
      "source": "wiki/sources/android-login-sdk-integration.md"
    }
  ],
  "sops": [
    {
      "id": "signature-debug",
      "title": "签名失败排查 SOP",
      "applies_to": [
        "签名错误",
        "验签失败",
        "返回 -1"
      ],
      "required_info": [
        "接口路径",
        "app_id",
        "请求时间戳",
        "除 sign 外完整请求参数",
        "待签名字符串",
        "签名算法和编码方式"
      ],
      "steps": [
        "检查 app_id 是否匹配合作方和环境",
        "检查 timestamp 是否为秒级 Unix 时间戳",
        "确认 sign 未参与签名",
        "确认参数按 ASCII 升序排序",
        "确认拼接格式为 字段名=字段值 并用 & 连接",
        "确认算法与接口约定一致",
        "确认结果已 base64 编码",
        "确认是否属于独立签名接口"
      ],
      "source": "wiki/sops/signature-debug.md"
    },
    {
      "id": "callback-debug",
      "title": "回调失败排查 SOP",
      "applies_to": [
        "未收到回调",
        "回调重复",
        "回调 500",
        "回调超时"
      ],
      "required_info": [
        "回调地址",
        "事件类型",
        "事件发生时间",
        "HTTP 响应状态码",
        "渠道侧日志和响应时间"
      ],
      "steps": [
        "确认事件是否应回调给当前渠道",
        "确认回调地址可访问",
        "返回 200 不重试",
        "超时或 500 会重试",
        "当前规则为 2 次重试",
        "渠道侧需要做幂等处理",
        "投诉会持续回调直到完成"
      ],
      "source": "wiki/sops/callback-debug.md"
    },
    {
      "id": "new-renewal-debug",
      "title": "新续租排查 SOP",
      "applies_to": [
        "续租失败",
        "续租展示异常",
        "解锁码异常"
      ],
      "required_info": [
        "原订单号",
        "续租接口路径和参数",
        "端游/手游",
        "套餐字段",
        "userid/payid",
        "订单状态/投诉状态/不可租时间/黑名单状态"
      ],
      "steps": [
        "确认使用新续租还是老续租接口",
        "确认端游/手游区分",
        "确认是否传递套餐字段",
        "检查是否已有未开始续租单",
        "检查是否投诉中",
        "检查是否被号主拉黑",
        "检查不可租时间冲突",
        "确认独立订单号和解锁码通用逻辑"
      ],
      "source": "wiki/sops/new-renewal-debug.md"
    }
  ]
};
